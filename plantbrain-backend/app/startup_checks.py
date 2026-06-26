"""Startup environment validation checks for the PlantBrain backend."""

import asyncio
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Literal

import httpx
from google import genai
from google.genai import types
from sqlalchemy import text

from app.config import settings
from app.database import AsyncSessionLocal
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store


logger = logging.getLogger(__name__)
CheckStatus = Literal["pass", "warn", "fail"]


async def run_startup_checks() -> list[dict]:
    """Run startup validation checks and return structured check results."""

    results = [
        _check_gemini_api_key(),
        _check_data_directories(),
        await _check_database_connection(),
        _check_chromadb_connection(),
        await _check_embedding_model(),
        _check_disk_space(),
        await _check_gemini_api_reachable(),
        await _check_network_connectivity(),
    ]

    pass_count = sum(1 for result in results if result["status"] == "pass")
    warn_count = sum(1 for result in results if result["status"] == "warn")
    fail_count = sum(1 for result in results if result["status"] == "fail")

    for result in results:
        if result["status"] == "fail":
            logger.error("Startup check failed: %s - %s", result["name"], result["message"])

    logger.info("Startup checks: %s passed, %s warnings, %s failures", pass_count, warn_count, fail_count)
    return results


async def assert_critical_checks(results: list[dict]) -> None:
    """Raise when a critical startup check failed."""

    critical_checks = {"gemini_api_key", "data_directories", "database_connection"}
    for result in results:
        if result["name"] in critical_checks and result["status"] == "fail":
            raise RuntimeError(f"Critical startup check failed: {result['name']}: {result['message']}")


def _result(name: str, status: CheckStatus, message: str) -> dict:
    """Build a startup check result payload."""

    return {"name": name, "status": status, "message": message}


def _check_gemini_api_key() -> dict:
    """Verify Gemini API key configuration."""

    api_key = (settings.gemini_api_key or "").strip()
    if not api_key or api_key == "your_key_here":
        return _result("gemini_api_key", "fail", "GEMINI_API_KEY is missing or still set to the placeholder value")
    return _result("gemini_api_key", "pass", "GEMINI_API_KEY is configured")


def _check_data_directories() -> dict:
    """Verify required data directories exist and are writable."""

    directories = [
        settings.upload_dir,
        settings.chroma_persist_dir,
        os.path.dirname(settings.graph_persist_path),
    ]
    failures: list[str] = []

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            test_path = Path(directory) / ".write_test"
            test_path.write_text("ok", encoding="utf-8")
            test_path.unlink(missing_ok=True)
        except Exception as exc:
            failures.append(f"{directory}: {exc}")

    if failures:
        return _result("data_directories", "fail", "; ".join(failures))
    return _result("data_directories", "pass", "Required data directories exist and are writable")


async def _check_database_connection() -> dict:
    """Verify the SQLite database accepts a simple query."""

    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return _result("database_connection", "pass", "Database SELECT 1 succeeded")
    except Exception as exc:
        return _result("database_connection", "fail", f"Database connection failed: {exc}")


def _check_chromadb_connection() -> dict:
    """Verify the ChromaDB collection is initialized and queryable."""

    try:
        if vector_store.collection is None:
            raise RuntimeError("Vector store collection is not initialized")
        count = vector_store.collection.count()
        return _result("chromadb_connection", "pass", f"ChromaDB collection is available with {count} chunks")
    except Exception as exc:
        return _result("chromadb_connection", "fail", f"ChromaDB check failed: {exc}")


async def _check_embedding_model() -> dict:
    """Load the embedding model and warn if cold start is slow."""

    start = time.time()
    try:
        await asyncio.get_event_loop().run_in_executor(None, embedding_service.get_model)
        elapsed = time.time() - start
        message = f"Embedding model loaded in {elapsed:.1f}s"
        if elapsed > 10:
            logger.warning(message)
            return _result("embedding_model", "warn", message)
        return _result("embedding_model", "pass", message)
    except Exception as exc:
        return _result("embedding_model", "fail", f"Embedding model failed to load: {exc}")


def _check_disk_space() -> dict:
    """Verify available disk space for the data directory."""

    try:
        os.makedirs(settings.upload_dir, exist_ok=True)
        _, _, free = shutil.disk_usage(settings.upload_dir)
        free_mb = free // (1024**2)
        message = f"Free: {free_mb}MB available"
        if free < 100 * 1024 * 1024:
            return _result("disk_space", "fail", message)
        if free < 500 * 1024 * 1024:
            return _result("disk_space", "warn", message)
        return _result("disk_space", "pass", message)
    except Exception as exc:
        return _result("disk_space", "fail", f"Disk space check failed: {exc}")


async def _check_gemini_api_reachable() -> dict:
    """Make a minimal Gemini call to verify API reachability and credentials."""

    api_key = (settings.gemini_api_key or "").strip()
    if settings.environment == "development" and (not api_key or api_key == "your_key_here"):
        return _result("gemini_api_reachable", "warn", "Skipped Gemini API call in development because GEMINI_API_KEY is not configured")

    try:
        client = genai.Client(api_key=api_key)
        await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents="ping",
            config=types.GenerateContentConfig(max_output_tokens=10),
        )
        return _result("gemini_api_reachable", "pass", "Gemini API test call succeeded")
    except Exception as exc:
        return _result("gemini_api_reachable", "fail", f"Gemini API test call failed: {exc}")


async def _check_network_connectivity() -> dict:
    """Verify outbound network connectivity to Gemini API infrastructure."""

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.get("https://generativelanguage.googleapis.com")
        return _result("network_connectivity", "pass", "Outbound network connectivity is available")
    except Exception as exc:
        return _result("network_connectivity", "warn", f"Outbound network check failed: {exc}")

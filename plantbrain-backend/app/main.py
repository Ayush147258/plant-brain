"""FastAPI application entry point for the PlantBrain backend."""

import asyncio
import importlib.metadata
import json
import logging
import os
import sys
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

import fastapi
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.config import settings
from app.database import async_engine, check_db_health, init_db
from app.middleware import ErrorHandlingMiddleware, RateLimitMiddleware, RequestLoggingMiddleware
from app.scheduler import scheduler
from app.services.graph_service import graph_service
from app.services.ingestion_service import ingestion_service
from app.services.vector_store import vector_store
from app.startup_checks import assert_critical_checks, run_startup_checks
from app.routers import admin, compliance, graph, ingest, patterns, query, voice, whatsapp


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
if settings.environment != "production":
    os.makedirs("data", exist_ok=True)
    file_handler = logging.FileHandler("data/app.log")
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))
    logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)
APP_START_TIME = time.time()
STARTUP_CHECK_RESULTS: list[dict] = []
STARTUP_CHECKED_AT: str | None = None


async def cleanup_rate_limit_cache() -> None:
    """Periodically remove stale rate limit entries."""

    while True:
        await asyncio.sleep(300)
        now = time.time()
        with RateLimitMiddleware._lock:
            RateLimitMiddleware._request_counts = {
                ip: timestamps
                for ip, timestamps in RateLimitMiddleware._request_counts.items()
                if timestamps and now - timestamps[-1] < 120
            }
        logger.debug("Rate limit cache cleaned up")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup and shutdown tasks for the FastAPI application."""

    global APP_START_TIME, STARTUP_CHECK_RESULTS, STARTUP_CHECKED_AT
    APP_START_TIME = time.time()
    admin.APP_START_TIME = APP_START_TIME
    await init_db()
    asyncio.create_task(cleanup_rate_limit_cache())
    vector_store.initialize()
    STARTUP_CHECK_RESULTS = await run_startup_checks()
    STARTUP_CHECKED_AT = datetime.utcnow().isoformat()
    await assert_critical_checks(STARTUP_CHECK_RESULTS)
    scheduler.start()
    logger.info("PlantBrain backend started")
    try:
        yield
    finally:
        scheduler.stop()
        for task in list(ingestion_service._active_tasks.values()):
            task.cancel()
        await async_engine.dispose()
        logger.info("Shutdown complete")


app = FastAPI(
    title="PlantBrain API",
    description=f"""
## PlantBrain ? AI-powered Plant Intelligence Backend

PlantBrain ingests industrial documents (P&IDs, maintenance records, OEM manuals, compliance guidelines) 
and enables natural language Q&A over them in English and Hindi.

### Core Features
- **Document Ingestion**: Upload PDFs, DOCX, images, and scanned documents
- **Smart Q&A**: Ask questions in English or Hindi, get cited answers with confidence levels
- **Equipment Graph**: Browse and query the equipment knowledge graph
- **Compliance Monitoring**: Check procedures against OISD, PESO, and Factory Act rules
- **Failure Patterns**: Detect recurring failure patterns and overdue inspections
- **Voice Capture**: Transcribe field technician voice notes and extract structured knowledge

### Authentication
Admin endpoints require the `X-Admin-Key` header.

### Rate Limiting
{settings.rate_limit_requests_per_minute} requests per minute per IP.

### WhatsApp Integration
Configure Twilio webhook to: `POST /api/v1/whatsapp/webhook`
""",
    version="1.0.0",
    contact={"name": "PlantBrain Team", "email": "team@plantbrain.ai"},
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "Health", "description": "System health and status"},
        {"name": "Document Ingestion", "description": "Upload and manage documents"},
        {"name": "Query", "description": "Ask questions over ingested documents"},
        {"name": "Equipment Graph", "description": "Browse the equipment knowledge graph"},
        {"name": "Compliance", "description": "Check procedures against regulations"},
        {"name": "Pattern Detection", "description": "Failure patterns and risk analysis"},
        {"name": "Voice Knowledge Capture", "description": "Transcribe voice notes"},
        {"name": "WhatsApp", "description": "WhatsApp webhook integration"},
        {"name": "Admin", "description": "Admin management (requires X-Admin-Key header)"},
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return consistent JSON for request validation errors."""

    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(location) for location in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": errors},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return consistent JSON for explicit HTTP exceptions."""

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


app.include_router(ingest.router, prefix="/api/v1/ingest")
app.include_router(query.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(compliance.router, prefix="/api/v1")
app.include_router(patterns.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get(
    "/",
    tags=["Health"],
    summary="Basic health check",
    description="Return basic API health, version, and environment for load balancers and quick smoke tests.",
    response_description="Basic health status",
)
async def health_check() -> dict[str, str]:
    """Return a basic application health check."""

    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
    }


@app.get(
    "/api/v1/health",
    tags=["Health"],
    summary="Versioned health check",
    description="Return API health, version, environment, and UTC timestamp for frontend status indicators.",
    response_description="Versioned health status",
)
async def api_health_check() -> dict[str, str]:
    """Return a versioned application health check."""

    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
    }



@app.get(
    "/api/v1/health/deep",
    tags=["Health"],
    summary="Deep subsystem health check",
    description="Check database, vector store, and graph subsystems for production monitoring on Render.",
    response_description="Subsystem health status",
)
async def deep_health_check() -> JSONResponse:
    """Return deep health status for core backend subsystems."""

    checks = {
        "database": await check_db_health(),
        "vector_store": await vector_store.health_check(),
        "graph": graph_service.health_check(),
    }

    if not checks["database"]:
        status_value = "unhealthy"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif not all(checks.values()):
        status_value = "degraded"
        status_code = status.HTTP_207_MULTI_STATUS
    else:
        status_value = "healthy"
        status_code = status.HTTP_200_OK

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status_value,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )



@app.get(
    "/api/v1/version",
    tags=["Health"],
    summary="Get API version information",
    description="Return runtime and package version information for support and demo diagnostics.",
    response_description="Version metadata",
)
async def version_info() -> dict[str, str]:
    """Return runtime version metadata."""

    return {
        "version": "1.0.0",
        "environment": settings.environment,
        "python_version": sys.version,
        "fastapi_version": fastapi.__version__,
        "anthropic_version": _package_version("anthropic"),
        "gemini_version": _package_version("google-genai"),
    }


def _package_version(package_name: str) -> str:
    """Return an installed package version or not-installed."""

    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"

@app.get(
    "/api/v1/startup-checks",
    tags=["Health"],
    summary="Get startup check results",
    description="Return cached startup validation checks for Gemini configuration, storage, database, ChromaDB, embeddings, disk, and network.",
    response_description="Cached startup check results",
)
async def startup_checks_status() -> dict:
    """Return cached startup validation results from application startup."""

    return {
        "checks": STARTUP_CHECK_RESULTS,
        "checked_at": STARTUP_CHECKED_AT,
    }


@app.get(
    "/api/v1/docs-examples",
    tags=["Health"],
    summary="Get API curl examples",
    description="Return copy-paste curl examples for common PlantBrain backend operations.",
    response_description="Common API usage examples",
)
async def docs_examples() -> dict[str, str]:
    """Return curl examples for common PlantBrain API operations."""

    return {
        "upload_document": "curl -X POST http://localhost:8000/api/v1/ingest/upload -F 'file=@manual.pdf'",
        "ask_question": "curl -X POST http://localhost:8000/api/v1/query/ask -H 'Content-Type: application/json' -d '{\"question\": \"What are the issues with pump P-202?\"}'",
        "get_risk_summary": "curl http://localhost:8000/api/v1/patterns/risk-summary",
        "check_compliance": "curl -X POST http://localhost:8000/api/v1/compliance/check -H 'Content-Type: application/json' -d '{\"procedure_text\": \"PRV tested annually\", \"rule_codes\": [\"OISD-116-3.2\"]}'",
        "whatsapp_webhook": "Configure Twilio to POST to: /api/v1/whatsapp/webhook",
    }



@app.get(
    "/api/v1/postman-collection",
    tags=["Health"],
    summary="Get Postman collection",
    description="Return a minimal Postman collection covering the most important PlantBrain demo endpoints.",
    response_description="Postman collection JSON",
)
async def postman_collection() -> dict:
    """Return an importable Postman collection for hackathon judges."""

    return {
        "info": {
            "name": "PlantBrain API Demo",
            "description": "Minimal PlantBrain collection for health, ingestion, Q&A, compliance, graph, risk, voice, and admin checks.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "base_url", "value": "http://localhost:8000"},
            {"key": "admin_key", "value": "changeme"},
            {"key": "document_id", "value": ""},
        ],
        "item": [
            _postman_request("Health", "GET", "{{base_url}}/api/v1/health"),
            _postman_request(
                "Upload Document",
                "POST",
                "{{base_url}}/api/v1/ingest/upload",
                body={
                    "mode": "formdata",
                    "formdata": [
                        {"key": "file", "type": "file", "src": []},
                        {"key": "description", "type": "text", "value": "Uploaded from Postman"},
                    ],
                },
            ),
            _postman_request(
                "Ask PlantBrain",
                "POST",
                "{{base_url}}/api/v1/query/ask",
                json_body={
                    "question": "What are the known issues with pump P-202?",
                    "language": "auto",
                    "top_k": 5,
                    "channel": "web",
                    "include_graph_context": True,
                },
            ),
            _postman_request("Seed Compliance Rules", "POST", "{{base_url}}/api/v1/compliance/seed-rules"),
            _postman_request(
                "Check Compliance",
                "POST",
                "{{base_url}}/api/v1/compliance/check",
                json_body={
                    "document_id": "",
                    "procedure_text": "PRV tested annually and records are maintained.",
                    "rule_codes": ["OISD-116-3.2"],
                },
            ),
            _postman_request("Graph Stats", "GET", "{{base_url}}/api/v1/graph/stats"),
            _postman_request("Risk Summary", "GET", "{{base_url}}/api/v1/patterns/risk-summary"),
            _postman_request("Overdue Inspections", "GET", "{{base_url}}/api/v1/patterns/overdue"),
            _postman_request(
                "Voice Transcribe Text",
                "POST",
                "{{base_url}}/api/v1/voice/transcribe-text",
                json_body={
                    "text": "Pump P-202 is vibrating",
                    "equipment_tag": "P-202",
                    "severity": "minor",
                    "inspector_name": "Postman Demo",
                },
            ),
            _postman_request(
                "Admin Stats",
                "GET",
                "{{base_url}}/api/v1/admin/stats",
                headers=[{"key": "X-Admin-Key", "value": "{{admin_key}}", "type": "text"}],
            ),
        ],
    }


def _postman_request(
    name: str,
    method: str,
    raw_url: str,
    json_body: dict | None = None,
    body: dict | None = None,
    headers: list[dict] | None = None,
) -> dict:
    """Build one Postman collection request item."""

    request_headers = headers or []
    request: dict = {
        "method": method,
        "header": request_headers,
        "url": {"raw": raw_url, "host": [raw_url]},
    }
    if json_body is not None:
        request["header"] = [*request_headers, {"key": "Content-Type", "value": "application/json", "type": "text"}]
        request["body"] = {"mode": "raw", "raw": json.dumps(json_body), "options": {"raw": {"language": "json"}}}
    elif body is not None:
        request["body"] = body
    return {"name": name, "request": request}



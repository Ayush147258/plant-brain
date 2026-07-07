"""Internal management endpoints for PlantBrain administrators."""

import json
import logging
import os
import shutil
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import networkx as nx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.compliance import ComplianceCheck, ComplianceRule
from app.models.document import Document
from app.models.equipment import Equipment
from app.models.inspection import Inspection
from app.models.query_log import QueryLog
from app.services.graph_service import graph_service
from app.services.task_queue import ingestion_queue
from app.services.vector_store import vector_store
from app.security import verify_admin_key


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])
APP_START_TIME = time.time()



@router.get(
    "/stats",
    summary="Get admin system stats",
    description="Return full database, vector store, graph, and uptime stats. Requires X-Admin-Key in production.",
    response_description="System statistics",
)
async def get_admin_stats(
    _: bool = Depends(verify_admin_key),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return full system statistics."""

    try:
        database_stats = {
            "documents": {
                "total": await _count(db, Document),
                "completed": await _count(db, Document, Document.status == "completed"),
                "processing": await _count(db, Document, Document.status == "processing"),
                "failed": await _count(db, Document, Document.status == "failed"),
            },
            "equipment": await _count(db, Equipment),
            "inspections": await _count(db, Inspection),
            "compliance_rules": await _count(db, ComplianceRule, ComplianceRule.is_active.is_(True)),
            "compliance_checks": await _count(db, ComplianceCheck),
            "query_logs": await _count(db, QueryLog),
        }
        return {
            "database": database_stats,
            "vector_store": await vector_store.get_stats(),
            "graph": graph_service.get_graph_stats(),
            "uptime_seconds": int(time.time() - APP_START_TIME),
        }
    except Exception as exc:
        logger.exception("Failed to get admin stats")
        raise HTTPException(status_code=500, detail=f"Failed to get admin stats: {exc}") from exc


@router.delete(
    "/reset/vector-store",
    summary="Reset vector store",
    description="Dangerous admin endpoint that deletes all ChromaDB vectors and reinitializes the collection.",
    response_description="Vector store reset result",
)
async def reset_vector_store(
    confirm: bool = Query(...),
    _: bool = Depends(verify_admin_key),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete all ChromaDB vectors and reinitialize the collection."""

    if not confirm:
        raise HTTPException(status_code=400, detail="confirm=true is required")

    try:
        old_stats = await vector_store.get_stats()
        old_count = int(old_stats.get("total_chunks", 0))
        vector_store.client = None
        vector_store.collection = None
        if os.path.exists(settings.chroma_persist_dir):
            shutil.rmtree(settings.chroma_persist_dir)
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        vector_store.initialize()
        logger.warning("Vector store reset by admin")
        return {"message": "Vector store reset", "deleted_chunks": old_count}
    except Exception as exc:
        logger.exception("Failed to reset vector store")
        raise HTTPException(status_code=500, detail=f"Failed to reset vector store: {exc}") from exc


@router.delete(
    "/reset/graph",
    summary="Reset equipment graph",
    description="Dangerous admin endpoint that resets the NetworkX equipment graph to empty.",
    response_description="Graph reset result",
)
async def reset_graph(
    confirm: bool = Query(...),
    _: bool = Depends(verify_admin_key),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Reset the equipment graph to an empty directed graph."""

    if not confirm:
        raise HTTPException(status_code=400, detail="confirm=true is required")

    try:
        graph_service.graph = nx.DiGraph()
        graph_service.save()
        logger.warning("Equipment graph reset by admin")
        return {"message": "Graph reset"}
    except Exception as exc:
        logger.exception("Failed to reset graph")
        raise HTTPException(status_code=500, detail=f"Failed to reset graph: {exc}") from exc


@router.post(
    "/reprocess/{document_id}",
    summary="Reprocess document",
    description="Delete existing vectors for a document and rerun ingestion in the background.",
    response_description="Reprocessing start confirmation",
)
async def reprocess_document(
    document_id: str,
    _: bool = Depends(verify_admin_key),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Re-run ingestion for an existing document."""

    document = await db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        await vector_store.delete_document(document_id)
        document.status = "pending"
        document.total_chunks = 0
        document.error_message = None
        document.processed_at = None
        await db.commit()
        ingestion_queue.enqueue_document_processing(
            document.id,
            document.file_path,
            document.file_type,
            document.original_filename,
        )
        return {"message": "Reprocessing queued", "document_id": document_id}
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to start reprocessing for %s", document_id)
        raise HTTPException(status_code=500, detail=f"Failed to reprocess document: {exc}") from exc


@router.get(
    "/query-stats",
    summary="Get query analytics",
    description="Return Q&A usage analytics, confidence distribution, top questions, and channel breakdown.",
    response_description="Query analytics",
)
async def get_query_stats(
    _: bool = Depends(verify_admin_key),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return Q&A usage analytics."""

    try:
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        total_7 = await _count(db, QueryLog, QueryLog.created_at >= seven_days_ago)
        total_30 = await _count(db, QueryLog, QueryLog.created_at >= thirty_days_ago)
        total_all = await _count(db, QueryLog)

        avg_result = await db.execute(select(func.coalesce(func.avg(QueryLog.response_time_ms), 0)))
        confidence_distribution = await _confidence_distribution(db)
        channel_breakdown = await _group_count(db, QueryLog.channel)
        top_questions_result = await db.execute(
            select(QueryLog.question, func.count(QueryLog.id).label("count"))
            .group_by(QueryLog.question)
            .order_by(func.count(QueryLog.id).desc())
            .limit(10)
        )
        top_questions = [
            {"question": question, "count": int(count)} for question, count in top_questions_result.all()
        ]

        return {
            "queries_last_7_days": total_7,
            "queries_last_30_days": total_30,
            "queries_all_time": total_all,
            "average_response_time_ms": round(float(avg_result.scalar_one() or 0), 2),
            "confidence_distribution": confidence_distribution,
            "top_questions": top_questions,
            "channel_breakdown": channel_breakdown,
        }
    except Exception as exc:
        logger.exception("Failed to get query stats")
        raise HTTPException(status_code=500, detail=f"Failed to get query stats: {exc}") from exc


@router.post(
    "/export/db",
    summary="Export database JSON",
    description="Export all SQLite tables as JSON for backup or demo handoff.",
    response_description="Database export JSON",
)
async def export_database(
    _: bool = Depends(verify_admin_key),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Export all database tables as JSON for backup."""

    try:
        payload = {
            "documents": await _export_table(db, Document),
            "equipment": await _export_table(db, Equipment),
            "inspections": await _export_table(db, Inspection),
            "compliance_rules": await _export_table(db, ComplianceRule),
            "compliance_checks": await _export_table(db, ComplianceCheck),
            "query_logs": await _export_table(db, QueryLog),
        }
        date_stamp = datetime.utcnow().strftime("%Y%m%d")
        return JSONResponse(
            content=payload,
            headers={"Content-Disposition": f"attachment; filename=plantbrain_export_{date_stamp}.json"},
        )
    except Exception as exc:
        logger.exception("Failed to export database")
        raise HTTPException(status_code=500, detail=f"Failed to export database: {exc}") from exc


@router.get(
    "/logs/recent",
    summary="Get recent app logs",
    description="Return the last 100 local application log lines when file logging is enabled.",
    response_description="Recent log lines",
)
async def get_recent_logs(
    _: bool = Depends(verify_admin_key),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return the last 100 application log lines if a local log file exists."""

    log_path = Path("data/app.log")
    if not log_path.exists():
        return {"lines": [], "total_lines": 0}

    try:
        lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return {"lines": lines[-100:], "total_lines": len(lines)}
    except Exception as exc:
        logger.exception("Failed to read recent logs")
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {exc}") from exc


async def _count(db: AsyncSession, model, *filters) -> int:
    """Count rows for a model with optional filters."""

    query = select(func.count()).select_from(model)
    if filters:
        query = query.where(*filters)
    result = await db.execute(query)
    return int(result.scalar_one())


async def _group_count(db: AsyncSession, column) -> dict[str, int]:
    """Return counts grouped by a SQLAlchemy column."""

    result = await db.execute(select(column, func.count()).group_by(column))
    return {str(key or "unknown"): int(count) for key, count in result.all()}


async def _confidence_distribution(db: AsyncSession) -> dict[str, int]:
    """Bucket numeric confidence values into High, Medium, and Low."""

    result = await db.execute(select(QueryLog.confidence))
    buckets = Counter({"High": 0, "Medium": 0, "Low": 0})
    for confidence in result.scalars().all():
        if confidence is None:
            buckets["Medium"] += 1
        elif confidence >= 0.8:
            buckets["High"] += 1
        elif confidence >= 0.5:
            buckets["Medium"] += 1
        else:
            buckets["Low"] += 1
    return dict(buckets)


async def _export_table(db: AsyncSession, model) -> list[dict[str, Any]]:
    """Export all rows for one ORM model."""

    result = await db.execute(select(model))
    return [_serialize_model(row) for row in result.scalars().all()]


def _serialize_model(instance) -> dict[str, Any]:
    """Serialize a SQLAlchemy ORM object to JSON-safe values."""

    data: dict[str, Any] = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        if isinstance(value, datetime):
            data[column.name] = value.isoformat()
        else:
            data[column.name] = value
    return data

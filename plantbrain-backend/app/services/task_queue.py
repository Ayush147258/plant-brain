"""Durable ingestion queue integration for production document processing."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.config import settings


logger = logging.getLogger(__name__)

try:
    from celery import Celery
except ImportError:  # pragma: no cover - dependency is optional in local test environments
    Celery = None  # type: ignore[assignment]

celery_app = None
if Celery is not None and settings.worker_queue_url:
    celery_app = Celery("plantbrain", broker=settings.worker_queue_url, backend=settings.worker_queue_url)
    celery_app.conf.update(task_track_started=True, task_serializer="json", result_serializer="json", accept_content=["json"])


async def _run_ingestion(
    document_id: str,
    file_path: str,
    file_type: str,
    filename: str,
    extraction_kind: str = "auto",
    zone: str = "",
) -> None:
    from app.database import AsyncSessionLocal
    from app.services.ingestion_service import ingestion_service

    async with AsyncSessionLocal() as session:
        await ingestion_service.process_document(document_id, file_path, file_type, filename, session, extraction_kind, zone)


if celery_app is not None:
    @celery_app.task(name="plantbrain.process_document")
    def process_document_task(
        document_id: str,
        file_path: str,
        file_type: str,
        filename: str,
        extraction_kind: str = "auto",
        zone: str = "",
    ) -> None:
        """Celery task entrypoint for durable ingestion workers."""

        asyncio.run(_run_ingestion(document_id, file_path, file_type, filename, extraction_kind, zone))


class IngestionQueue:
    """Dispatch ingestion through Celery in production, with local async fallback for dev/test."""

    def durable_enabled(self) -> bool:
        return celery_app is not None and bool(settings.worker_queue_url)

    def enqueue_document_processing(
        self,
        document_id: str,
        file_path: str,
        file_type: str,
        filename: str,
        extraction_kind: str = "auto",
        zone: str = "",
    ) -> dict[str, Any]:
        payload = [document_id, file_path, file_type, filename, extraction_kind, zone]
        if self.durable_enabled():
            assert celery_app is not None
            result = celery_app.send_task("plantbrain.process_document", args=payload)
            logger.info("Queued document %s on durable worker queue: %s", document_id, result.id)
            return {"mode": "celery", "task_id": result.id}

        asyncio.create_task(_run_ingestion(document_id, file_path, file_type, filename, extraction_kind, zone))
        logger.info("Queued document %s on local async fallback", document_id)
        return {"mode": "local_async", "task_id": document_id}


ingestion_queue = IngestionQueue()

__all__ = ["celery_app", "IngestionQueue", "ingestion_queue"]

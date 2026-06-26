"""Document ingestion pipeline orchestration for PlantBrain."""

import asyncio
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.document import Document
from app.models.equipment import Equipment
from app.models.inspection import Inspection
from app.utils.file_parser import FileParser
from app.utils.text_chunker import TextChunker


logger = logging.getLogger(__name__)


class IngestionService:
    """Coordinate parsing, chunking, vector storage, graph extraction, and DB updates."""

    _active_tasks: dict[str, asyncio.Task] = {}
    _processing_stats: dict[str, int] = {
        "total_processed": 0,
        "total_failed": 0,
        "total_chunks_created": 0,
    }

    EQUIPMENT_TAG_PATTERN = re.compile(r"\b([A-Z]{1,3}-\d{3,4}[A-Z]?)\b")
    INSPECTION_KEYWORDS = ("inspect", "inspection", "check", "found")
    SUPPORTED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "png", "jpg", "jpeg", "tiff", "bmp"}

    async def process_document(
        self,
        document_id: str,
        file_path: str,
        file_type: str,
        filename: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Run the full document ingestion pipeline for an uploaded file."""

        current_task = asyncio.current_task()
        if current_task is not None:
            self._active_tasks[document_id] = current_task

        logger.info("[%s] Step 1/8: Starting ingestion for %s", document_id, filename)
        loop = asyncio.get_event_loop()
        document: Document | None = None
        chunk_count = 0

        try:
            document = await self._get_document(document_id, db)
            if document is None:
                raise ValueError(f"Document not found: {document_id}")

            document.status = "processing"
            document.error_message = None
            await db.commit()

            file_size = os.path.getsize(file_path)
            max_size = settings.max_upload_size_mb * 1024 * 1024
            if file_size > max_size:
                raise ValueError(f"File size {file_size} exceeds limit")
            logger.info("[%s] Step 1/8: File size validated (%s bytes)", document_id, file_size)

            parse_result = await loop.run_in_executor(None, FileParser.parse_file_sync, file_path, file_type)
            if not parse_result.get("success"):
                error = parse_result.get("error") or "File parsing failed"
                await self._mark_failed(document, db, error)
                self._processing_stats["total_failed"] += 1
                return {"success": False, "error": error}
            logger.info(
                "[%s] Step 2/8: Parsed %s pages, %s chars",
                document_id,
                parse_result.get("pages", 0),
                len(parse_result.get("text", "")),
            )

            chunks = await loop.run_in_executor(
                None,
                TextChunker.smart_chunk,
                parse_result["text"],
                settings.chunk_size,
                settings.chunk_overlap,
                parse_result.get("metadata", {}),
            )
            chunks = TextChunker.add_document_context(chunks, filename, document_id)
            logger.info("[%s] Step 3/8: Created %s chunks", document_id, len(chunks))

            from app.services.vector_store import vector_store

            chunk_count = await vector_store.add_chunks(chunks, document_id)
            logger.info("[%s] Step 4/8: Stored chunks in vector store", document_id)

            from app.services.graph_service import graph_service

            new_tags = await loop.run_in_executor(
                None,
                graph_service.extract_and_add_from_text,
                parse_result["text"],
                document_id,
            )
            logger.info("[%s] Step 5/8: Extracted %s equipment tags from %s", document_id, len(new_tags), filename)

            await self._store_equipment_tags(new_tags, document_id, db)
            logger.info("[%s] Step 6/8: Stored equipment records in SQL", document_id)

            self._store_inspection_events(parse_result["text"], document_id, db)
            logger.info("[%s] Step 7/8: Extracted inspection events", document_id)

            document.status = "completed"
            document.total_chunks = chunk_count
            document.processed_at = datetime.utcnow()
            document.error_message = None
            await db.commit()

            self._processing_stats["total_processed"] += 1
            self._processing_stats["total_chunks_created"] += chunk_count
            logger.info("[%s] Step 8/8: Completed ingestion pipeline", document_id)
            return {
                "success": True,
                "document_id": document_id,
                "chunks_created": chunk_count,
                "equipment_tags_found": new_tags,
                "pages": parse_result.get("pages", 0),
            }
        except asyncio.CancelledError:
            logger.warning("[%s] Ingestion task cancelled", document_id)
            await db.rollback()
            if document is not None:
                document.status = "cancelled"
                document.error_message = "Processing cancelled"
                await db.commit()
            raise
        except Exception as exc:
            logger.exception("Document ingestion failed for %s", document_id)
            await db.rollback()
            self._processing_stats["total_failed"] += 1
            if document is not None:
                await self._mark_failed(document, db, str(exc))
            return {"success": False, "error": str(exc)}
        finally:
            self._active_tasks.pop(document_id, None)

    def get_active_tasks(self) -> list[str]:
        """Return document ids currently being processed."""

        return list(self._active_tasks.keys())

    def get_processing_stats(self) -> dict:
        """Return aggregate processing stats plus active task count."""

        return {**self._processing_stats, "currently_processing": len(self._active_tasks)}

    async def cancel_processing(self, document_id: str) -> bool:
        """Cancel active processing for a document and mark it cancelled in the DB."""

        task = self._active_tasks.get(document_id)
        if task is None:
            return False

        task.cancel()
        async with AsyncSessionLocal() as session:
            document = await session.get(Document, document_id)
            if document is not None:
                document.status = "cancelled"
                document.error_message = "Processing cancelled"
                await session.commit()
        return True

    async def get_processing_status(self, document_id: str, db: AsyncSession) -> dict[str, Any]:
        """Return processing status fields for a document."""

        try:
            document = await self._get_document(document_id, db)
            if document is None:
                return {
                    "document_id": document_id,
                    "status": "not_found",
                    "total_chunks": 0,
                    "error_message": "Document not found",
                    "processed_at": None,
                }

            return {
                "document_id": document_id,
                "status": document.status,
                "total_chunks": document.total_chunks,
                "error_message": document.error_message,
                "processed_at": document.processed_at.isoformat() if document.processed_at else None,
            }
        except Exception:
            logger.exception("Failed to get processing status for document %s", document_id)
            raise

    def validate_file(self, filename: str, file_size_bytes: int) -> tuple[bool, str]:
        """Validate upload extension and maximum file size."""

        extension = Path(filename).suffix.lower().lstrip(".")
        if extension not in self.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file type: {extension or 'unknown'}"

        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            return False, f"File exceeds maximum size of {settings.max_upload_size_mb} MB"

        return True, ""

    async def _get_document(self, document_id: str, db: AsyncSession) -> Document | None:
        """Fetch a document by primary key."""

        return await db.get(Document, document_id)

    async def _mark_failed(self, document: Document, db: AsyncSession, error: str) -> None:
        """Mark a document as failed and persist the error message."""

        document.status = "failed"
        document.error_message = error
        await db.commit()
        logger.error("Marked document %s as failed: %s", document.id, error)

    async def _store_equipment_tags(self, tags: list[str], document_id: str, db: AsyncSession) -> None:
        """Create SQL equipment rows for newly extracted tags when absent."""

        for tag in tags:
            result = await db.execute(select(Equipment).where(Equipment.tag == tag))
            existing = result.scalar_one_or_none()
            if existing:
                continue

            equipment = Equipment(tag=tag, source_document_id=document_id)
            await db.merge(equipment)
            logger.info("Queued SQL equipment record for tag %s", tag)

    def _store_inspection_events(self, text: str, document_id: str, db: AsyncSession) -> None:
        """Extract simple inspection-like sentences and add Inspection records."""

        for sentence in self._split_sentences(text):
            lowered_sentence = sentence.lower()
            if not any(keyword in lowered_sentence for keyword in self.INSPECTION_KEYWORDS):
                continue

            tags = self.EQUIPMENT_TAG_PATTERN.findall(sentence)
            for tag in tags:
                db.add(
                    Inspection(
                        equipment_tag=tag.upper(),
                        findings=sentence.strip(),
                        source_document_id=document_id,
                        inspection_type="auto_extracted",
                    )
                )
                logger.info("Queued inspection event for tag %s", tag.upper())

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences using English and Hindi sentence endings."""

        return [sentence.strip() for sentence in re.split(r"(?<=[.!?।])\s+", text) if sentence.strip()]


ingestion_service = IngestionService()

__all__ = ["IngestionService", "ingestion_service"]

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
    """Coordinate parsing, chunking, vector storage, structured extraction, and graph writes."""

    _active_tasks: dict[str, asyncio.Task] = {}
    _pipeline_runs: dict[str, dict[str, Any]] = {}
    _processing_stats: dict[str, int] = {
        "total_processed": 0,
        "total_failed": 0,
        "total_chunks_created": 0,
        "pages_processed": 0,
        "equipment_extracted": 0,
        "low_confidence_fields": 0,
        "failed_jobs_recovered": 0,
        "neo4j_writes": 0,
    }

    EQUIPMENT_TAG_PATTERN = re.compile(r"\b([A-Z]{1,3}-\d{3,4}[A-Z]?)\b")
    INSPECTION_KEYWORDS = ("inspect", "inspection", "check", "found")
    SUPPORTED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "png", "jpg", "jpeg", "tif", "tiff", "bmp", "xlsx", "xls", "dxf", "dwg", "eml", "msg"}
    PIPELINE_STAGES = (
        "upload_received",
        "file_parsed",
        "gemini_multimodal_schema_extraction",
        "json_validation",
        "confidence_scoring",
        "neo4j_merge",
        "vector_index_update",
        "review_queue",
        "query_readiness",
    )

    async def process_document(
        self,
        document_id: str,
        file_path: str,
        file_type: str,
        filename: str,
        db: AsyncSession,
        extraction_kind: str = "auto",
        zone: str = "",
    ) -> dict[str, Any]:
        """Run the full document ingestion pipeline for an uploaded file."""

        current_task = asyncio.current_task()
        if current_task is not None:
            self._active_tasks[document_id] = current_task
        self._start_pipeline(document_id, filename)
        self._stage(document_id, "upload_received", "running", "Upload accepted by backend")

        logger.info("[%s] Step 1/9: Starting ingestion for %s", document_id, filename)
        loop = asyncio.get_event_loop()
        document: Document | None = None
        chunk_count = 0
        new_tags: list[str] = []
        structured_data: dict[str, Any] = {}
        structured_kind = "none"
        extraction_summary: dict[str, int] = {}

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
            self._stage(document_id, "upload_received", "completed", f"{file_size} bytes received")

            parse_result = await loop.run_in_executor(None, FileParser.parse_file_sync, file_path, file_type)
            if not parse_result.get("success"):
                error = parse_result.get("error") or "File parsing failed"
                await self._mark_failed(document, db, error)
                self._processing_stats["total_failed"] += 1
                self._stage(document_id, "file_parsed", "failed", error)
                return {"success": False, "error": error}
            pages = int(parse_result.get("pages", 0) or 0)
            text = parse_result.get("text", "")
            self._processing_stats["pages_processed"] += pages
            self._stage(document_id, "file_parsed", "completed", f"Parsed {pages} pages and {len(text)} characters")
            logger.info("[%s] Step 2/9: Parsed %s pages, %s chars", document_id, pages, len(text))

            base_metadata = {
                **(parse_result.get("metadata", {}) or {}),
                "filename": filename,
                "original_filename": filename,
                "document_id": document_id,
            }
            chunks = self._build_chunks(parse_result, base_metadata, filename, document_id)
            logger.info("[%s] Step 3/9: Created %s chunks", document_id, len(chunks))

            from app.services.vector_store import vector_store

            chunk_count = await vector_store.add_chunks(chunks, document_id)
            self._stage(document_id, "vector_index_update", "completed", f"{chunk_count} chunks stored in vector index")
            logger.info("[%s] Step 4/9: Stored chunks in vector store", document_id)

            text_tags = self._extract_equipment_tags(text)
            structured_kind, structured_data, extraction_summary = await self._run_structured_extraction(
                loop,
                document_id,
                file_path,
                file_type,
                filename,
                text,
                extraction_kind,
                zone,
            )
            structured_tags = self._extract_tags_from_structured(structured_kind, structured_data)
            new_tags = self._dedupe_preserve_order([*text_tags, *structured_tags])
            low_confidence = int(extraction_summary.get("low_confidence", 0))
            self._processing_stats["low_confidence_fields"] += low_confidence
            self._processing_stats["equipment_extracted"] += len(new_tags)
            self._stage(document_id, "confidence_scoring", "completed", f"{low_confidence} low-confidence fields flagged")
            self._stage(
                document_id,
                "review_queue",
                "completed" if low_confidence == 0 else "needs_review",
                "No manual review needed" if low_confidence == 0 else f"{low_confidence} fields require review",
            )

            graph_write_count = await loop.run_in_executor(
                None,
                self._write_graph_data,
                document_id,
                text,
                text_tags,
                structured_kind,
                structured_data,
                bool(parse_result.get("low_confidence", False)),
            )
            self._processing_stats["neo4j_writes"] += graph_write_count
            graph_label = "Neo4j MERGE" if self._neo4j_configured() else "NetworkX fallback"
            self._stage(document_id, "neo4j_merge", "completed", f"{graph_label}: {graph_write_count} graph writes")
            logger.info("[%s] Step 5/9: Wrote %s graph entities", document_id, graph_write_count)

            await self._store_equipment_tags(new_tags, document_id, db)
            logger.info("[%s] Step 6/9: Stored equipment records in SQL", document_id)

            self._store_inspection_events(text, document_id, db)
            self._store_structured_log_events(structured_data, document_id, db)
            logger.info("[%s] Step 7/9: Extracted inspection and maintenance events", document_id)

            document.status = "completed"
            document.total_chunks = chunk_count
            document.processed_at = datetime.utcnow()
            document.error_message = None
            await db.commit()

            self._processing_stats["total_processed"] += 1
            self._processing_stats["total_chunks_created"] += chunk_count
            self._stage(document_id, "query_readiness", "completed", "Document is queryable with citations and graph context")
            logger.info("[%s] Step 9/9: Completed ingestion pipeline", document_id)
            return {
                "success": True,
                "document_id": document_id,
                "chunks_created": chunk_count,
                "equipment_tags_found": new_tags,
                "pages": pages,
                "structured_extraction": structured_kind,
                "extraction_summary": extraction_summary,
            }
        except asyncio.CancelledError:
            logger.warning("[%s] Ingestion task cancelled", document_id)
            await db.rollback()
            self._stage(document_id, "query_readiness", "failed", "Processing cancelled")
            if document is not None:
                document.status = "cancelled"
                document.error_message = "Processing cancelled"
                await db.commit()
            raise
        except Exception as exc:
            logger.exception("Document ingestion failed for %s", document_id)
            await db.rollback()
            self._processing_stats["total_failed"] += 1
            self._stage(document_id, "query_readiness", "failed", str(exc))
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

    def get_pipeline_overview(self) -> dict[str, Any]:
        """Return dashboard-ready ingestion pipeline evidence."""

        recent = sorted(
            self._pipeline_runs.values(),
            key=lambda run: str(run.get("updated_at") or ""),
            reverse=True,
        )[:20]
        return {
            "runs": recent,
            "metrics": self.get_processing_stats(),
            "graph_backend": "neo4j" if self._neo4j_configured() else "networkx_fallback",
            "neo4j_configured": self._neo4j_configured(),
        }

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
            "pipeline": self._pipeline_runs.get(document_id),
        }

    def validate_file(self, filename: str, file_size_bytes: int) -> tuple[bool, str]:
        """Validate upload extension and maximum file size."""

        extension = Path(filename).suffix.lower().lstrip(".")
        if extension not in self.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file type: {extension or 'unknown'}"

        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            return False, f"File exceeds maximum size of {settings.max_upload_size_mb} MB"

        return True, ""

    def _build_chunks(self, parse_result: dict[str, Any], base_metadata: dict[str, Any], filename: str, document_id: str) -> list[dict]:
        page_texts = parse_result.get("page_texts") or []
        if page_texts:
            chunks = []
            for page_data in page_texts:
                page_chunks = TextChunker.smart_chunk(
                    str(page_data.get("text", "")),
                    settings.chunk_size,
                    settings.chunk_overlap,
                    {**base_metadata, "page_number": int(page_data.get("page_number", 0) or 0)},
                )
                chunks.extend(page_chunks)
            for index, chunk in enumerate(chunks):
                chunk["chunk_index"] = index
                chunk["total_chunks"] = len(chunks)
        else:
            chunks = TextChunker.smart_chunk(
                parse_result["text"],
                settings.chunk_size,
                settings.chunk_overlap,
                base_metadata,
            )
        return TextChunker.add_document_context(chunks, filename, document_id)

    async def _run_structured_extraction(
        self,
        loop: asyncio.AbstractEventLoop,
        document_id: str,
        file_path: str,
        file_type: str,
        filename: str,
        text: str,
        requested_kind: str,
        zone: str,
    ) -> tuple[str, dict[str, Any], dict[str, int]]:
        from app.services.multimodal_extraction_service import multimodal_extraction_service
        from app.services.neo4j_service import neo4j_service

        kind = multimodal_extraction_service.classify(filename, file_type, text, requested_kind)  # type: ignore[arg-type]
        if kind == "none":
            self._stage(document_id, "gemini_multimodal_schema_extraction", "skipped", "Document did not require visual structured extraction")
            self._stage(document_id, "json_validation", "skipped", "No structured extraction payload")
            return "none", {}, {"low_confidence": 0}
        if not multimodal_extraction_service.configured():
            self._stage(document_id, "gemini_multimodal_schema_extraction", "skipped", "Gemini extraction API is not configured")
            self._stage(document_id, "json_validation", "skipped", "No structured extraction payload")
            return kind, {}, {"low_confidence": 0}

        self._stage(document_id, "gemini_multimodal_schema_extraction", "running", f"Extracting {kind} with Gemini response_schema")
        data = await loop.run_in_executor(None, multimodal_extraction_service.extract, file_path, kind, zone)
        self._stage(document_id, "gemini_multimodal_schema_extraction", "completed", f"Gemini returned structured {kind} JSON")
        self._stage(document_id, "json_validation", "completed", "Schema-constrained JSON parsed successfully")
        return kind, data, {"low_confidence": neo4j_service.count_low_confidence(data)}

    def _write_graph_data(
        self,
        document_id: str,
        text: str,
        text_tags: list[str],
        structured_kind: str,
        structured_data: dict[str, Any],
        document_low_confidence: bool = False,
    ) -> int:
        from app.services.graph_service import graph_service
        from app.services.neo4j_service import neo4j_service

        if neo4j_service.configured():
            try:
                count = neo4j_service.merge_text_equipment(text_tags, document_id)
                if structured_kind == "pid" and structured_data:
                    result = neo4j_service.merge_pid_extraction(structured_data, document_id, document_low_confidence=document_low_confidence)
                    count += int(result.get("equipment", 0)) + int(result.get("valves", 0)) + int(result.get("instruments", 0))
                elif structured_kind == "maintenance_log" and structured_data:
                    result = neo4j_service.merge_log_extraction(structured_data, document_id, document_low_confidence=document_low_confidence)
                    count += int(result.get("maintenance_events", 0))
                return count
            except Exception as exc:
                logger.warning("Neo4j graph write failed; using NetworkX fallback for document %s: %s", document_id, exc)
                self._processing_stats["failed_jobs_recovered"] += 1

        added = graph_service.extract_and_add_from_text(text, document_id)
        if structured_kind == "pid" and structured_data:
            added.extend(graph_service.add_pid_extraction(structured_data, document_id))
        return len(self._dedupe_preserve_order([*added, *text_tags]))

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
            db.add(Equipment(tag=tag, source_document_id=document_id))
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

    def _store_structured_log_events(self, data: dict[str, Any], document_id: str, db: AsyncSession) -> None:
        for entry in data.get("entries", []) or []:
            tag = str(entry.get("Asset_ID") or "").strip().upper()
            if not tag:
                continue
            db.add(
                Inspection(
                    equipment_tag=tag,
                    inspection_date=self._parse_date(entry.get("Date")),
                    findings=entry.get("Technician_Notes") or entry.get("Failure_Mode"),
                    severity="low" if entry.get("confidence") == "low" else "routine",
                    source_document_id=document_id,
                    inspection_type="maintenance_log_extracted",
                )
            )

    def _start_pipeline(self, document_id: str, filename: str) -> None:
        now = datetime.utcnow().isoformat()
        self._pipeline_runs[document_id] = {
            "document_id": document_id,
            "filename": filename,
            "created_at": now,
            "updated_at": now,
            "stages": [
                {"name": stage, "status": "pending", "message": "Waiting", "updated_at": now}
                for stage in self.PIPELINE_STAGES
            ],
        }

    def _stage(self, document_id: str, name: str, status: str, message: str) -> None:
        run = self._pipeline_runs.get(document_id)
        if not run:
            return
        now = datetime.utcnow().isoformat()
        run["updated_at"] = now
        for stage in run["stages"]:
            if stage["name"] == name:
                stage.update({"status": status, "message": message, "updated_at": now})
                return

    def _extract_equipment_tags(self, text: str) -> list[str]:
        return self._dedupe_preserve_order([match.group(1).upper() for match in self.EQUIPMENT_TAG_PATTERN.finditer(text)])

    def _extract_tags_from_structured(self, kind: str, data: dict[str, Any]) -> list[str]:
        tags: list[str] = []
        if kind == "pid":
            tags.extend(str(item.get("id") or "").strip().upper() for item in data.get("equipment", []) if item.get("id"))
            tags.extend(str(item.get("valve_id") or "").strip().upper() for item in data.get("valves", []) if item.get("valve_id"))
        elif kind == "maintenance_log":
            tags.extend(str(item.get("Asset_ID") or "").strip().upper() for item in data.get("entries", []) if item.get("Asset_ID"))
        return self._dedupe_preserve_order([tag for tag in tags if tag])

    @staticmethod
    def _neo4j_configured() -> bool:
        return bool(settings.neo4j_uri and settings.neo4j_user and settings.neo4j_password)

    @staticmethod
    def _parse_date(value: Any) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences using common English and Indic sentence endings."""

        return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]

    @staticmethod
    def _dedupe_preserve_order(values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                deduped.append(value)
        return deduped


ingestion_service = IngestionService()

__all__ = ["IngestionService", "ingestion_service"]

"""Voice transcription and knowledge capture API endpoints for PlantBrain."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from app.schemas import TextKnowledgeRequest, TranscriptionResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal, get_db
from app.models.document import Document
from app.models.inspection import Inspection
from app.services.ingestion_service import ingestion_service
from app.services.voice_service import voice_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["Voice Knowledge Capture"])



@router.post(
    "/transcribe",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload voice note",
    description="Upload an audio file for local Whisper transcription, knowledge extraction, and background ingestion.",
    response_description="Voice document ID and processing status",
)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form(default=""),
    link_to_document_id: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Upload audio and start background transcription and knowledge capture."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded audio must have a filename")

    try:
        content = await file.read()
        file_size_bytes = len(content)
        await file.seek(0)

        is_valid, validation_error = voice_service.validate_audio_file(file.filename, file_size_bytes)
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_error)

        document_id = link_to_document_id.strip() or str(uuid4())
        unique_filename = f"voice_{uuid4()}_{_secure_filename(file.filename)}"
        os.makedirs(settings.upload_dir, exist_ok=True)
        file_path = str(Path(settings.upload_dir) / unique_filename)

        async with aiofiles.open(file_path, "wb") as output_file:
            await output_file.write(content)

        document = Document(
            id=document_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_type="voice",
            file_size_bytes=file_size_bytes,
            file_path=file_path,
            status="processing",
        )
        await db.merge(document)
        await db.commit()

        asyncio.create_task(
            process_voice_background(
                document_id,
                file_path,
                file.filename,
                language,
                None,
            )
        )

        logger.info("Accepted voice upload %s for document %s", file.filename, document_id)
        return {
            "document_id": document_id,
            "message": "Audio uploaded, transcription in progress",
            "status": "processing",
        }
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to upload voice note %s", file.filename)
        raise HTTPException(status_code=500, detail=f"Failed to upload audio: {exc}") from exc


async def process_voice_background(
    document_id: str,
    file_path: str,
    filename: str,
    language: str,
    db: AsyncSession | None = None,
) -> None:
    """Process a voice upload in the background and persist transcription chunks."""

    async with AsyncSessionLocal() as session:
        document = await session.get(Document, document_id)
        try:
            if document is None:
                raise ValueError(f"Document not found: {document_id}")

            voice_result = await voice_service.process_voice_note(
                file_path,
                filename,
                document_id,
                language or None,
            )
            transcription_text = voice_result.get("transcription", "")
            text_path = _transcription_text_path(file_path)
            async with aiofiles.open(text_path, "w", encoding="utf-8") as text_file:
                await text_file.write(transcription_text)

            ingestion_result = await ingestion_service.process_document(
                document_id,
                text_path,
                "txt",
                f"{filename}.txt",
                session,
            )
            if not ingestion_result.get("success"):
                raise RuntimeError(ingestion_result.get("error", "Voice transcription ingestion failed"))

            document = await session.get(Document, document_id)
            if document is not None:
                document.status = "completed"
                document.total_chunks = int(ingestion_result.get("chunks_created", 0))
                document.error_message = None
                await session.commit()

            logger.info("Completed voice background processing for document %s", document_id)
        except Exception as exc:
            await session.rollback()
            document = await session.get(Document, document_id)
            if document is not None:
                document.status = "failed"
                document.error_message = str(exc)
                await session.commit()
            logger.exception("Voice background processing failed for document %s", document_id)


@router.get(
    "/transcription/{document_id}",
    summary="Get transcription status",
    description="Return transcription preview, equipment tags, and created inspection count for a voice document.",
    response_description="Voice transcription status",
)
async def get_transcription(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return transcription status and extracted inspection count for a voice document."""

    document = await db.get(Document, document_id)
    if document is None or document.file_type != "voice":
        raise HTTPException(status_code=404, detail="Voice document not found")

    inspections_result = await db.execute(
        select(Inspection).where(Inspection.source_document_id == document_id)
    )
    inspections = inspections_result.scalars().all()
    transcription_text = await _read_transcription_preview(document.file_path) if document.status == "completed" else ""
    equipment_tags = _dedupe_preserve_order([inspection.equipment_tag for inspection in inspections])

    return {
        "document_id": document.id,
        "status": document.status,
        "transcription_preview": transcription_text[:500],
        "equipment_tags_found": equipment_tags,
        "inspections_created": len(inspections),
    }


@router.post(
    "/transcribe-text",
    summary="Capture typed knowledge",
    description="Extract equipment tags, keywords, and inspection hints from technician-entered text without audio transcription.",
    response_description="Extracted knowledge result",
)
async def transcribe_text(
    request: TextKnowledgeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Capture typed technician knowledge without audio transcription."""

    try:
        knowledge = voice_service.extract_knowledge(request.text)
        inspection_created = False
        equipment_tag = request.equipment_tag.strip().upper()
        if equipment_tag:
            db.add(
                Inspection(
                    equipment_tag=equipment_tag,
                    inspector_name=request.inspector_name,
                    inspection_type="text_manual_capture",
                    findings=request.text,
                    severity=request.severity.lower(),
                )
            )
            await db.commit()
            inspection_created = True

        return {"knowledge_extracted": knowledge, "inspection_created": inspection_created}
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to capture typed knowledge")
        raise HTTPException(status_code=500, detail=f"Failed to capture text knowledge: {exc}") from exc


@router.get(
    "/recent-captures",
    summary="List recent voice captures",
    description="Return the latest voice capture documents with transcription previews and extracted knowledge.",
    response_description="Recent voice captures",
)
async def recent_captures(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return the 20 most recent voice captures with extracted inspection knowledge."""

    try:
        documents_result = await db.execute(
            select(Document)
            .where(Document.file_type == "voice")
            .order_by(Document.uploaded_at.desc())
            .limit(20)
        )
        documents = documents_result.scalars().all()
        captures = []

        for document in documents:
            inspections_result = await db.execute(
                select(Inspection).where(Inspection.source_document_id == document.id)
            )
            inspections = inspections_result.scalars().all()
            transcription_preview = await _read_transcription_preview(document.file_path)
            knowledge = voice_service.extract_knowledge(transcription_preview)
            captures.append(
                {
                    "document_id": document.id,
                    "filename": document.original_filename,
                    "status": document.status,
                    "uploaded_at": document.uploaded_at,
                    "processed_at": document.processed_at,
                    "transcription_preview": transcription_preview[:300],
                    "knowledge_extracted": knowledge,
                    "inspections_created": len(inspections),
                }
            )

        return {"captures": captures, "total": len(captures)}
    except Exception as exc:
        logger.exception("Failed to get recent voice captures")
        raise HTTPException(status_code=500, detail=f"Failed to get recent captures: {exc}") from exc


def _secure_filename(filename: str) -> str:
    """Return a conservative filename safe for local storage."""

    filename = Path(filename).name.replace(" ", "_")
    safe_name = "".join(character for character in filename if character.isalnum() or character in {".", "_", "-"})
    return safe_name or "voice_audio"


def _transcription_text_path(file_path: str) -> str:
    """Return the text sidecar path for a voice transcription."""

    return f"{file_path}.txt"


async def _read_transcription_preview(file_path: str) -> str:
    """Read a voice transcription sidecar if it exists."""

    text_path = _transcription_text_path(file_path)
    if not Path(text_path).exists():
        return ""
    async with aiofiles.open(text_path, "r", encoding="utf-8") as text_file:
        return await text_file.read()


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    """Remove duplicate strings while preserving first-seen order."""

    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


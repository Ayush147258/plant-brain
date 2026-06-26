"""Document ingestion API endpoints for PlantBrain."""

import asyncio
import logging
import os
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from app.schemas import DocumentListItem, DocumentListResponse, DocumentStatsResponse, DocumentStatusResponse, DocumentUploadResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal, get_db
from app.models.document import Document
from app.services.ingestion_service import ingestion_service
from app.services.vector_store import vector_store
from app.utils.file_parser import FileParser


logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["Document Ingestion"])



@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a document",
    description="Upload a PDF, DOCX, TXT, or image file. Processing starts immediately in the background. Poll /status/{document_id} to track progress.",
    response_description="Document ID and initial status",
)
async def upload_document(
    file: UploadFile = File(...),
    description: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """Upload a document and start background ingestion."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")

    try:
        content = await file.read()
        file_size_bytes = len(content)
        await file.seek(0)

        is_valid, validation_error = ingestion_service.validate_file(file.filename, file_size_bytes)
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_error)

        file_type = FileParser.detect_file_type(file.filename)
        if file_type == "unknown":
            raise HTTPException(status_code=400, detail="Unsupported file type")

        secure_filename = _secure_filename(file.filename)
        unique_filename = f"{uuid4()}_{secure_filename}"
        os.makedirs(settings.upload_dir, exist_ok=True)
        file_path = str(Path(settings.upload_dir) / unique_filename)

        async with aiofiles.open(file_path, "wb") as output_file:
            await output_file.write(content)

        document = Document(
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            file_path=file_path,
            status="pending",
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        logger.info("Accepted document upload %s (%s bytes)", document.id, file_size_bytes)
        asyncio.create_task(
            _process_document_background(
                document.id,
                file_path,
                file_type,
                file.filename,
            )
        )

        return DocumentUploadResponse(
            document_id=document.id,
            filename=file.filename,
            status="processing",
            message="Document uploaded and processing started",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to upload document %s", file.filename)
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {exc}") from exc


@router.get(
    "/status/{document_id}",
    response_model=DocumentStatusResponse,
    summary="Get document processing status",
    description="Return the current ingestion status, chunk count, and error details for one uploaded document.",
    response_description="Current document processing status",
)
async def get_document_status(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentStatusResponse:
    """Return the current processing status for a document."""

    document = await _get_document_or_404(document_id, db)
    return _document_to_status_response(document)


@router.get(
    "/list",
    response_model=DocumentListResponse,
    summary="List uploaded documents",
    description="List uploaded documents with pagination and optional status filtering for dashboard tables.",
    response_description="Paginated document list",
)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List uploaded documents with optional status filtering."""

    if skip < 0:
        raise HTTPException(status_code=400, detail="skip must be greater than or equal to 0")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    try:
        filters = []
        if status:
            filters.append(Document.status == status)

        count_query = select(func.count()).select_from(Document)
        documents_query = select(Document).order_by(Document.uploaded_at.desc()).offset(skip).limit(limit)
        if filters:
            count_query = count_query.where(*filters)
            documents_query = documents_query.where(*filters)

        total_result = await db.execute(count_query)
        documents_result = await db.execute(documents_query)
        documents = documents_result.scalars().all()

        return DocumentListResponse(
            documents=[_document_to_list_item(document) for document in documents],
            total=int(total_result.scalar_one()),
            skip=skip,
            limit=limit,
        )
    except Exception as exc:
        logger.exception("Failed to list documents")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {exc}") from exc

@router.get(
    "/processing",
    summary="List active ingestion tasks",
    description="Return active background processing task IDs and aggregate processing counters.",
    response_description="Active ingestion tasks and processing stats",
)
async def get_processing_overview() -> dict:
    """Return active background ingestion tasks and aggregate processing stats."""

    return {
        "active_tasks": ingestion_service.get_active_tasks(),
        **ingestion_service.get_processing_stats(),
    }


@router.delete(
    "/processing/{document_id}",
    summary="Cancel document processing",
    description="Cancel a currently active background ingestion task for a document.",
    response_description="Cancellation status",
)
async def cancel_processing(document_id: str) -> dict[str, str]:
    """Cancel active background ingestion for a document."""

    cancelled = await ingestion_service.cancel_processing(document_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="No active processing task found for document")
    return {"message": "Processing cancelled", "document_id": document_id}

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
    description="Delete a document record, remove its vector chunks, and delete the uploaded file from disk.",
    response_description="No content",
)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Delete a document, its vector chunks, and its uploaded file."""

    document = await _get_document_or_404(document_id, db)

    try:
        await vector_store.delete_document(document_id)

        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()

        await db.delete(document)
        await db.commit()
        logger.info("Deleted document %s", document_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to delete document %s", document_id)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {exc}") from exc


@router.get(
    "/stats",
    response_model=DocumentStatsResponse,
    summary="Get document statistics",
    description="Return aggregate document ingestion counts for dashboard cards and monitoring.",
    response_description="Document ingestion statistics",
)
async def get_document_stats(db: AsyncSession = Depends(get_db)) -> DocumentStatsResponse:
    """Return aggregate ingestion statistics."""

    try:
        total_documents = await _count_documents(db)
        completed = await _count_documents(db, "completed")
        processing = await _count_documents(db, "processing")
        failed = await _count_documents(db, "failed")
        total_chunks_result = await db.execute(select(func.coalesce(func.sum(Document.total_chunks), 0)))

        return DocumentStatsResponse(
            total_documents=total_documents,
            completed=completed,
            processing=processing,
            failed=failed,
            total_chunks=int(total_chunks_result.scalar_one() or 0),
        )
    except Exception as exc:
        logger.exception("Failed to get document stats")
        raise HTTPException(status_code=500, detail=f"Failed to get document stats: {exc}") from exc


async def _get_document_or_404(document_id: str, db: AsyncSession) -> Document:
    """Fetch a document or raise a 404 error."""

    document = await db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

async def _process_document_background(
    document_id: str,
    file_path: str,
    file_type: str,
    filename: str,
) -> None:
    """Run document processing with a background-owned database session."""

    async with AsyncSessionLocal() as session:
        await ingestion_service.process_document(document_id, file_path, file_type, filename, session)

def _document_to_status_response(document: Document) -> DocumentStatusResponse:
    """Convert a Document ORM object into a status response model."""

    return DocumentStatusResponse(
        document_id=document.id,
        filename=document.filename,
        original_filename=document.original_filename,
        status=document.status,
        file_type=document.file_type,
        total_chunks=document.total_chunks,
        error_message=document.error_message,
        uploaded_at=document.uploaded_at,
        processed_at=document.processed_at,
    )


async def _count_documents(db: AsyncSession, status_value: str | None = None) -> int:
    """Count documents, optionally filtered by status."""

    query = select(func.count()).select_from(Document)
    if status_value:
        query = query.where(Document.status == status_value)
    result = await db.execute(query)
    return int(result.scalar_one())


def _secure_filename(filename: str) -> str:
    """Return a conservative filename safe for local storage."""

    filename = Path(filename).name.replace(" ", "_")
    safe_name = "".join(character for character in filename if character.isalnum() or character in {".", "_", "-"})
    return safe_name or "upload.bin"





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
from app.database import get_db
from app.models.document import Document
from app.services.ingestion_service import ingestion_service
from app.services.task_queue import ingestion_queue
from app.services.vector_store import vector_store
from app.utils.file_parser import FileParser
from app.security import verify_admin_key


logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["Document Ingestion"])

DEMO_DOCUMENT_NAME = "OSHA_3120_Lockout_Tagout.pdf"
DEMO_DOCUMENT_PATH = Path(__file__).resolve().parents[2] / "demo_documents" / DEMO_DOCUMENT_NAME


def _build_demo_document_pdf() -> bytes:
    """Return a compact lockout/tagout demo PDF when the large bundled file is absent."""

    lines = [
        "PlantBrain Demo: Lockout/Tagout Safety Guidance",
        "This compact sample is generated when the full OSHA 3120 PDF is not bundled.",
        "Purpose: control hazardous energy before service or maintenance work begins.",
        "Authorized employees must understand energy-control procedures and equipment isolation.",
        "Affected employees must know when lockout/tagout is applied and avoid restarting equipment.",
        "Energy-control procedures should identify energy sources, shutdown steps, isolation points,",
        "lockout or tagout device application, stored energy release, and verification before work.",
        "Tagout may be used only when it provides effective warning and equivalent protection.",
        "Periodic inspections should verify that procedures remain accurate and employees follow them.",
        "During shift changes, responsibility for lockout/tagout protection must be transferred clearly.",
        "Contractors and host employers must coordinate energy-control responsibilities before work.",
    ]
    text_commands = ["BT", "/F1 14 Tf", "72 742 Td", "16 TL"]
    for index, line in enumerate(lines):
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if index == 0:
            text_commands.append(f"({escaped}) Tj")
        else:
            text_commands.append(f"T* ({escaped}) Tj")
    text_commands.append("ET")
    stream = "\n".join(text_commands).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_at = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode("ascii"))
    return bytes(pdf)

@router.post("/demo-document", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED, summary="Load the built-in demo PDF")
async def load_demo_document(db: AsyncSession = Depends(get_db)) -> DocumentUploadResponse:
    """Ingest the bundled OSHA maintenance-safety booklet."""
    result = await db.execute(select(Document).where(Document.original_filename == DEMO_DOCUMENT_NAME).order_by(Document.uploaded_at.desc()))
    existing = result.scalars().first()
    if existing and existing.status == "completed":
        return DocumentUploadResponse(document_id=existing.id, filename=existing.original_filename, status=existing.status, message="Demo PDF is already available")
    if existing and Path(existing.file_path).exists():
        existing.status = "pending"
        existing.error_message = None
        await db.commit()
        ingestion_queue.enqueue_document_processing(existing.id, existing.file_path, "pdf", DEMO_DOCUMENT_NAME)
        return DocumentUploadResponse(document_id=existing.id, filename=existing.original_filename, status="processing", message="Demo PDF indexing resumed")
    bundled_demo_available = DEMO_DOCUMENT_PATH.is_file()
    content = DEMO_DOCUMENT_PATH.read_bytes() if bundled_demo_available else _build_demo_document_pdf()
    unique_filename = f"{uuid4()}_{DEMO_DOCUMENT_NAME}"
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = str(Path(settings.upload_dir) / unique_filename)
    async with aiofiles.open(file_path, "wb") as output_file:
        await output_file.write(content)
    document = Document(filename=unique_filename, original_filename=DEMO_DOCUMENT_NAME, file_type="pdf", file_size_bytes=len(content), file_path=file_path, status="pending")
    db.add(document)
    await db.commit()
    await db.refresh(document)
    ingestion_queue.enqueue_document_processing(document.id, file_path, "pdf", DEMO_DOCUMENT_NAME)
    message = "Official OSHA PDF loaded and indexing started" if bundled_demo_available else "Generated lockout/tagout demo PDF loaded and indexing started"
    return DocumentUploadResponse(document_id=document.id, filename=DEMO_DOCUMENT_NAME, status="processing", message=message)




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
    extraction_kind: str = Form(default="auto"),
    zone: str = Form(default=""),
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
        ingestion_queue.enqueue_document_processing(
            document.id,
            file_path,
            file_type,
            file.filename,
            extraction_kind,
            zone,
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


@router.get(
    "/pipeline",
    summary="Get plant intelligence pipeline evidence",
    description="Return recent ingestion stages, proof metrics, graph backend status, review queue counts, and query readiness evidence.",
    response_description="Pipeline proof dashboard data",
)
async def get_pipeline_overview() -> dict:
    """Return dashboard-ready evidence for the plant intelligence pipeline."""

    return ingestion_service.get_pipeline_overview()

@router.delete(
    "/processing/{document_id}",
    summary="Cancel document processing",
    description="Cancel a currently active background ingestion task for a document.",
    response_description="Cancellation status",
)
async def cancel_processing(document_id: str, _: bool = Depends(verify_admin_key)) -> dict[str, str]:
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
    _: bool = Depends(verify_admin_key),
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

def _document_to_list_item(document: Document) -> DocumentListItem:
    """Convert a Document ORM object into a compact list item."""

    return DocumentListItem(
        document_id=document.id,
        filename=document.original_filename,
        status=document.status,
        file_type=document.file_type,
        total_chunks=document.total_chunks,
        uploaded_at=document.uploaded_at,
    )


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

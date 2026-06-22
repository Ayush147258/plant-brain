import json
import logging
import io
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pypdf import PdfReader

from app.models.schemas import DocumentUploadResponse
from app.core.document_store import upload_document, list_documents

logger = logging.getLogger("plantbrain.api.documents")
router = APIRouter()

@router.get("/documents")
async def get_documents():
    """
    List all documents (summary).
    """
    docs = await list_documents()
    return docs

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    metadata: str = Form(...) # JSON string
):
    """
    Upload a document (TXT or PDF).
    """
    MAX_SIZE = 10 * 1024 * 1024 # 10MB
    
    if file.content_type not in ["text/plain", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Only TXT and PDF files are supported.")
        
    content_bytes = await file.read()
    if len(content_bytes) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 10MB limit.")
        
    try:
        meta_dict = json.loads(metadata)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON format.")
        
    text_content = ""
    if file.content_type == "text/plain":
        try:
            text_content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="TXT file must be UTF-8 encoded.")
    elif file.content_type == "application/pdf":
        try:
            pdf_file = io.BytesIO(content_bytes)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content += extracted + "\n"
        except Exception as e:
            logger.error(f"PDF Extraction failed: {e}")
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF.")
            
    if not text_content.strip():
        raise HTTPException(status_code=400, detail="No readable text found in file.")
        
    try:
        doc_id = await upload_document(
            filename=file.filename,
            content=text_content,
            source_type=source_type,
            metadata=meta_dict
        )
        return DocumentUploadResponse(
            document_id=doc_id,
            message="Document uploaded successfully"
        )
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save document.")

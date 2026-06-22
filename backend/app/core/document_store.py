"""
Supabase SQL Table Definition:

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_type TEXT NOT NULL,
    page_or_section TEXT NOT NULL,
    freshness_score FLOAT DEFAULT 1.0,
    last_validated_date DATE,
    equipment_tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

import uuid
import logging
from typing import List, Dict, Any
from datetime import datetime
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger("plantbrain.document_store")

# Initialize Supabase client
# Ensure we handle case where config validation fails but we still want to import this in tests
try:
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
except Exception as e:
    logger.warning(f"Failed to initialize Supabase client: {e}")
    supabase = None

async def get_relevant_documents(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve top_k documents based on keyword matching relevance.
    Scores documents based on term frequency of query words.
    """
    try:
        response = supabase.table("documents").select("*").execute()
        documents = response.data
        
        if not documents:
            return []
            
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        if not query_terms:
            return documents[:top_k]
            
        scored_docs = []
        for doc in documents:
            score = 0.0
            title = (doc.get("title") or "").lower()
            content = (doc.get("content") or "").lower()
            
            for term in query_terms:
                if term in title:
                    score += 2.0
                
                score += content.count(term) * 0.5
                
            norm_score = min(score / (len(query_terms) * 3), 1.0)
            
            if score > 0:
                doc["relevance_score"] = norm_score
                scored_docs.append(doc)
                
        scored_docs.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return scored_docs[:top_k]
        
    except Exception as e:
        logger.error(f"Error retrieving documents from Supabase: {e}")
        return []

async def upload_document(
    filename: str,
    content: str,
    source_type: str,
    metadata: Dict[str, Any]
) -> str:
    """
    Upload a document to Supabase database.
    """
    try:
        doc_id = str(uuid.uuid4())
        
        data = {
            "id": doc_id,
            "title": filename,
            "content": content,
            "source_type": source_type,
            "page_or_section": metadata.get("page_or_section", "1"),
            "freshness_score": metadata.get("freshness_score", 1.0),
            "last_validated_date": metadata.get("last_validated_date", datetime.now().strftime("%Y-%m-%d")),
            "equipment_tags": metadata.get("equipment_tags", [])
        }
        
        supabase.table("documents").insert(data).execute()
        logger.info(f"Uploaded document {filename} with ID {doc_id}")
        return doc_id
        
    except Exception as e:
        logger.error(f"Error uploading document to Supabase: {e}")
        raise

async def list_documents() -> List[Dict[str, Any]]:
    """
    List all documents (summary format).
    """
    try:
        response = supabase.table("documents").select(
            "id, title, source_type, freshness_score, last_validated_date, equipment_tags"
        ).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return []

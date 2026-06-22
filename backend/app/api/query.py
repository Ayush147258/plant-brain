import time
import logging
import json
import asyncio
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse

from app.models.schemas import QueryRequest, QueryResponse, DocumentSummary, ErrorResponse
from app.core.document_store import get_relevant_documents
from app.core.llm_router import query_with_fallback

logger = logging.getLogger("plantbrain.api.query")
router = APIRouter()

SYSTEM_PROMPT = """You are PlantBrain, an advanced industrial knowledge AI assistant.
Your goal is to answer technical, maintenance, and compliance questions using ONLY the provided context documents.

Instructions:
1. Answer using plain, clear technical language suitable for plant engineers and technicians.
2. Cite your sources explicitly by mentioning the Document Title (e.g., "According to the P-201 Manual...").
3. If the provided documents do not contain the answer, state clearly: "I cannot find a definitive answer in the current documents." Do NOT guess or hallucinate.
4. Keep the answer concise but thorough.
"""

@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute a standard non-streaming query against the knowledge base.
    """
    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(status_code=422, detail="Question cannot be empty")
        
    if len(request.question) > 500:
        raise HTTPException(status_code=422, detail="Question exceeds 500 characters")
        
    # Retrieve relevant documents
    docs = await get_relevant_documents(request.question, top_k=5)
    
    # Filter documents to ensure at least some relevance
    relevant_docs = [d for d in docs if d.get("relevance_score", 0) > 0.1]
    
    if not relevant_docs:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="Not Found",
                message="No relevant documents found for this query",
                detail="Try rephrasing your question or adding different keywords."
            ).model_dump()
        )
        
    # Query LLM with fallback
    try:
        llm_response = await query_with_fallback(
            system_prompt=SYSTEM_PROMPT,
            user_message=request.question,
            context_documents=relevant_docs
        )
    except Exception as e:
        logger.error(f"LLM Query Failed: {e}")
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error="Service Unavailable",
                message="Both primary and fallback AI models are currently unavailable.",
                detail=str(e)
            ).model_dump()
        )
        
    logger.info(f"Query: '{request.question[:50]}...' Model: {llm_response.model_used} "
                f"Latency: {llm_response.latency_ms}ms Confidence: {llm_response.confidence_score}")
                
    # Prepare Document Summaries
    retrieved_docs = [
        DocumentSummary(
            title=doc.get("title", "Unknown"),
            freshness_score=float(doc.get("freshness_score", 1.0))
        )
        for doc in relevant_docs
    ]
    
    return QueryResponse(
        answer=llm_response.answer,
        sources_used=llm_response.sources_used,
        confidence_score=llm_response.confidence_score,
        model_used=llm_response.model_used,
        latency_ms=llm_response.latency_ms,
        fallback_triggered=llm_response.fallback_triggered,
        retrieved_documents=retrieved_docs
    )

@router.post("/query/stream")
async def execute_query_stream(request: QueryRequest):
    """
    Execute a streaming query (Server-Sent Events) for live chat.
    """
    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(status_code=422, detail="Question cannot be empty")
        
    docs = await get_relevant_documents(request.question, top_k=5)
    relevant_docs = [d for d in docs if d.get("relevance_score", 0) > 0.1]
    
    if not relevant_docs:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="Not Found",
                message="No relevant documents found for this query"
            ).model_dump()
        )
        
    async def event_generator():
        try:
            llm_response = await query_with_fallback(
                system_prompt=SYSTEM_PROMPT,
                user_message=request.question,
                context_documents=relevant_docs
            )
            
            # Simulate streaming tokens for Phase 1
            words = llm_response.answer.split(" ")
            for word in words:
                yield f"data: {{\"type\": \"token\", \"data\": \"{word} \"}}\n\n"
                await asyncio.sleep(0.01)
                
            retrieved_docs = [
                DocumentSummary(
                    title=doc.get("title", "Unknown"),
                    freshness_score=float(doc.get("freshness_score", 1.0))
                ) for doc in relevant_docs
            ]
            
            final_response = QueryResponse(
                answer=llm_response.answer,
                sources_used=[s for s in llm_response.sources_used],
                confidence_score=llm_response.confidence_score,
                model_used=llm_response.model_used,
                latency_ms=llm_response.latency_ms,
                fallback_triggered=llm_response.fallback_triggered,
                retrieved_documents=retrieved_docs
            )
            
            # Using model_dump to serialize Pydantic models cleanly
            yield f"data: {{\"type\": \"done\", \"data\": {json.dumps(final_response.model_dump())}}}\n\n"
            
        except Exception as e:
            yield f"data: {{\"type\": \"error\", \"data\": \"{str(e)}\"}}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

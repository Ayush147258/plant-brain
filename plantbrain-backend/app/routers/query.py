"""Question answering API endpoints for PlantBrain."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas import FeedbackRequest, QuestionRequest, QuestionResponse, SourceInfo
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.query_log import QueryLog
from app.services.graph_service import graph_service
from app.services.llm_service import llm_service
from app.services.neo4j_service import neo4j_service
from app.services.vector_store import vector_store
from app.utils.text_chunker import TextChunker


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/query", tags=["Query"])



@router.post(
    "/ask",
    response_model=QuestionResponse,
    summary="Ask PlantBrain a question",
    description="Ask a natural language question in English or Hindi. PlantBrain searches document chunks, adds equipment graph context, and returns a cited answer with confidence.",
    response_description="Generated answer with sources and confidence",
)
async def ask_question(
    request: QuestionRequest,
    db: AsyncSession = Depends(get_db),
) -> QuestionResponse:
    """Answer a user question using vector retrieval, graph context, and Gemini."""

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        if not request.language or request.language == "auto":
            language = TextChunker.detect_language(request.question)
        else:
            language = request.language

        retrieved_chunks = await vector_store.search(
            question,
            top_k=request.top_k,
            filter_document_id=request.filter_document_id or None,
        )

        graph_context: list[dict] = []
        equipment_in_question: list[str] = []
        if request.include_graph_context:
            if neo4j_service.configured():
                try:
                    neo4j_context = neo4j_service.build_graph_rag_context(question, depth=2, limit=30)
                    graph_context = neo4j_service.format_graph_context(neo4j_context)
                    equipment_in_question = neo4j_context.get("seed_tags", [])
                except Exception as exc:
                    logger.warning("Neo4j graph context unavailable; answering from retrieved documents only: %s", exc)
                    equipment_in_question = graph_service.find_equipment_in_text(question)
                    for tag in equipment_in_question:
                        graph_context.extend(graph_service.get_neighbors(tag, depth=1))
            else:
                equipment_in_question = graph_service.find_equipment_in_text(question)
                for tag in equipment_in_question:
                    graph_context.extend(graph_service.get_neighbors(tag, depth=1))
        llm_result = await llm_service.answer_question(
            question,
            retrieved_chunks,
            graph_context,
            request.session_id,
            language=language,
        )

        confidence = llm_result.get("confidence", "Medium")
        confidence_map = {"High": 0.9, "Medium": 0.6, "Low": 0.3}
        query_log = QueryLog(
            question=question,
            language=language,
            answer=llm_result.get("answer", ""),
            sources=json.dumps([source.get("filename") for source in llm_result.get("sources", [])]),
            confidence=confidence_map.get(confidence, 0.6),
            response_time_ms=llm_result.get("response_time_ms", 0),
            channel=request.channel,
            session_id=request.session_id or None,
        )
        db.add(query_log)
        await db.commit()
        await db.refresh(query_log)

        answer = llm_result.get("answer", "")
        if neo4j_service.configured():
            try:
                answer_tags = neo4j_service.find_equipment_ids_in_text(answer)
            except Exception:
                logger.warning("Neo4j tag extraction unavailable; using local graph tag extraction")
                answer_tags = graph_service.find_equipment_in_text(answer)
        else:
            answer_tags = graph_service.find_equipment_in_text(answer)
        equipment_mentioned = _dedupe_preserve_order(equipment_in_question + answer_tags)

        return QuestionResponse(
            answer=answer,
            confidence=confidence,
            sources=_build_source_info(retrieved_chunks),
            response_time_ms=llm_result.get("response_time_ms", 0),
            query_id=query_log.id,
            equipment_mentioned=equipment_mentioned,
        )
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to answer question")
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {exc}") from exc


@router.get(
    "/history",
    summary="List query history",
    description="Return recent Q&A logs, optionally filtered by session ID for frontend conversation history.",
    response_description="Recent query log entries",
)
async def get_query_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session_id: str = "",
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return recent query logs, optionally filtered by session id."""

    try:
        filters = []
        if session_id:
            filters.append(QueryLog.session_id == session_id)

        count_query = select(func.count()).select_from(QueryLog)
        logs_query = select(QueryLog).order_by(QueryLog.created_at.desc()).offset(skip).limit(limit)
        if filters:
            count_query = count_query.where(*filters)
            logs_query = logs_query.where(*filters)

        total_result = await db.execute(count_query)
        logs_result = await db.execute(logs_query)
        logs = logs_result.scalars().all()

        return {
            "queries": [
                {
                    "id": log.id,
                    "question": log.question,
                    "answer": log.answer,
                    "confidence": log.confidence,
                    "created_at": log.created_at,
                    "response_time_ms": log.response_time_ms,
                }
                for log in logs
            ],
            "total": int(total_result.scalar_one()),
        }
    except Exception as exc:
        logger.exception("Failed to get query history")
        raise HTTPException(status_code=500, detail=f"Failed to get query history: {exc}") from exc


@router.get(
    "/history/{query_id}",
    summary="Get one query history item",
    description="Return the full stored question, answer, sources, channel, and feedback data for a query log entry.",
    response_description="Query log entry",
)
async def get_query_history_item(
    query_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return a single query log entry by id."""

    query_log = await db.get(QueryLog, query_id)
    if query_log is None:
        raise HTTPException(status_code=404, detail="Query not found")

    return {
        "id": query_log.id,
        "question": query_log.question,
        "answer": query_log.answer,
        "language": query_log.language,
        "sources": _parse_sources(query_log.sources),
        "confidence": query_log.confidence,
        "response_time_ms": query_log.response_time_ms,
        "channel": query_log.channel,
        "session_id": query_log.session_id,
        "helpful": query_log.helpful,
        "feedback_comment": query_log.feedback_comment,
        "created_at": query_log.created_at,
    }


@router.post(
    "/feedback/{query_id}",
    summary="Record answer feedback",
    description="Record whether an answer was helpful plus an optional user comment for later evaluation.",
    response_description="Feedback confirmation",
)
async def record_feedback(
    query_id: str,
    feedback: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Record helpfulness feedback for a query answer."""

    query_log = await db.get(QueryLog, query_id)
    if query_log is None:
        raise HTTPException(status_code=404, detail="Query not found")

    try:
        query_log.helpful = feedback.helpful
        query_log.feedback_comment = feedback.comment
        await db.commit()
        logger.info("Recorded feedback for query %s", query_id)
        return {"message": "Feedback recorded"}
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to record feedback for query %s", query_id)
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {exc}") from exc


@router.get(
    "/search-chunks",
    summary="Search retrieved chunks",
    description="Run raw vector search without LLM generation. Useful for debugging retrieval quality in frontend demos.",
    response_description="Retrieved chunks with metadata and distances",
)
async def search_chunks(
    query: str = Query(min_length=1),
    top_k: int = Query(default=5, ge=1, le=10),
    document_id: str = "",
) -> dict:
    """Search raw retrieved chunks without generating an LLM answer."""

    try:
        chunks = await vector_store.search(query, top_k=top_k, filter_document_id=document_id or None)
        return {
            "chunks": [
                {
                    "text": chunk.get("text", ""),
                    "metadata": chunk.get("metadata", {}),
                    "distance": chunk.get("distance"),
                }
                for chunk in chunks
            ],
            "query": query,
        }
    except Exception as exc:
        logger.exception("Failed to search chunks")
        raise HTTPException(status_code=500, detail=f"Failed to search chunks: {exc}") from exc


def _build_source_info(retrieved_chunks: list[dict]) -> list[SourceInfo]:
    """Build source info response objects from retrieved chunks."""

    sources = []
    for chunk in retrieved_chunks:
        metadata = chunk.get("metadata", {}) or {}
        sources.append(
            SourceInfo(
                filename=str(metadata.get("filename") or "Unknown"),
                chunk_index=int(metadata.get("chunk_index") or 0),
                text_preview=str(chunk.get("text", ""))[:300],
                page_number=int(metadata.get("page_number") or 0) or None,
                section=str(metadata.get("section_header") or ""),
            )
        )
    return sources


def _parse_sources(sources_json: str | None) -> list:
    """Parse stored source JSON safely."""

    if not sources_json:
        return []
    try:
        return json.loads(sources_json)
    except json.JSONDecodeError:
        return []


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    """Remove duplicate strings while preserving first-seen order."""

    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped

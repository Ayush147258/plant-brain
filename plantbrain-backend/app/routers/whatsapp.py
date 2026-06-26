"""Twilio WhatsApp webhook endpoints for PlantBrain."""

import hashlib
import html
import json
import logging
import re
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.document import Document
from app.models.query_log import QueryLog
from app.schemas import WhatsAppAlertRequest
from app.services.graph_service import graph_service
from app.services.llm_service import llm_service
from app.services.pattern_service import pattern_service
from app.services.vector_store import vector_store
from app.utils.text_chunker import TextChunker


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

HELP_TEXT = """*PlantBrain Help / प्लांटब्रेन सहायता*

Commands:
- HELP - Show this message
- STATUS - System status
- RISK - Risk summary

Or just type your question in English or Hindi:
- "What are the issues with pump P-202?"
- "P-202 पंप की क्या समस्याएं हैं?"
"""


@router.post(
    "/webhook",
    summary="Receive WhatsApp webhook",
    description="Twilio webhook endpoint for WhatsApp messages. Handles HELP, STATUS, RISK, and natural-language PlantBrain questions.",
    response_description="TwiML XML response",
)
async def whatsapp_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> PlainTextResponse:
    """Handle inbound Twilio WhatsApp messages as PlantBrain commands or questions."""

    try:
        form = await request.form()
        from_number = str(form.get("From", ""))
        message_body = str(form.get("Body", "")).strip()
        detected_lang = TextChunker.detect_language(message_body)
        session_id = hashlib.md5(from_number.encode()).hexdigest()[:12]
        logger.info("Incoming WhatsApp message from %s", _mask_phone(from_number))

        if not message_body:
            answer = "Please send a question or type HELP for commands."
        else:
            command = message_body.upper()
            if command == "HELP":
                answer = _help_text()
            elif command == "STATUS":
                answer = await _status_text(db)
            elif command == "RISK":
                answer = await _risk_text(db)
            else:
                answer = await _answer_whatsapp_question(message_body, session_id, db, detected_lang)

        formatted_answer = _format_whatsapp_answer(answer)
        return _twiml_response(formatted_answer)
    except Exception:
        logger.exception("Failed to handle WhatsApp webhook")
        return _twiml_response("PlantBrain could not process that message. Please try again.")


@router.get(
    "/webhook",
    summary="WhatsApp webhook health",
    description="Health check endpoint for Twilio webhook configuration.",
    response_description="Webhook health status",
)
async def whatsapp_webhook_health() -> dict[str, str]:
    """Return Twilio webhook health status."""

    return {"status": "PlantBrain WhatsApp webhook active"}


@router.post(
    "/send-alert",
    summary="Send WhatsApp alert",
    description="Send a proactive WhatsApp alert through Twilio for compliance or risk notifications.",
    response_description="Twilio message SID and status",
)
async def send_alert(payload: WhatsAppAlertRequest) -> dict[str, str]:
    """Send a proactive WhatsApp alert using Twilio's Messages API."""

    if not settings.twilio_account_sid:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Twilio alerts are not configured")

    account_sid = payload.twilio_account_sid or settings.twilio_account_sid
    auth_token = payload.twilio_auth_token or settings.twilio_auth_token
    from_number = payload.from_number or settings.twilio_whatsapp_from
    if not account_sid or not auth_token or not from_number:
        raise HTTPException(status_code=400, detail="Twilio account SID, auth token, and from number are required")

    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                url,
                data={"To": payload.to_number, "From": from_number, "Body": payload.message},
                auth=(account_sid, auth_token),
            )
            response.raise_for_status()
        data = response.json()
        logger.info("Sent WhatsApp alert to %s", _mask_phone(payload.to_number))
        return {"message_sid": data.get("sid", ""), "status": data.get("status", "queued")}
    except httpx.HTTPStatusError as exc:
        logger.exception("Twilio API rejected WhatsApp alert")
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except Exception as exc:
        logger.exception("Failed to send WhatsApp alert")
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {exc}") from exc


async def _answer_whatsapp_question(question: str, session_id: str, db: AsyncSession, language: str) -> str:
    """Answer a WhatsApp question using retrieval, graph context, and Gemini."""

    retrieved_chunks = await vector_store.search(question, top_k=5)
    graph_context: list[dict] = []
    for tag in graph_service.find_equipment_in_text(question):
        graph_context.extend(graph_service.get_neighbors(tag, depth=1))

    llm_result = await llm_service.answer_question(question, retrieved_chunks, graph_context, session_id, language=language)
    confidence = llm_result.get("confidence", "Medium")
    confidence_map = {"High": 0.9, "Medium": 0.6, "Low": 0.3}
    db.add(
        QueryLog(
            question=question,
            language=language,
            answer=llm_result.get("answer", ""),
            sources=json.dumps([source.get("filename") for source in llm_result.get("sources", [])]),
            confidence=confidence_map.get(confidence, 0.6),
            response_time_ms=llm_result.get("response_time_ms", 0),
            channel="whatsapp",
            session_id=session_id,
        )
    )
    await db.commit()

    answer = llm_result.get("answer", "")
    sources = llm_result.get("sources", [])
    first_source = next((source.get("filename") for source in sources if source.get("filename")), None)
    if first_source:
        answer = f"{answer}\n\nSource: {first_source}"
    return answer


async def _status_text(db: AsyncSession) -> str:
    """Format current PlantBrain status for WhatsApp."""

    total_result = await db.execute(select(func.count()).select_from(Document))
    total_documents = int(total_result.scalar_one())
    graph_nodes = len(graph_service.graph.nodes)
    return f"PlantBrain Status\nDocuments: {total_documents}\nGraph nodes: {graph_nodes}"


async def _risk_text(db: AsyncSession) -> str:
    """Format risk summary for WhatsApp."""

    summary = await pattern_service.get_risk_summary(db)
    return (
        "PlantBrain Risk Summary\n"
        f"Overall: {summary.get('overall_risk_level', 'Low')}\n"
        f"Failure clusters: {len(summary.get('failure_clusters', []))}\n"
        f"Overdue inspections: {summary.get('overdue_inspections_count', 0)}\n"
        f"Critical overdue: {len(summary.get('critical_overdue', []))}\n"
        f"Co-occurrence patterns: {len(summary.get('cooccurrence_patterns', []))}"
    )


def _help_text() -> str:
    """Return WhatsApp command help text."""

    return HELP_TEXT


def _format_whatsapp_answer(answer: str) -> str:
    """Format answer text for WhatsApp and keep it under Twilio's practical limit."""

    formatted = re.sub(r"\*\*(.*?)\*\*", r"*\1*", answer)
    formatted = re.sub(r"^#+\s*", "", formatted, flags=re.MULTILINE)
    formatted = formatted.strip()
    if len(formatted) <= 1500:
        return formatted

    truncated = formatted[:1450]
    sentence_end = max(truncated.rfind("."), truncated.rfind("?"), truncated.rfind("!"), truncated.rfind("।"))
    if sentence_end > 500:
        truncated = truncated[: sentence_end + 1]
    return f"{truncated.strip()}\n[Reply FULL for complete answer]"


def _twiml_response(message: str) -> PlainTextResponse:
    """Build a TwiML XML response."""

    escaped = html.escape(message, quote=False)
    body = f'<?xml version="1.0" encoding="UTF-8"?>\n<Response>\n  <Message>{escaped}</Message>\n</Response>'
    return PlainTextResponse(content=body, media_type="application/xml")


def _mask_phone(phone_number: str) -> str:
    """Mask the last four digits of a WhatsApp phone number for logging."""

    if len(phone_number) <= 4:
        return "****"
    return f"{phone_number[:-4]}****"

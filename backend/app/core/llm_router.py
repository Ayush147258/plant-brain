import time
import logging
import asyncio
from typing import List, Dict, Any, Tuple
import anthropic
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockerThreshold
import httpx

from app.core.config import settings
from app.models.schemas import LLMResponse, SourceCitation

logger = logging.getLogger("plantbrain.llm_router")

class LLMUnavailableError(Exception):
    """Raised when both primary and fallback LLMs fail to respond."""
    pass

# Configure Gemini explicitly
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

async def _call_claude(
    system_prompt: str,
    user_message: str,
    context_text: str,
    max_tokens: int = 1000
) -> Tuple[str, int]:
    """Call Claude API with 30s timeout."""
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        client = anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            http_client=http_client
        )
        
        full_prompt = f"{context_text}\n\nQuestion: {user_message}"
        
        response = await client.messages.create(
            model="claude-sonnet-4-6", # Per requirements
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )
        
    latency_ms = int((time.time() - start_time) * 1000)
    return response.content[0].text, latency_ms

async def _call_gemini(
    system_prompt: str,
    user_message: str,
    context_text: str,
    max_tokens: int = 1000
) -> Tuple[str, int]:
    """Call Gemini 2.0 Flash API with 30s timeout."""
    start_time = time.time()
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    full_prompt = f"{system_prompt}\n\n{context_text}\n\nQuestion: {user_message}"
    
    try:
        response = await asyncio.wait_for(
            model.generate_content_async(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockerThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockerThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockerThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockerThreshold.BLOCK_NONE,
                }
            ),
            timeout=30.0
        )
        answer = response.text
    except asyncio.TimeoutError:
        raise httpx.TimeoutException("Gemini timed out")
        
    latency_ms = int((time.time() - start_time) * 1000)
    return answer, latency_ms

def _compute_confidence_score(answer: str, context_documents: List[Dict[str, Any]]) -> float:
    """
    Compute confidence score by checking how many provided documents
    were actually referenced or share terms with the answer.
    """
    if not context_documents:
        return 0.20
        
    matched_docs = 0
    answer_lower = answer.lower()
    
    for doc in context_documents:
        title_lower = doc.get("title", "").lower()
        if title_lower and title_lower in answer_lower:
            matched_docs += 1
            continue
            
        content = doc.get("content", "").lower()
        words = set([w for w in content.split() if len(w) > 5])
        matches = sum(1 for w in words if w in answer_lower)
        if matches >= 3:
            matched_docs += 1
            
    if matched_docs >= 3:
        return 0.90
    elif matched_docs == 2:
        return 0.75
    elif matched_docs == 1:
        return 0.55
    else:
        return 0.30

def _extract_citations(answer: str, context_documents: List[Dict[str, Any]]) -> List[SourceCitation]:
    """Extract which documents were cited in the answer."""
    citations = []
    answer_lower = answer.lower()
    
    for doc in context_documents:
        title = doc.get("title", "")
        if title and title.lower() in answer_lower:
            excerpt = doc.get("content", "")[:197] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", "")
            citations.append(
                SourceCitation(
                    document_title=title,
                    source_type=doc.get("source_type", "manual"),
                    excerpt=excerpt,
                    page_or_section=doc.get("page_or_section", "1"),
                    freshness_score=float(doc.get("freshness_score", 1.0))
                )
            )
    return citations

async def query_with_fallback(
    system_prompt: str,
    user_message: str,
    context_documents: List[Dict[str, Any]],
    max_tokens: int = 1000
) -> LLMResponse:
    """
    Execute AI query using Claude primarily, falling back to Gemini on failure.
    """
    context_text = "Context Documents:\n"
    for i, doc in enumerate(context_documents, 1):
        context_text += f"\n[{i}] Title: {doc.get('title')}\n"
        context_text += f"Type: {doc.get('source_type')}\n"
        context_text += f"Content: {doc.get('content')}\n"
        
    context_text += "\nInstructions: Use the documents above to answer. Cite by Title."

    answer = ""
    latency_ms = 0
    model_used = ""
    fallback_triggered = False
    
    try:
        answer, latency_ms = await _call_claude(
            system_prompt, user_message, context_text, max_tokens
        )
        model_used = "claude-sonnet-4-6"
    except (anthropic.RateLimitError, httpx.TimeoutException, httpx.RequestError) as e:
        logger.warning(f"Claude primary failed with {type(e).__name__}: {str(e)}. Triggering Gemini fallback.")
        fallback_triggered = True
    except anthropic.APIStatusError as e:
        if e.status_code >= 500 or e.status_code == 429 or e.status_code == 529:
            logger.warning(f"Claude primary returned {e.status_code}. Triggering Gemini fallback.")
            fallback_triggered = True
        else:
            raise
            
    if fallback_triggered:
        try:
            answer, latency_ms = await _call_gemini(
                system_prompt, user_message, context_text, max_tokens
            )
            model_used = "gemini-2.0-flash"
            logger.info(f"Gemini fallback succeeded in {latency_ms}ms")
        except Exception as e:
            logger.error(f"Gemini fallback failed: {str(e)}")
            raise LLMUnavailableError("Both primary (Claude) and fallback (Gemini) LLMs are currently unavailable.")
            
    confidence_score = _compute_confidence_score(answer, context_documents)
    citations = _extract_citations(answer, context_documents)
    
    logger.info(f"Query completed using {model_used} in {latency_ms}ms with confidence {confidence_score}")
    
    return LLMResponse(
        answer=answer,
        sources_used=citations,
        confidence_score=confidence_score,
        model_used=model_used,
        latency_ms=latency_ms,
        fallback_triggered=fallback_triggered
    )

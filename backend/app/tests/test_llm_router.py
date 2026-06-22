import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import TimeoutException
import anthropic

from app.core.llm_router import query_with_fallback, LLMUnavailableError, _compute_confidence_score

@pytest.fixture
def sample_context():
    return [
        {"title": "Pump Manual", "content": "The pump P-201 requires frequent alignment.", "source_type": "manual", "page_or_section": "1", "freshness_score": 1.0},
        {"title": "Safety Guide", "content": "Always wear PPE near P-201.", "source_type": "procedure", "page_or_section": "2", "freshness_score": 0.8},
        {"title": "Inspection Report", "content": "Vibration on P-201 was high.", "source_type": "inspection", "page_or_section": "3", "freshness_score": 0.5},
        {"title": "Work Order", "content": "Fixed bearing on P-201.", "source_type": "work_order", "page_or_section": "4", "freshness_score": 0.9},
        {"title": "Regulation OISD", "content": "Pumps must be audited.", "source_type": "regulation", "page_or_section": "5", "freshness_score": 1.0}
    ]

@pytest.mark.asyncio
@patch("app.core.llm_router._call_claude")
async def test_successful_claude(mock_claude, sample_context):
    mock_claude.return_value = ("According to the Pump Manual, alignment is needed.", 150)
    
    result = await query_with_fallback("system", "How to fix P-201?", sample_context)
    
    assert result.model_used == "claude-sonnet-4-6"
    assert result.fallback_triggered is False
    assert result.latency_ms == 150
    assert len(result.sources_used) >= 1

@pytest.mark.asyncio
@patch("app.core.llm_router._call_gemini")
@patch("app.core.llm_router._call_claude")
async def test_claude_ratelimit_triggers_gemini(mock_claude, mock_gemini, sample_context):
    mock_claude.side_effect = anthropic.RateLimitError(
        message="Rate limit exceeded",
        response=MagicMock(),
        body={}
    )
    mock_gemini.return_value = ("Gemini says check Pump Manual.", 250)
    
    result = await query_with_fallback("system", "How to fix P-201?", sample_context)
    
    assert result.model_used == "gemini-2.0-flash"
    assert result.fallback_triggered is True
    assert result.latency_ms == 250

@pytest.mark.asyncio
@patch("app.core.llm_router._call_gemini")
@patch("app.core.llm_router._call_claude")
async def test_both_fail_raises_error(mock_claude, mock_gemini, sample_context):
    mock_claude.side_effect = TimeoutException("Claude timed out")
    mock_gemini.side_effect = TimeoutException("Gemini timed out")
    
    with pytest.raises(LLMUnavailableError):
        await query_with_fallback("system", "How to fix P-201?", sample_context)

def test_confidence_score_computation(sample_context):
    # 0 documents matched
    score_0 = _compute_confidence_score("Random irrelevant answer about unicorns.", sample_context)
    
    # 1 document matched
    score_1 = _compute_confidence_score("The Pump Manual mentions alignment.", sample_context)
    
    # 3 documents matched
    score_3 = _compute_confidence_score("The Pump Manual says alignment. The Safety Guide says PPE. The Inspection Report noted vibration.", sample_context)
    
    # 5 documents matched
    score_5 = _compute_confidence_score("Pump Manual, Safety Guide, Inspection Report, Work Order, Regulation OISD all apply here.", sample_context)
    
    assert score_0 < score_1
    assert score_1 < score_3
    assert score_3 <= score_5
    assert score_0 <= 0.40
    assert score_5 >= 0.85

@pytest.mark.asyncio
async def test_claude_timeout_behavior():
    # Test that a simulated timeout raises TimeoutException
    from httpx import TimeoutException
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        from app.core.llm_router import _call_claude
        with patch("anthropic.AsyncAnthropic") as mock_anthropic:
            mock_anthropic_instance = MagicMock()
            mock_anthropic.return_value = mock_anthropic_instance
            mock_anthropic_instance.messages.create = AsyncMock(side_effect=TimeoutException("Timeout"))
            
            with pytest.raises(TimeoutException):
                await _call_claude("sys", "user", "context")

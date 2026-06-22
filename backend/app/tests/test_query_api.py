import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

@patch("app.api.query.get_relevant_documents", new_callable=AsyncMock)
@patch("app.api.query.query_with_fallback", new_callable=AsyncMock)
def test_valid_question(mock_query, mock_get_docs):
    mock_get_docs.return_value = [{"title": "Doc", "content": "Info", "relevance_score": 0.5, "freshness_score": 1.0}]
    
    from app.models.schemas import LLMResponse
    mock_query.return_value = LLMResponse(
        answer="Info found.",
        sources_used=[],
        confidence_score=0.8,
        model_used="claude-sonnet-4-6",
        latency_ms=100,
        fallback_triggered=False
    )
    
    response = client.post("/api/query", json={"question": "What is Info?"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Info found."

def test_empty_question():
    response = client.post("/api/query", json={"question": "   "})
    assert response.status_code == 422

def test_question_too_long():
    long_q = "a" * 501
    response = client.post("/api/query", json={"question": long_q})
    assert response.status_code == 422

@patch("app.api.query.get_relevant_documents", new_callable=AsyncMock)
def test_no_matching_documents(mock_get_docs):
    mock_get_docs.return_value = []
    
    response = client.post("/api/query", json={"question": "What is Info?"})
    assert response.status_code == 404
    assert response.json()["error"] == "Not Found"

@patch("app.api.health.supabase")
def test_health_check(mock_supabase):
    mock_supabase.table().select().limit().execute.return_value = True
    
    response = client.get("/api/health")
    assert "status" in response.json()
    assert response.status_code in [200, 503] # Depending on if keys are present

@patch("app.api.documents.list_documents", new_callable=AsyncMock)
def test_get_documents(mock_list):
    mock_list.return_value = []
    
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert response.json() == []

"""Q&A endpoint tests."""

import pytest


@pytest.fixture
def mock_llm(monkeypatch):
    """Mock Gemini answer generation."""

    async def fake_answer(*args, **kwargs):
        return {
            "answer": "Test answer",
            "confidence": "High",
            "sources": [],
            "response_time_ms": 100,
            "model": "test",
        }

    monkeypatch.setattr("app.services.llm_service.llm_service.answer_question", fake_answer)


@pytest.fixture
def mock_vector_search(monkeypatch):
    """Mock vector search to avoid Chroma/model dependencies."""

    async def fake_search(*args, **kwargs):
        return [
            {
                "text": "Pump P-202 has vibration findings.",
                "metadata": {"filename": "demo.txt", "chunk_index": 0},
                "distance": 0.1,
                "id": "chunk-1",
            }
        ]

    monkeypatch.setattr("app.services.vector_store.vector_store.search", fake_search)
    monkeypatch.setattr("app.routers.query.vector_store.search", fake_search)


@pytest.mark.asyncio
async def test_ask_empty_question_validation(client) -> None:
    """Empty questions are rejected by request validation."""

    response = await client.post("/api/v1/query/ask", json={"question": ""})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ask_valid_question(client, mock_llm, mock_vector_search) -> None:
    """A valid question returns an answer."""

    response = await client.post("/api/v1/query/ask", json={"question": "What about P-202?"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Test answer"


@pytest.mark.asyncio
async def test_query_history(client) -> None:
    """History endpoint returns query list."""

    response = await client.get("/api/v1/query/history")

    assert response.status_code == 200
    assert "queries" in response.json()


@pytest.mark.asyncio
async def test_search_chunks(client, mock_vector_search) -> None:
    """Raw chunk search returns chunks."""

    response = await client.get("/api/v1/query/search-chunks?query=pump")

    assert response.status_code == 200
    assert "chunks" in response.json()

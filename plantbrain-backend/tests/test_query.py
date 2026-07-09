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
                "metadata": {"filename": "demo.txt", "chunk_index": 0, "page_number": 3, "section_header": "Maintenance"},
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
    body = response.json()
    assert "Trust Summary" in body["answer"]
    assert "Test answer" in body["answer"]
    assert body["trust_summary"]["engine"] == "Knowledge Decay Engine"
    assert body["trust_summary"]["sources"] == 1


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


@pytest.mark.asyncio
async def test_ask_returns_page_aware_citation(client, mock_llm, mock_vector_search) -> None:
    """Retrieved filename, page, and section survive the API citation contract."""

    response = await client.post("/api/v1/query/ask", json={"question": "What about P-202?"})

    assert response.status_code == 200
    source = response.json()["sources"][0]
    assert source["filename"] == "demo.txt"
    assert source["page_number"] == 3
    assert source["section"] == "Maintenance"
    assert source["freshness_score"] is not None


@pytest.mark.asyncio
async def test_ask_exposes_low_freshness_trust_gate(client, mock_llm, monkeypatch) -> None:
    """Stale review metadata reaches the final trust summary."""

    async def stale_search(*args, **kwargs):
        return [
            {
                "text": "Pump P-201 maintenance procedure. Last reviewed: 2022-01-01. Verify revision before use.",
                "metadata": {"filename": "P-201 Procedure.pdf", "chunk_index": 0, "section_header": "Maintenance"},
                "distance": 0.05,
                "id": "stale-chunk",
            }
        ]

    monkeypatch.setattr("app.services.vector_store.vector_store.search", stale_search)
    monkeypatch.setattr("app.routers.query.vector_store.search", stale_search)

    response = await client.post("/api/v1/query/ask", json={"question": "Can I safely follow this procedure?"})

    assert response.status_code == 200
    summary = response.json()["trust_summary"]
    assert summary["risk"] in {"High", "Critical"}
    assert summary["knowledge_decay"] >= 60
    assert "Trust Gate" in response.json()["answer"]


@pytest.mark.asyncio
async def test_ask_returns_p201_graph_context(client, mock_llm, mock_vector_search) -> None:
    """P-201 judge prompt returns connected graph assets for the frontend card."""

    response = await client.post(
        "/api/v1/query/ask",
        json={"question": "Show all equipment connected to Pump P-201 and cite every source."},
    )

    assert response.status_code == 200
    body = response.json()
    mentioned = set(body["equipment_mentioned"])
    assert "P-201" in mentioned
    assert {"XV-201", "M-201", "PT-201"} & mentioned
    assert body["graph_context"]
    assert body["trust_summary"]["graph_assets"] >= 2
@pytest.mark.asyncio
async def test_ask_degrades_when_vector_search_fails(client, mock_llm, monkeypatch) -> None:
    """A vector-store outage should not turn Ask into HTTP 500."""

    async def failing_search(*args, **kwargs):
        raise RuntimeError("vector store unavailable")

    monkeypatch.setattr("app.services.vector_store.vector_store.search", failing_search)
    monkeypatch.setattr("app.routers.query.vector_store.search", failing_search)

    response = await client.post("/api/v1/query/ask", json={"question": "What about P-201?"})

    assert response.status_code == 200
    body = response.json()
    assert "Trust Summary" in body["answer"]
    assert body["sources"] == []
    assert body["trust_summary"]["risk"] == "Critical"


@pytest.mark.asyncio
async def test_ask_degrades_when_query_log_write_fails(client, mock_llm, mock_vector_search, monkeypatch) -> None:
    """A query-history write failure should not block the answer response."""
    from sqlalchemy.ext.asyncio import AsyncSession

    async def failing_commit(self):
        raise RuntimeError("database write unavailable")

    monkeypatch.setattr(AsyncSession, "commit", failing_commit)

    response = await client.post("/api/v1/query/ask", json={"question": "What about P-202?"})

    assert response.status_code == 200
    body = response.json()
    assert body["query_id"]
    assert "Test answer" in body["answer"]
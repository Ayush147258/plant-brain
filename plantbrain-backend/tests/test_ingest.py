"""Document ingestion endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_ingest_stats_empty(client) -> None:
    """Stats endpoint returns required keys."""

    response = await client.get("/api/v1/ingest/stats")

    assert response.status_code == 200
    body = response.json()
    assert "total_documents" in body
    assert "completed" in body
    assert "processing" in body
    assert "failed" in body
    assert "total_chunks" in body


@pytest.mark.asyncio
async def test_ingest_list_empty(client) -> None:
    """List endpoint works on an empty or fresh DB."""

    response = await client.get("/api/v1/ingest/list")

    assert response.status_code == 200
    body = response.json()
    assert "documents" in body
    assert "total" in body


@pytest.mark.asyncio
async def test_upload_tiny_text_file(client, monkeypatch) -> None:
    """Uploading a tiny text file returns accepted with a document id."""

    async def fake_process_document(*args, **kwargs):
        return {"success": True, "chunks_created": 1}

    monkeypatch.setattr("app.routers.ingest.ingestion_service.process_document", fake_process_document)
    files = {"file": ("test.txt", b"Test document text", "text/plain")}
    response = await client.post("/api/v1/ingest/upload", files=files, data={"description": "test"})

    assert response.status_code == 202
    assert "document_id" in response.json()


@pytest.mark.asyncio
async def test_get_status_for_uploaded_document(client, monkeypatch) -> None:
    """A valid uploaded document id can be queried for status."""

    async def fake_process_document(*args, **kwargs):
        return {"success": True, "chunks_created": 1}

    monkeypatch.setattr("app.routers.ingest.ingestion_service.process_document", fake_process_document)
    response = await client.post(
        "/api/v1/ingest/upload",
        files={"file": ("status.txt", b"Status test text", "text/plain")},
    )
    document_id = response.json()["document_id"]

    status_response = await client.get(f"/api/v1/ingest/status/{document_id}")

    assert status_response.status_code == 200
    assert status_response.json()["document_id"] == document_id


@pytest.mark.asyncio
async def test_get_status_nonexistent(client) -> None:
    """Unknown document status returns 404."""

    response = await client.get("/api/v1/ingest/status/nonexistent")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_rejects_large_file(client) -> None:
    """Files larger than the configured limit are rejected."""

    large_bytes = b"0" * (51 * 1024 * 1024)
    response = await client.post(
        "/api/v1/ingest/upload",
        files={"file": ("large.txt", large_bytes, "text/plain")},
    )

    assert response.status_code == 400

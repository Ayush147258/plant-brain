"""Pending review graph-write tests."""

from __future__ import annotations

import json

import pytest

from app.services.neo4j_service import Neo4jService, neo4j_service


def test_low_confidence_pid_equipment_goes_to_pending_review_not_equipment(monkeypatch) -> None:
    """Low-confidence extraction is held for review instead of merged as Equipment."""

    service = Neo4jService()
    writes: list[tuple[str, dict]] = []
    monkeypatch.setattr(service, "_write", lambda query, params: writes.append((query, params)))

    result = service.merge_pid_extraction(
        {
            "zone": "Zone 3",
            "equipment": [{"id": "P-909", "type": "pump", "confidence": "low"}],
            "valves": [],
            "instruments": [],
            "confidence_flags": [],
        },
        "doc-low",
    )

    assert result["equipment"] == 0
    assert result["pending_review"] == 1
    pending_writes = [params for query, params in writes if "PendingReview" in query]
    assert pending_writes
    assert pending_writes[0]["rows"][0]["entity_type"] == "equipment"
    assert "P-909" in pending_writes[0]["rows"][0]["payload_json"]
    direct_equipment_writes = [query for query, params in writes if "UNWIND $equipment" in query and "MERGE (e:Equipment" in query]
    assert direct_equipment_writes == []


def test_document_low_confidence_sends_all_pid_items_to_pending_review(monkeypatch) -> None:
    """Document-level low confidence gates even medium-confidence entities."""

    service = Neo4jService()
    writes: list[tuple[str, dict]] = []
    monkeypatch.setattr(service, "_write", lambda query, params: writes.append((query, params)))

    result = service.merge_pid_extraction(
        {
            "zone": "Zone 9",
            "equipment": [{"id": "P-111", "type": "pump", "confidence": "medium"}],
            "valves": [{"valve_id": "V-111", "valve_type": "gate", "connects_from": "P-111", "connects_to": "T-111", "confidence": "medium"}],
            "instruments": [{"tag": "PT-111", "attached_to_line_between": ["P-111", "T-111"], "confidence": "medium"}],
            "confidence_flags": [],
        },
        "doc-image-low",
        document_low_confidence=True,
    )

    assert result["equipment"] == 0
    assert result["valves"] == 0
    assert result["instruments"] == 0
    assert result["pending_review"] == 3
    pending_rows = [params["rows"] for query, params in writes if "PendingReview" in query][0]
    assert {row["entity_type"] for row in pending_rows} == {"equipment", "valve", "instrument"}


def test_promote_pending_review_merges_equipment_and_archives(monkeypatch) -> None:
    """Promotion applies corrections, writes the real node, and archives the review."""

    service = Neo4jService()
    merged: list[tuple[str, dict]] = []
    archived: list[tuple[str, str, dict]] = []
    review = {
        "id": "doc-low:equipment:P-909",
        "entity_type": "equipment",
        "payload_json": json.dumps({"id": "P-909", "type": "pump", "source_document_id": "doc-low"}),
    }
    monkeypatch.setattr(service, "_get_pending_review", lambda review_id: review)
    monkeypatch.setattr(service, "merge_equipment", lambda tag, attrs: merged.append((tag, attrs)) or {"id": tag})
    monkeypatch.setattr(service, "_archive_pending_review", lambda review_id, status, fields: archived.append((review_id, status, fields)))

    result = service.promote_pending_review("doc-low:equipment:P-909", {"equipment_type": "centrifugal pump"})

    assert result["status"] == "promoted"
    assert merged == [("P-909", {"id": "P-909", "type": "pump", "source_document_id": "doc-low", "equipment_type": "centrifugal pump"})]
    assert archived == [("doc-low:equipment:P-909", "promoted", {"equipment_type": "centrifugal pump"})]


@pytest.mark.asyncio
async def test_pending_review_api_list_and_promote(client, monkeypatch) -> None:
    """Graph API exposes pending review list and promotion."""

    monkeypatch.setattr(neo4j_service, "configured", lambda: True)
    monkeypatch.setattr("app.routers.graph._use_neo4j", lambda: True)
    monkeypatch.setattr(
        neo4j_service,
        "list_pending_reviews",
        lambda limit=100: [{"id": "review-1", "entity_type": "equipment", "payload": {"id": "P-909"}}],
    )
    monkeypatch.setattr(
        neo4j_service,
        "promote_pending_review",
        lambda review_id, corrected_fields=None: {"id": review_id, "status": "promoted", "payload": corrected_fields or {}},
    )

    list_response = await client.get("/api/v1/graph/pending-review")
    promote_response = await client.post(
        "/api/v1/graph/pending-review/review-1/promote",
        json={"corrected_fields": {"equipment_type": "pump"}},
    )

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert promote_response.status_code == 200
    assert promote_response.json()["status"] == "promoted"
    assert promote_response.json()["payload"] == {"equipment_type": "pump"}

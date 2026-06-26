"""Equipment graph endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_create_equipment_valid(client) -> None:
    """Valid equipment can be created."""

    response = await client.post(
        "/api/v1/graph/equipment",
        json={
            "tag": "P-202",
            "name": "Crude Transfer Pump",
            "equipment_type": "pump",
            "location": "Pump House A",
            "description": "Test pump",
        },
    )

    assert response.status_code == 200
    assert response.json()["tag"] == "P-202"


@pytest.mark.asyncio
async def test_create_equipment_invalid_tag(client) -> None:
    """Invalid equipment tag is rejected."""

    response = await client.post(
        "/api/v1/graph/equipment",
        json={"tag": "bad-tag", "name": "Bad"},
    )

    assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_get_existing_equipment(client) -> None:
    """Existing equipment can be fetched."""

    await client.post(
        "/api/v1/graph/equipment",
        json={"tag": "V-101", "name": "Tank", "equipment_type": "vessel"},
    )
    response = await client.get("/api/v1/graph/equipment/V-101")

    assert response.status_code == 200
    assert response.json()["tag"] == "V-101"


@pytest.mark.asyncio
async def test_get_nonexistent_equipment(client) -> None:
    """Missing equipment returns 404."""

    response = await client.get("/api/v1/graph/equipment/V-999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_graph_stats(client) -> None:
    """Graph stats include node and edge counts."""

    response = await client.get("/api/v1/graph/stats")

    assert response.status_code == 200
    body = response.json()
    assert "nodes" in body
    assert "edges" in body


@pytest.mark.asyncio
async def test_create_relationship(client) -> None:
    """Relationship can be created between existing nodes."""

    await client.post("/api/v1/graph/equipment", json={"tag": "HE-303", "name": "Exchanger"})
    await client.post("/api/v1/graph/equipment", json={"tag": "C-404", "name": "Column"})
    response = await client.post(
        "/api/v1/graph/relationship",
        json={"source_tag": "HE-303", "target_tag": "C-404", "relationship_type": "feeds_into"},
    )

    assert response.status_code == 200

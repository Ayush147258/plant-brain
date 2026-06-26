"""Compliance endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_seed_rules(client) -> None:
    """Built-in compliance rules can be seeded."""

    response = await client.post("/api/v1/compliance/seed-rules")

    assert response.status_code == 200
    assert "seeded" in response.json()


@pytest.mark.asyncio
async def test_list_rules_after_seed(client) -> None:
    """Rules list is non-empty after seeding."""

    await client.post("/api/v1/compliance/seed-rules")
    response = await client.get("/api/v1/compliance/rules")

    assert response.status_code == 200
    assert response.json()["total"] > 0


@pytest.mark.asyncio
async def test_list_rules_filtered_by_regulation_body(client) -> None:
    """Rules can be filtered by regulation body."""

    await client.post("/api/v1/compliance/seed-rules")
    response = await client.get("/api/v1/compliance/rules?regulation_body=OISD")

    assert response.status_code == 200
    for rule in response.json()["rules"]:
        assert rule["regulation_body"] == "OISD"


@pytest.mark.asyncio
async def test_get_single_rule(client) -> None:
    """A seeded rule can be fetched by rule code."""

    await client.post("/api/v1/compliance/seed-rules")
    response = await client.get("/api/v1/compliance/rules/OISD-116-3.1")

    assert response.status_code == 200
    assert response.json()["rule_code"] == "OISD-116-3.1"

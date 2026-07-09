"""Seed PlantBrain demo data through the running FastAPI API."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import httpx  # type: ignore[reportMissingImports]


BASE_URL = "http://localhost:8000"


async def seed_compliance_rules(client: httpx.AsyncClient) -> None:
    """Seed built-in compliance rules through the API."""

    print("STEP 1: Seeding compliance rules...")
    try:
        response = await client.post("/api/v1/compliance/seed-rules")
        print_result(response)
    except Exception as exc:
        print(f"  Failed to seed compliance rules: {exc}")


async def seed_equipment_graph(client: httpx.AsyncClient) -> None:
    """Seed equipment nodes and relationships through the API."""

    print("STEP 2: Seeding equipment graph...")
    equipment_nodes = [
        {"tag": "V-101", "name": "Crude Oil Storage Tank", "equipment_type": "vessel", "location": "Tank Farm Area"},
        {"tag": "P-201", "name": "Pump P-201", "equipment_type": "pump", "location": "Pump House A"},
        {"tag": "XV-201", "name": "Isolation Valve XV-201", "equipment_type": "valve", "location": "P-201 discharge"},
        {"tag": "M-201", "name": "Motor M-201", "equipment_type": "motor", "location": "Pump House A"},
        {"tag": "PT-201", "name": "Pressure Sensor PT-201", "equipment_type": "instrument", "location": "P-201 discharge"},
        {"tag": "DH-201", "name": "Discharge Header", "equipment_type": "header", "location": "Pump House A"},
        {"tag": "P-202", "name": "Crude Transfer Pump", "equipment_type": "pump", "location": "Pump House A"},
        {"tag": "HE-303", "name": "Feed/Effluent Heat Exchanger", "equipment_type": "heat_exchanger", "location": "Preheat Train"},
        {"tag": "C-404", "name": "Distillation Column", "equipment_type": "vessel", "location": "Process Area 1"},
        {"tag": "V-105", "name": "Reflux Drum", "equipment_type": "vessel", "location": "Process Area 1"},
        {"tag": "P-206", "name": "Reflux Pump", "equipment_type": "pump", "location": "Process Area 1"},
        {"tag": "PRV-307", "name": "Pressure Relief Valve", "equipment_type": "valve", "location": "C-404 Overhead"},
        {"tag": "HE-408", "name": "Overhead Condenser", "equipment_type": "heat_exchanger", "location": "Process Area 1"},
        {"tag": "V-109", "name": "Product Storage Tank", "equipment_type": "vessel", "location": "Tank Farm B"},
        {"tag": "P-210", "name": "Product Transfer Pump", "equipment_type": "pump", "location": "Tank Farm B"},
        {"tag": "FCV-311", "name": "Feed Flow Control Valve", "equipment_type": "valve", "location": "Preheat Train"},
        {"tag": "SDV-412", "name": "Emergency Shutdown Valve", "equipment_type": "valve", "location": "Battery Limit"},
    ]
    relationships = [
        ("P-201", "XV-201", "connected_to"),
        ("P-201", "M-201", "controls"),
        ("P-201", "PT-201", "connected_to"),
        ("P-201", "DH-201", "feeds_into"),
        ("XV-201", "DH-201", "connected_to"),
        ("V-101", "P-202", "feeds_into"),
        ("P-202", "HE-303", "feeds_into"),
        ("HE-303", "C-404", "feeds_into"),
        ("C-404", "V-105", "feeds_into"),
        ("V-105", "P-206", "feeds_into"),
        ("C-404", "PRV-307", "connected_to"),
        ("C-404", "HE-408", "connected_to"),
        ("HE-408", "V-109", "feeds_into"),
        ("V-109", "P-210", "feeds_into"),
        ("FCV-311", "HE-303", "controls"),
        ("SDV-412", "P-202", "controls"),
    ]

    for node in equipment_nodes:
        try:
            response = await client.post("/api/v1/graph/equipment", json={**node, "description": "Demo equipment node"})
            print(f"  Equipment {node['tag']}: {response.status_code}")
        except Exception as exc:
            print(f"  Equipment {node['tag']} failed: {exc}")

    for source, target, relationship_type in relationships:
        try:
            response = await client.post(
                "/api/v1/graph/relationship",
                json={"source_tag": source, "target_tag": target, "relationship_type": relationship_type},
            )
            print(f"  Relationship {source}->{target}: {response.status_code}")
        except Exception as exc:
            print(f"  Relationship {source}->{target} failed: {exc}")


async def seed_inspection_records(client: httpx.AsyncClient) -> None:
    """Seed built-in and additional manual inspection records."""

    print("STEP 3: Seeding inspection records...")
    try:
        response = await client.post("/api/v1/patterns/inspections/seed")
        print_result(response)
    except Exception as exc:
        print(f"  Built-in inspection seeder failed: {exc}")

    manual_records = _manual_inspections()
    for record in manual_records:
        try:
            response = await client.post("/api/v1/patterns/inspections/manual", json=record)
            print(f"  Inspection {record['equipment_tag']}: {response.status_code}")
        except Exception as exc:
            print(f"  Inspection {record['equipment_tag']} failed: {exc}")


async def seed_sample_queries(client: httpx.AsyncClient) -> None:
    """Seed sample user questions through the Q&A endpoint."""

    print("STEP 4: Seeding sample queries...")
    questions = [
        "Which maintenance procedure should I follow for Pump P-201?",
        "Show all equipment connected to Pump P-201 and cite every source.",
        "What are the known issues with pump P-202?",
        "Is the pressure relief valve PRV-307 compliant with OISD inspection requirements?",
        "What equipment is connected to the distillation column C-404?",
    ]
    for question in questions:
        try:
            response = await client.post(
                "/api/v1/query/ask",
                json={"question": question, "top_k": 5, "include_graph_context": True},
                timeout=120,
            )
            print(f"  Query: {response.status_code} - {question}")
        except Exception as exc:
            print(f"  Query failed: {question} ({exc})")


async def print_summary(client: httpx.AsyncClient) -> None:
    """Print final seed summary from API responses."""

    print("STEP 5: Fetching summary...")
    graph_stats = await safe_json(client, "GET", "/api/v1/graph/stats")
    rules = await safe_json(client, "GET", "/api/v1/compliance/rules")
    overdue = await safe_json(client, "GET", "/api/v1/patterns/overdue?threshold_days=1")

    print("=== PlantBrain Demo Data Seeded ===")
    print(f"- Equipment nodes: {graph_stats.get('nodes', 0)}")
    print(f"- Graph edges: {graph_stats.get('edges', 0)}")
    print(f"- Compliance rules: {rules.get('total', 0)}")
    print(f"- Inspection records: {overdue.get('total', 0)}")
    print("- Sample queries stored: 5")
    print("=== Ready for demo! ===")


async def safe_json(client: httpx.AsyncClient, method: str, path: str) -> dict[str, Any]:
    """Return JSON for an API request, or an empty dict on failure."""

    try:
        response = await client.request(method, path)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"  Summary request failed for {path}: {exc}")
        return {}


def print_result(response: httpx.Response) -> None:
    """Print a compact API response result."""

    try:
        body = response.json()
    except ValueError:
        body = response.text
    print(f"  Status {response.status_code}: {body}")


def _manual_inspections() -> list[dict[str, Any]]:
    """Return additional realistic manual inspection records."""

    now = datetime.utcnow()
    records = [
        ("P-202", 5, "Bearing vibration increased to 8.5 mm/s during full-load operation", "major", "R. Mehta"),
        ("P-202", 45, "Horizontal bearing vibration trend rising with audible coupling noise", "major", "R. Mehta"),
        ("P-202", 120, "Pump bearing vibration exceeded alarm limit after seal replacement", "major", "K. Iyer"),
        ("C-404", 200, "Tray damage suspected due to pressure drop instability across middle section", "major", "S. Menon"),
        ("C-404", 300, "Inspection found damaged valve trays and loose downcomer hardware", "major", "S. Menon"),
        ("PRV-307", 45, "Set pressure drifted 7% above design during bench test", "critical", "N. Rao"),
        ("PRV-307", 210, "PRV failed initial pop test and required spring adjustment", "critical", "N. Rao"),
        ("HE-303", 35, "Tube side fouling caused elevated pressure drop across exchanger", "minor", "A. Sharma"),
        ("HE-303", 160, "Fouling deposits observed during cleaning, performance below baseline", "minor", "A. Sharma"),
        ("V-101", 260, "External corrosion found near tank shell bottom course and stair support", "major", "L. Das"),
    ]
    return [
        {
            "equipment_tag": tag,
            "inspection_date": (now - timedelta(days=days_ago)).isoformat(),
            "inspector_name": inspector,
            "inspection_type": "demo_manual",
            "findings": findings,
            "severity": severity,
        }
        for tag, days_ago, findings, severity, inspector in records
    ]


async def main() -> None:
    """Run all demo seeding steps in order."""

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
        await seed_compliance_rules(client)
        await seed_equipment_graph(client)
        await seed_inspection_records(client)
        await seed_sample_queries(client)
        await print_summary(client)


if __name__ == "__main__":
    asyncio.run(main())

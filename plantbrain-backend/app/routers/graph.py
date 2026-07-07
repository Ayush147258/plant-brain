"""Equipment knowledge graph API endpoints for PlantBrain."""

import logging
import re
from datetime import datetime, timedelta
from typing import Any

import networkx as nx
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from app.schemas import EquipmentCreate, EquipmentNode, EquipmentResponse, GraphStatsResponse, RelationshipCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.equipment import Equipment
from app.services.graph_service import graph_service
from app.services.neo4j_service import neo4j_service
from app.security import verify_admin_key


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/graph", tags=["Equipment Graph"])
TAG_PATTERN = re.compile(r"^[A-Z]{1,3}-\d{3,4}[A-Z]?$")
VALID_RELATIONSHIP_TYPES = {"feeds_into", "controls", "bypasses", "connected_to", "part_of"}


_NEO4J_HEALTHY = False
_NEO4J_CHECKED_AT: datetime | None = None


def _use_neo4j() -> bool:
    """Return True only when Neo4j is configured and currently reachable."""

    global _NEO4J_HEALTHY, _NEO4J_CHECKED_AT
    if not neo4j_service.configured():
        return False
    if _NEO4J_CHECKED_AT and datetime.utcnow() - _NEO4J_CHECKED_AT < timedelta(minutes=2):
        return _NEO4J_HEALTHY
    _NEO4J_HEALTHY = neo4j_service.health_check()
    _NEO4J_CHECKED_AT = datetime.utcnow()
    if not _NEO4J_HEALTHY:
        logger.warning("Neo4j is configured but unavailable; using NetworkX graph fallback")
    return _NEO4J_HEALTHY


@router.post(
    "/equipment",
    response_model=EquipmentNode,
    summary="Create or update equipment",
    description="Add an equipment tag to the production Neo4j graph and create or update its SQL record.",
    response_description="Created equipment node",
)
async def create_equipment(
    equipment: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
) -> EquipmentNode:
    """Add equipment to Neo4j when configured, with NetworkX retained as a dev fallback."""

    tag = equipment.tag.strip().upper()
    _validate_tag(tag)

    attributes = {
        "name": equipment.name,
        "equipment_type": equipment.equipment_type,
        "location": equipment.location,
        "description": equipment.description,
    }

    try:
        if _use_neo4j():
            neo4j_service.merge_equipment(tag, attributes)
            node_attributes = (neo4j_service.get_equipment(tag) or {}).get("attributes", {})
            neighbor_count = len((neo4j_service.get_equipment(tag) or {}).get("neighbors", []))
        else:
            graph_service.add_equipment(tag, attributes)
            node_attributes = graph_service.get_equipment(tag) or {}
            neighbor_count = _networkx_neighbor_count(tag)

        result = await db.execute(select(Equipment).where(Equipment.tag == tag))
        existing = result.scalar_one_or_none()
        if existing:
            existing.name = equipment.name
            existing.equipment_type = equipment.equipment_type
            existing.location = equipment.location
            existing.description = equipment.description
            existing.updated_at = datetime.utcnow()
        else:
            db.add(
                Equipment(
                    tag=tag,
                    name=equipment.name,
                    equipment_type=equipment.equipment_type,
                    location=equipment.location,
                    description=equipment.description,
                )
            )

        await db.commit()
        return EquipmentNode(tag=tag, attributes=node_attributes, neighbor_count=neighbor_count)
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to create equipment %s", tag)
        raise HTTPException(status_code=500, detail=f"Failed to create equipment: {exc}") from exc


@router.get(
    "/equipment/{tag}",
    response_model=EquipmentResponse,
    summary="Get equipment details",
    description="Return one equipment graph node with direct neighbors and relationship context.",
    response_description="Equipment node with neighbors",
)
async def get_equipment(
    tag: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return one equipment node with direct neighbors."""

    normalized_tag = tag.strip().upper()
    if _use_neo4j():
        payload = neo4j_service.get_equipment(normalized_tag)
        if payload is None:
            raise HTTPException(status_code=404, detail="Equipment tag not found in graph")
        return payload

    attributes = graph_service.get_equipment(normalized_tag)
    if attributes is None:
        raise HTTPException(status_code=404, detail="Equipment tag not found in graph")

    neighbors = graph_service.get_neighbors(normalized_tag, depth=1)
    return {
        "tag": normalized_tag,
        "attributes": attributes,
        "neighbors": [
            {"tag": neighbor["tag"], "relationship": neighbor["relationship"], "attributes": neighbor["attributes"]}
            for neighbor in neighbors
        ],
    }


@router.get(
    "/equipment",
    summary="List equipment",
    description="List all equipment nodes in the production graph, optionally filtered by equipment type.",
    response_description="Equipment list",
)
async def list_equipment(
    equipment_type: str = "",
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List all equipment nodes, optionally filtered by equipment type."""

    try:
        backend = "neo4j" if _use_neo4j() else "networkx_fallback"
        if backend == "neo4j":
            equipment = neo4j_service.list_equipment(equipment_type)
        else:
            equipment = graph_service.get_all_equipment()
            if equipment_type:
                equipment = [
                    item for item in equipment if str(item.get("equipment_type", "")).lower() == equipment_type.lower()
                ]
        return {"equipment": equipment, "total": len(equipment), "graph_backend": backend}
    except Exception as exc:
        logger.exception("Failed to list graph equipment; returning empty fallback equipment list")
        return {
            "equipment": [],
            "total": 0,
            "graph_backend": "networkx_fallback",
            "warning": f"graph_equipment_unavailable: {exc}",
        }


@router.post(
    "/relationship",
    summary="Create equipment relationship",
    description="Add a directed edge between two equipment tags in the production graph.",
    response_description="Relationship creation confirmation",
)
async def create_relationship(
    relationship: RelationshipCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Add a directed edge between two equipment nodes."""

    source = relationship.source_tag.strip().upper()
    target = relationship.target_tag.strip().upper()
    relationship_type = relationship.relationship_type.strip()

    _validate_relationship_type(relationship_type)
    try:
        if _use_neo4j():
            neo4j_service.merge_relationship(source, target, relationship_type)
        else:
            if graph_service.get_equipment(source) is None:
                raise HTTPException(status_code=400, detail=f"Source equipment tag not found: {source}")
            if graph_service.get_equipment(target) is None:
                raise HTTPException(status_code=400, detail=f"Target equipment tag not found: {target}")
            graph_service.add_relationship(source, target, relationship_type)
        return {"message": "Relationship added", "source": source, "target": target, "type": relationship_type}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create graph relationship")
        raise HTTPException(status_code=500, detail=f"Failed to create relationship: {exc}") from exc


@router.get(
    "/neighbors/{tag}",
    summary="Get graph neighbors",
    description="Return neighboring graph nodes up to depth 3, optionally filtered by relationship type.",
    response_description="Neighbor graph node list",
)
async def get_neighbors(
    tag: str,
    depth: int = Query(default=1, ge=1, le=3),
    relationship_type: str = "",
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return graph neighbors up to a bounded depth."""

    normalized_tag = tag.strip().upper()
    try:
        if _use_neo4j():
            neighbors = neo4j_service.get_neighbors(normalized_tag, depth=depth)
        else:
            if graph_service.get_equipment(normalized_tag) is None:
                raise HTTPException(status_code=404, detail="Equipment tag not found in graph")
            neighbors = graph_service.get_neighbors(normalized_tag, depth=depth)
        if relationship_type:
            neighbors = [neighbor for neighbor in neighbors if neighbor.get("relationship") == relationship_type]
        return neighbors
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get neighbors for %s", normalized_tag)
        raise HTTPException(status_code=500, detail=f"Failed to get neighbors: {exc}") from exc


@router.get(
    "/stats",
    response_model=GraphStatsResponse,
    summary="Get graph statistics",
    description="Return node count, edge count, graph backend, and the most connected equipment.",
    response_description="Equipment graph statistics",
)
async def get_graph_stats(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return graph statistics and most connected equipment."""

    try:
        if _use_neo4j():
            stats = neo4j_service.get_graph_stats()
            return {
                "nodes": int(stats.get("nodes", 0)),
                "edges": int(stats.get("edges", 0)),
                "top_connected": stats.get("top_connected", []),
                "graph_backend": "neo4j",
                "equipment_count": int(stats.get("equipment_count", 0)),
                "valve_count": int(stats.get("valve_count", 0)),
                "instrument_count": int(stats.get("instrument_count", 0)),
                "maintenance_event_count": int(stats.get("maintenance_event_count", 0)),
            }

        stats = graph_service.get_graph_stats()
        degrees = sorted(graph_service.graph.degree(), key=lambda item: item[1], reverse=True)[:10]
        return {
            "nodes": stats["nodes"],
            "edges": stats["edges"],
            "top_connected": [{"tag": tag, "connections": int(connections)} for tag, connections in degrees],
            "graph_backend": "networkx_fallback",
            "equipment_count": stats.get("equipment_count", 0),
        }
    except Exception as exc:
        logger.exception("Failed to get graph stats")
        return _fallback_graph_stats(f"neo4j_unavailable: {exc}")


@router.get(
    "/path/{source_tag}/{target_tag}",
    summary="Find shortest equipment path",
    description="Find the shortest directed path between two equipment tags in the graph.",
    response_description="Shortest path result",
)
async def get_shortest_path(
    source_tag: str,
    target_tag: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Find the shortest directed path between two equipment tags."""

    source = source_tag.strip().upper()
    target = target_tag.strip().upper()
    if _use_neo4j():
        return {"path": [], "message": "Neo4j path endpoint is graph-ready; use /graph/export for visual traversal in the dashboard."}

    if graph_service.get_equipment(source) is None:
        raise HTTPException(status_code=404, detail=f"Source equipment tag not found: {source}")
    if graph_service.get_equipment(target) is None:
        raise HTTPException(status_code=404, detail=f"Target equipment tag not found: {target}")

    try:
        path = nx.shortest_path(graph_service.graph, source=source, target=target)
        return {"path": path, "length": max(len(path) - 1, 0)}
    except nx.NetworkXNoPath:
        return {"path": [], "message": "No path found"}
    except Exception as exc:
        logger.exception("Failed to find path from %s to %s", source, target)
        raise HTTPException(status_code=500, detail=f"Failed to find path: {exc}") from exc


@router.get(
    "/export",
    summary="Export graph JSON",
    description="Export graph nodes and edges as JSON suitable for D3.js, Cytoscape.js, or dashboard visualization.",
    response_description="Graph nodes and edges",
)
async def export_graph(db: AsyncSession = Depends(get_db)) -> dict[str, list[dict]]:
    """Export the graph as JSON for front-end visualization."""

    try:
        if _use_neo4j():
            payload = neo4j_service.export_graph()
            payload["backend"] = "neo4j"  # type: ignore[index]
            return payload  # type: ignore[return-value]

        nodes = [{"id": tag, "tag": tag, "labels": [attributes.get("node_type", "equipment")], "attributes": dict(attributes)} for tag, attributes in graph_service.graph.nodes(data=True)]
        edges = [
            {"source": source, "target": target, "relationship": attributes.get("relationship", "connected_to")}
            for source, target, attributes in graph_service.graph.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges, "backend": "networkx_fallback"}  # type: ignore[return-value]
    except Exception as exc:
        logger.exception("Failed to export graph")
        return _fallback_graph_export(f"neo4j_unavailable: {exc}")  # type: ignore[return-value]


@router.get(
    "/pending-review",
    summary="List pending graph review items",
    description="Return low-confidence extracted entities that were held back from direct graph writes.",
)
async def list_pending_review(limit: int = Query(default=100, ge=1, le=500), _: bool = Depends(verify_admin_key)) -> dict[str, Any]:
    """List pending review items from Neo4j."""

    if not _use_neo4j():
        raise HTTPException(status_code=503, detail="Pending review requires Neo4j configuration")
    try:
        items = neo4j_service.list_pending_reviews(limit=limit)
        return {"items": items, "total": len(items)}
    except Exception as exc:
        logger.exception("Failed to list pending review items")
        raise HTTPException(status_code=500, detail=f"Failed to list pending review items: {exc}") from exc


@router.post(
    "/pending-review/{review_id}/promote",
    summary="Promote a pending review item",
    description="Apply optional human corrections and MERGE the reviewed entity into the real graph.",
)
async def promote_pending_review(review_id: str, body: dict[str, Any] = Body(default={}), _: bool = Depends(verify_admin_key)) -> dict[str, Any]:
    """Promote one pending review item."""

    if not _use_neo4j():
        raise HTTPException(status_code=503, detail="Pending review requires Neo4j configuration")
    try:
        corrected_fields = body.get("corrected_fields") if isinstance(body, dict) else None
        return neo4j_service.promote_pending_review(review_id, corrected_fields or {})
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to promote pending review item %s", review_id)
        raise HTTPException(status_code=500, detail=f"Failed to promote pending review item: {exc}") from exc


@router.post(
    "/pending-review/{review_id}/reject",
    summary="Reject a pending review item",
    description="Archive a pending review item without writing it into the real graph.",
)
async def reject_pending_review(review_id: str, body: dict[str, Any] = Body(default={}), _: bool = Depends(verify_admin_key)) -> dict[str, Any]:
    """Reject one pending review item."""

    if not _use_neo4j():
        raise HTTPException(status_code=503, detail="Pending review requires Neo4j configuration")
    try:
        reason = str(body.get("reason", "")) if isinstance(body, dict) else ""
        return neo4j_service.reject_pending_review(review_id, reason)
    except Exception as exc:
        logger.exception("Failed to reject pending review item %s", review_id)
        raise HTTPException(status_code=500, detail=f"Failed to reject pending review item: {exc}") from exc


def _fallback_graph_stats(reason: str = "") -> dict[str, Any]:
    """Return graph stats from the local fallback graph."""

    stats = graph_service.get_graph_stats()
    degrees = sorted(graph_service.graph.degree(), key=lambda item: item[1], reverse=True)[:10]
    return {
        "nodes": stats["nodes"],
        "edges": stats["edges"],
        "top_connected": [{"tag": tag, "connections": int(connections)} for tag, connections in degrees],
        "graph_backend": "networkx_fallback",
        "equipment_count": stats.get("equipment_count", 0),
        "valve_count": 0,
        "instrument_count": 0,
        "maintenance_event_count": 0,
        "warning": reason,
    }


def _fallback_graph_export(reason: str = "") -> dict[str, Any]:
    """Export graph data from the local fallback graph."""

    nodes = [
        {"id": tag, "tag": tag, "labels": [attributes.get("node_type", "equipment")], "attributes": dict(attributes)}
        for tag, attributes in graph_service.graph.nodes(data=True)
    ]
    edges = [
        {"source": source, "target": target, "relationship": attributes.get("relationship", "connected_to")}
        for source, target, attributes in graph_service.graph.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges, "backend": "networkx_fallback", "warning": reason}

def _validate_tag(tag: str) -> None:
    """Validate an equipment tag."""

    if not TAG_PATTERN.match(tag):
        raise HTTPException(status_code=400, detail="Invalid equipment tag format")


def _validate_relationship_type(relationship_type: str) -> None:
    """Validate a relationship type."""

    if relationship_type not in VALID_RELATIONSHIP_TYPES:
        raise HTTPException(status_code=400, detail="Invalid relationship type")


def _networkx_neighbor_count(tag: str) -> int:
    """Return total directed neighbor count for a tag."""

    graph = graph_service.graph
    if tag not in graph.nodes:
        return 0
    return len(set(graph.successors(tag)) | set(graph.predecessors(tag)))


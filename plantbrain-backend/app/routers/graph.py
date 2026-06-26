"""Equipment knowledge graph API endpoints for PlantBrain."""

import logging
import re
from datetime import datetime
from typing import Any

import networkx as nx
from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas import EquipmentCreate, EquipmentNode, EquipmentResponse, GraphStatsResponse, RelationshipCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.equipment import Equipment
from app.services.graph_service import graph_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/graph", tags=["Equipment Graph"])
TAG_PATTERN = re.compile(r"^[A-Z]{1,3}-\d{3,4}[A-Z]?$")
VALID_RELATIONSHIP_TYPES = {"feeds_into", "controls", "bypasses", "connected_to", "part_of"}



@router.post(
    "/equipment",
    response_model=EquipmentNode,
    summary="Create or update equipment",
    description="Add an equipment tag to the knowledge graph and create or update its SQL record.",
    response_description="Created equipment node",
)
async def create_equipment(
    equipment: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
) -> EquipmentNode:
    """Add equipment to the graph and create or update the SQL record."""

    tag = equipment.tag.strip().upper()
    _validate_tag(tag)

    attributes = {
        "name": equipment.name,
        "equipment_type": equipment.equipment_type,
        "location": equipment.location,
        "description": equipment.description,
    }

    try:
        graph_service.add_equipment(tag, attributes)
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
        node_attributes = graph_service.get_equipment(tag) or {}
        return EquipmentNode(
            tag=tag,
            attributes=node_attributes,
            neighbor_count=_neighbor_count(tag),
        )
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
    attributes = graph_service.get_equipment(normalized_tag)
    if attributes is None:
        raise HTTPException(status_code=404, detail="Equipment tag not found in graph")

    neighbors = graph_service.get_neighbors(normalized_tag, depth=1)
    return {
        "tag": normalized_tag,
        "attributes": attributes,
        "neighbors": [
            {
                "tag": neighbor["tag"],
                "relationship": neighbor["relationship"],
                "attributes": neighbor["attributes"],
            }
            for neighbor in neighbors
        ],
    }


@router.get(
    "/equipment",
    summary="List equipment",
    description="List all equipment nodes in the graph, optionally filtered by equipment type.",
    response_description="Equipment list",
)
async def list_equipment(
    equipment_type: str = "",
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List all equipment nodes, optionally filtered by equipment type."""

    try:
        equipment = graph_service.get_all_equipment()
        if equipment_type:
            equipment = [
                item for item in equipment if str(item.get("equipment_type", "")).lower() == equipment_type.lower()
            ]
        return {"equipment": equipment, "total": len(equipment)}
    except Exception as exc:
        logger.exception("Failed to list graph equipment")
        raise HTTPException(status_code=500, detail=f"Failed to list equipment: {exc}") from exc


@router.post(
    "/relationship",
    summary="Create equipment relationship",
    description="Add a directed relationship between two existing equipment tags in the knowledge graph.",
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
    if graph_service.get_equipment(source) is None:
        raise HTTPException(status_code=400, detail=f"Source equipment tag not found: {source}")
    if graph_service.get_equipment(target) is None:
        raise HTTPException(status_code=400, detail=f"Target equipment tag not found: {target}")

    try:
        graph_service.add_relationship(source, target, relationship_type)
        return {
            "message": "Relationship added",
            "source": source,
            "target": target,
            "type": relationship_type,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create graph relationship")
        raise HTTPException(status_code=500, detail=f"Failed to create relationship: {exc}") from exc


@router.get(
    "/neighbors/{tag}",
    summary="Get graph neighbors",
    description="Return neighboring equipment up to depth 3, optionally filtered by relationship type.",
    response_description="Neighbor equipment list",
)
async def get_neighbors(
    tag: str,
    depth: int = Query(default=1, ge=1, le=3),
    relationship_type: str = "",
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return graph neighbors up to a bounded depth."""

    normalized_tag = tag.strip().upper()
    if graph_service.get_equipment(normalized_tag) is None:
        raise HTTPException(status_code=404, detail="Equipment tag not found in graph")

    try:
        neighbors = graph_service.get_neighbors(normalized_tag, depth=depth)
        if relationship_type:
            neighbors = [neighbor for neighbor in neighbors if neighbor.get("relationship") == relationship_type]
        return neighbors
    except Exception as exc:
        logger.exception("Failed to get neighbors for %s", normalized_tag)
        raise HTTPException(status_code=500, detail=f"Failed to get neighbors: {exc}") from exc


@router.get(
    "/stats",
    response_model=GraphStatsResponse,
    summary="Get graph statistics",
    description="Return node count, edge count, and the most connected equipment for dashboard visualization.",
    response_description="Equipment graph statistics",
)
async def get_graph_stats(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return graph statistics and most connected equipment."""

    try:
        stats = graph_service.get_graph_stats()
        degrees = sorted(graph_service.graph.degree(), key=lambda item: item[1], reverse=True)[:10]
        return {
            "nodes": stats["nodes"],
            "edges": stats["edges"],
            "top_connected": [
                {"tag": tag, "connections": int(connections)} for tag, connections in degrees
            ],
        }
    except Exception as exc:
        logger.exception("Failed to get graph stats")
        raise HTTPException(status_code=500, detail=f"Failed to get graph stats: {exc}") from exc


@router.get(
    "/path/{source_tag}/{target_tag}",
    summary="Find shortest equipment path",
    description="Find the shortest directed path between two equipment tags in the knowledge graph.",
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
    description="Export all graph nodes and edges as JSON suitable for D3.js, Cytoscape.js, or dashboard visualization.",
    response_description="Graph nodes and edges",
)
async def export_graph(db: AsyncSession = Depends(get_db)) -> dict[str, list[dict]]:
    """Export the entire graph as JSON for front-end visualization."""

    try:
        nodes = [
            {"tag": tag, "attributes": dict(attributes)}
            for tag, attributes in graph_service.graph.nodes(data=True)
        ]
        edges = [
            {
                "source": source,
                "target": target,
                "relationship": attributes.get("relationship", "connected_to"),
            }
            for source, target, attributes in graph_service.graph.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}
    except Exception as exc:
        logger.exception("Failed to export graph")
        raise HTTPException(status_code=500, detail=f"Failed to export graph: {exc}") from exc


def _validate_tag(tag: str) -> None:
    """Validate an equipment tag."""

    if not TAG_PATTERN.match(tag):
        raise HTTPException(status_code=400, detail="Invalid equipment tag format")


def _validate_relationship_type(relationship_type: str) -> None:
    """Validate a relationship type."""

    if relationship_type not in VALID_RELATIONSHIP_TYPES:
        raise HTTPException(status_code=400, detail="Invalid relationship type")


def _neighbor_count(tag: str) -> int:
    """Return total directed neighbor count for a tag."""

    graph = graph_service.graph
    if tag not in graph.nodes:
        return 0
    return len(set(graph.successors(tag)) | set(graph.predecessors(tag)))


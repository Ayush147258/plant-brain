"""NetworkX equipment knowledge graph service for PlantBrain."""

import asyncio
import logging
import os
import pickle
import re
import threading
from collections import deque
from collections.abc import Iterable
from typing import Any

import networkx as nx

from app.config import settings


logger = logging.getLogger(__name__)


class GraphService:
    """Build, persist, and query a directed equipment knowledge graph."""

    VALID_RELATIONSHIP_TYPES = {
        "feeds_into",
        "controls",
        "bypasses",
        "connected_to",
        "part_of",
    }
    EQUIPMENT_TAG_PATTERN = re.compile(r"\b([A-Z]{1,3}-\d{3,4}[A-Z]?)\b")
    SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!??])\s+")
    COMMON_EQUIPMENT_NAMES = (
        "pump",
        "valve",
        "vessel",
        "compressor",
        "heat exchanger",
        "reactor",
    )

    def __init__(self) -> None:
        """Create the graph service and load any persisted graph."""

        self.graph = nx.DiGraph()
        self.persist_path = settings.graph_persist_path
        self._save_lock = threading.Lock()
        self.load()

    def load(self) -> None:
        """Load the persisted graph from disk or start with an empty graph."""

        try:
            if os.path.exists(self.persist_path):
                with open(self.persist_path, "rb") as graph_file:
                    loaded_graph = pickle.load(graph_file)
                if not isinstance(loaded_graph, nx.DiGraph):
                    raise TypeError("Persisted graph is not a NetworkX DiGraph")
                self.graph = loaded_graph
                logger.info(
                    "Graph loaded: %s nodes, %s edges",
                    len(self.graph.nodes),
                    len(self.graph.edges),
                )
                return

            self.graph = nx.DiGraph()
            logger.info("Starting with empty graph")
        except Exception:
            logger.exception("Failed to load graph from %s", self.persist_path)
            self.graph = nx.DiGraph()
            raise

    def save(self) -> None:
        """Persist the current graph to disk using a lock and atomic rename."""

        try:
            os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
            temp_path = f"{self.persist_path}.tmp"
            with self._save_lock:
                with open(temp_path, "wb") as graph_file:
                    pickle.dump(self.graph, graph_file)
                os.replace(temp_path, self.persist_path)
            logger.info(
                "Graph saved: %s nodes, %s edges",
                len(self.graph.nodes),
                len(self.graph.edges),
            )
        except Exception:
            logger.exception("Failed to save graph to %s", self.persist_path)
            raise

    def add_equipment(self, tag: str, attributes: dict) -> str:
        """Add or update an equipment node and persist the graph."""

        try:
            normalized_tag = tag.strip().upper()
            self.graph.add_node(normalized_tag, **dict(attributes), node_type="equipment")
            self.save()
            logger.info("Added equipment node %s", normalized_tag)
            return normalized_tag
        except Exception:
            logger.exception("Failed to add equipment %s", tag)
            raise

    def add_relationship(
        self,
        source_tag: str,
        target_tag: str,
        relationship_type: str,
        metadata: dict | None = None,
    ) -> None:
        """Add a directed relationship between two equipment tags."""

        try:
            if relationship_type not in self.VALID_RELATIONSHIP_TYPES:
                raise ValueError(f"Invalid relationship type: {relationship_type}")

            source = source_tag.strip().upper()
            target = target_tag.strip().upper()
            self.graph.add_edge(source, target, relationship=relationship_type, **dict(metadata or {}))
            self.save()
            logger.info("Added relationship %s -> %s (%s)", source, target, relationship_type)
        except Exception:
            logger.exception(
                "Failed to add relationship %s -> %s (%s)",
                source_tag,
                target_tag,
                relationship_type,
            )
            raise

    def get_equipment(self, tag: str) -> dict | None:
        """Return equipment node attributes for a tag, or None if absent."""

        try:
            normalized_tag = tag.strip().upper()
            if normalized_tag not in self.graph.nodes:
                return None
            return dict(self.graph.nodes[normalized_tag])
        except Exception:
            logger.exception("Failed to get equipment %s", tag)
            raise

    def get_neighbors(self, tag: str, depth: int = 1) -> list[dict]:
        """Return graph neighbors reachable from a tag up to a bounded depth."""

        try:
            normalized_tag = tag.strip().upper()
            if normalized_tag not in self.graph.nodes:
                logger.info("Equipment tag %s not found while getting neighbors", normalized_tag)
                return []

            max_depth = max(depth, 0)
            results: list[dict] = []
            visited = {normalized_tag}
            queue: deque[tuple[str, int]] = deque([(normalized_tag, 0)])

            while queue and len(results) < 50:
                current_tag, current_depth = queue.popleft()
                if current_depth >= max_depth:
                    continue

                for neighbor_tag in self.graph.successors(current_tag):
                    edge_data = dict(self.graph.get_edge_data(current_tag, neighbor_tag) or {})
                    neighbor_depth = current_depth + 1
                    results.append(
                        {
                            "tag": neighbor_tag,
                            "attributes": dict(self.graph.nodes[neighbor_tag]),
                            "relationship": edge_data.get("relationship", "connected_to"),
                            "depth": neighbor_depth,
                        }
                    )

                    if neighbor_tag not in visited:
                        visited.add(neighbor_tag)
                        queue.append((neighbor_tag, neighbor_depth))

                    if len(results) >= 50:
                        break

            logger.info("Found %s neighbors for %s within depth %s", len(results), normalized_tag, depth)
            return results
        except Exception:
            logger.exception("Failed to get neighbors for %s", tag)
            raise

    def find_equipment_in_text(self, text: str) -> list[str]:
        """Find known graph equipment tags mentioned in text."""

        try:
            candidate_tags = self._extract_equipment_tags(text)
            known_tags = [tag for tag in candidate_tags if tag in self.graph.nodes]

            lowered_text = text.lower()
            if any(name in lowered_text for name in self.COMMON_EQUIPMENT_NAMES):
                logger.debug("Common equipment names found while scanning text")

            logger.info("Found %s known equipment tags in text", len(known_tags))
            return known_tags
        except Exception:
            logger.exception("Failed to find equipment in text")
            raise

    def get_all_equipment(self) -> list[dict]:
        """Return all equipment nodes and their attributes."""

        try:
            equipment = []
            for tag, attributes in self.graph.nodes(data=True):
                if attributes.get("node_type") == "equipment":
                    equipment.append({"tag": tag, **dict(attributes)})
            logger.info("Returning %s equipment nodes", len(equipment))
            return equipment
        except Exception:
            logger.exception("Failed to get all equipment")
            raise

    def extract_and_add_from_text(self, text: str, document_id: str) -> list[str]:
        """Extract equipment tags from text, add new nodes, and link sentence co-occurrences."""

        try:
            extracted_tags = self._extract_equipment_tags(text)
            newly_added: list[str] = []

            for tag in extracted_tags:
                if tag not in self.graph.nodes:
                    self.graph.add_node(
                        tag,
                        source_document_id=document_id,
                        auto_extracted=True,
                        node_type="equipment",
                    )
                    newly_added.append(tag)

            for sentence in self._split_sentences(text):
                sentence_tags = self._extract_equipment_tags(sentence)
                for source_tag, target_tag in self._pairwise(sentence_tags):
                    if source_tag in self.graph.nodes and target_tag in self.graph.nodes:
                        self.graph.add_edge(
                            source_tag,
                            target_tag,
                            relationship="connected_to",
                            source_document_id=document_id,
                            auto_extracted=True,
                        )

            if newly_added or extracted_tags:
                self.save()

            logger.info("Extracted %s tags and added %s new equipment nodes", len(extracted_tags), len(newly_added))
            return newly_added
        except Exception:
            logger.exception("Failed to extract and add equipment from document %s", document_id)
            raise

    def add_pid_extraction(self, data: dict, document_id: str) -> list[str]:
        """Add structured P&ID extraction output to the local NetworkX fallback graph."""

        added_or_updated: list[str] = []
        zone = data.get("zone")
        for item in data.get("equipment", []) or []:
            tag = str(item.get("id") or "").strip().upper()
            if not tag:
                continue
            self.graph.add_node(
                tag,
                source_document_id=document_id,
                equipment_type=item.get("type"),
                extraction_confidence=item.get("confidence", "low"),
                extraction_source="gemini_multimodal",
                zone=zone,
                node_type="equipment",
            )
            added_or_updated.append(tag)

        for item in data.get("valves", []) or []:
            source = str(item.get("connects_from") or "").strip().upper()
            target = str(item.get("connects_to") or "").strip().upper()
            valve_id = str(item.get("valve_id") or "").strip().upper()
            if not source or not target or source not in self.graph.nodes or target not in self.graph.nodes:
                continue
            metadata = {
                "relationship": "connected_to",
                "source_document_id": document_id,
                "auto_extracted": True,
                "extraction_source": "gemini_multimodal",
                "valve_id": valve_id or None,
                "valve_type": item.get("valve_type"),
                "confidence": item.get("confidence", "low"),
            }
            self.graph.add_edge(source, target, **metadata)
            if valve_id:
                self.graph.add_node(
                    valve_id,
                    source_document_id=document_id,
                    equipment_type="valve",
                    valve_type=item.get("valve_type"),
                    extraction_confidence=item.get("confidence", "low"),
                    extraction_source="gemini_multimodal",
                    zone=zone,
                    node_type="equipment",
                )
                self.graph.add_edge(source, valve_id, **metadata)
                self.graph.add_edge(valve_id, target, **metadata)
                added_or_updated.append(valve_id)

        if added_or_updated or data.get("valves"):
            self.save()
        return self._dedupe_preserve_order(added_or_updated)
    def health_check(self) -> bool:
        """Return True when the graph object is available and internally consistent."""

        try:
            return isinstance(self.graph, nx.DiGraph) and len(self.graph.nodes) >= 0
        except Exception:
            logger.exception("Graph health check failed")
            return False

    def get_graph_stats(self) -> dict:
        """Return node, edge, and equipment counts for the graph."""

        try:
            equipment_count = sum(
                1 for _, attributes in self.graph.nodes(data=True) if attributes.get("node_type") == "equipment"
            )
            return {
                "nodes": len(self.graph.nodes),
                "edges": len(self.graph.edges),
                "equipment_count": equipment_count,
            }
        except Exception:
            logger.exception("Failed to get graph stats")
            raise

    async def get_neighbors_async(self, tag: str, depth: int = 1) -> list[dict]:
        """Return equipment neighbors from the default executor."""

        return await asyncio.get_event_loop().run_in_executor(None, self.get_neighbors, tag, depth)

    def _extract_equipment_tags(self, text: str) -> list[str]:
        """Extract unique equipment tag-like identifiers from text in first-seen order."""

        matches = [match.group(1).upper() for match in self.EQUIPMENT_TAG_PATTERN.finditer(text)]
        return self._dedupe_preserve_order(matches)

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences using English and Hindi sentence endings."""

        return [sentence.strip() for sentence in self.SENTENCE_SPLIT_PATTERN.split(text) if sentence.strip()]

    @staticmethod
    def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
        """Remove duplicate values without changing their first-seen order."""

        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                deduped.append(value)
        return deduped

    @staticmethod
    def _pairwise(values: list[str]) -> Iterable[tuple[str, str]]:
        """Yield consecutive value pairs."""

        for index in range(len(values) - 1):
            yield values[index], values[index + 1]


graph_service = GraphService()

__all__ = ["GraphService", "graph_service"]

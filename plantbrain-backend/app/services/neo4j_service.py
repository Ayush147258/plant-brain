"""Neo4j-first graph service for PlantBrain production deployments."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from uuid import uuid4

from app.config import settings


logger = logging.getLogger(__name__)


class Neo4jService:
    """Store and query the plant knowledge graph in Neo4j using idempotent MERGE writes."""

    EQUIPMENT_TAG_PATTERN = re.compile(r"\b([A-Z]{1,4}-\d{2,5}[A-Z]?)\b", re.IGNORECASE)

    def configured(self) -> bool:
        return bool(settings.neo4j_uri and settings.neo4j_user and settings.neo4j_password)

    def health_check(self) -> bool:
        if not self.configured():
            return False
        GraphDatabase = self._driver_class()
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        try:
            with driver.session() as session:
                session.run("RETURN 1 AS ok").single()
            return True
        except Exception:
            logger.exception("Neo4j health check failed")
            return False
        finally:
            driver.close()

    def merge_equipment(self, tag: str, attributes: dict[str, Any] | None = None) -> dict[str, Any]:
        row = {"id": tag.strip().upper(), **(attributes or {})}
        query = """
        MERGE (e:Equipment {id: $id})
        SET e.name = coalesce($name, e.name),
            e.type = coalesce($equipment_type, $type, e.type),
            e.location = coalesce($location, e.location),
            e.description = coalesce($description, e.description),
            e.source_document_id = coalesce($source_document_id, e.source_document_id),
            e.updated_at = datetime()
        RETURN e
        """
        return self._write_return_node(query, row)

    def merge_relationship(
        self,
        source_tag: str,
        target_tag: str,
        relationship_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        relationship = self._cypher_relationship(relationship_type)
        query = f"""
        MERGE (source:Equipment {{id: $source}})
        MERGE (target:Equipment {{id: $target}})
        MERGE (source)-[r:{relationship}]->(target)
        SET r.source = $source_name,
            r.confidence = coalesce($confidence, r.confidence),
            r.updated_at = datetime()
        """
        self._write(
            query,
            {
                "source": source_tag.strip().upper(),
                "target": target_tag.strip().upper(),
                "source_name": metadata.get("source", "manual") if metadata else "manual",
                "confidence": metadata.get("confidence") if metadata else None,
            },
        )

    def merge_text_equipment(self, tags: list[str], source_document_id: str) -> int:
        rows = [{"id": tag.strip().upper(), "source_document_id": source_document_id} for tag in tags if tag]
        if not rows:
            return 0
        query = """
        UNWIND $rows AS row
        MERGE (e:Equipment {id: row.id})
        SET e.source_document_id = coalesce(e.source_document_id, row.source_document_id),
            e.extraction_source = coalesce(e.extraction_source, 'text_parser'),
            e.updated_at = datetime()
        """
        self._write(query, {"rows": rows})
        return len(rows)

    def merge_pid_extraction(self, data: dict[str, Any], source_document_id: str, document_low_confidence: bool = False) -> dict[str, int]:
        rows = self._pid_rows(data, source_document_id)
        pending_reviews = self._pending_reviews_from_pid_rows(rows, data, document_low_confidence)
        if pending_reviews:
            self._write_pending_reviews(pending_reviews)
        if document_low_confidence:
            rows["equipment"] = []
            rows["valves"] = []
            rows["instruments"] = []
        else:
            rows["equipment"] = [item for item in rows["equipment"] if str(item.get("confidence", "")).lower() != "low"]
            rows["valves"] = [item for item in rows["valves"] if str(item.get("confidence", "")).lower() != "low"]
            rows["instruments"] = [item for item in rows["instruments"] if str(item.get("confidence", "")).lower() != "low"]
        if rows.get("zone"):
            self._write(
                """
                MERGE (z:Zone {name: $zone})
                SET z.source_document_id = $source_document_id,
                    z.updated_at = datetime()
                """,
                {"zone": rows["zone"], "source_document_id": source_document_id},
            )
        if rows["equipment"]:
            self._write(
                """
                UNWIND $equipment AS item
                MERGE (e:Equipment {id: item.id})
                SET e.type = item.type,
                    e.confidence = item.confidence,
                    e.zone = item.zone,
                    e.source_document_id = item.source_document_id,
                    e.extraction_source = 'gemini_multimodal',
                    e.updated_at = datetime()
                FOREACH (_ IN CASE WHEN item.zone IS NULL THEN [] ELSE [1] END |
                  MERGE (z:Zone {name: item.zone})
                  MERGE (z)-[:CONTAINS]->(e)
                )
                """,
                {"equipment": rows["equipment"]},
            )
        if rows["valves"]:
            self._write(
                """
                UNWIND $valves AS valve
                MERGE (v:Valve {id: valve.valve_id})
                SET v.type = valve.valve_type,
                    v.confidence = valve.confidence,
                    v.zone = valve.zone,
                    v.source_document_id = valve.source_document_id,
                    v.extraction_source = 'gemini_multimodal',
                    v.updated_at = datetime()
                FOREACH (_ IN CASE WHEN valve.zone IS NULL THEN [] ELSE [1] END |
                  MERGE (z:Zone {name: valve.zone})
                  MERGE (z)-[:CONTAINS]->(v)
                )
                WITH valve, v
                MATCH (from:Equipment {id: valve.connects_from})
                MATCH (to:Equipment {id: valve.connects_to})
                MERGE (from)-[through:CONNECTED_THROUGH {valve_id: valve.valve_id}]->(to)
                SET through.confidence = valve.confidence,
                    through.source_document_id = valve.source_document_id,
                    through.updated_at = datetime()
                MERGE (from)-[:CONNECTED_TO]->(v)
                MERGE (v)-[:CONNECTED_TO]->(to)
                """,
                {"valves": rows["valves"]},
            )
        if rows["instruments"]:
            self._write(
                """
                UNWIND $instruments AS instrument
                MERGE (i:Instrument {id: instrument.tag})
                SET i.confidence = instrument.confidence,
                    i.zone = instrument.zone,
                    i.source_document_id = instrument.source_document_id,
                    i.extraction_source = 'gemini_multimodal',
                    i.updated_at = datetime()
                FOREACH (_ IN CASE WHEN instrument.zone IS NULL THEN [] ELSE [1] END |
                  MERGE (z:Zone {name: instrument.zone})
                  MERGE (z)-[:CONTAINS]->(i)
                )
                FOREACH (_ IN CASE WHEN size(instrument.attached_to_line_between) = 2 THEN [1] ELSE [] END |
                  MERGE (a:Equipment {id: instrument.attached_to_line_between[0]})
                  MERGE (b:Equipment {id: instrument.attached_to_line_between[1]})
                  MERGE (i)-[:HAS_INSTRUMENT]->(a)
                  MERGE (i)-[:HAS_INSTRUMENT]->(b)
                )
                """,
                {"instruments": rows["instruments"]},
            )
        return {
            "equipment": len(rows["equipment"]),
            "valves": len(rows["valves"]),
            "instruments": len(rows["instruments"]),
            "low_confidence": self.count_low_confidence(data),
            "pending_review": len(pending_reviews),
        }
    def merge_log_extraction(self, data: dict[str, Any], source_document_id: str, document_low_confidence: bool = False) -> dict[str, int]:
        rows = [
            {**entry, "Asset_ID": str(entry.get("Asset_ID") or "").strip().upper(), "source_document_id": source_document_id}
            for entry in data.get("entries", [])
            if entry.get("Asset_ID")
        ]
        pending_reviews = self._pending_reviews_from_log_rows(rows, data, document_low_confidence)
        if pending_reviews:
            self._write_pending_reviews(pending_reviews)
        rows = [] if document_low_confidence else [row for row in rows if str(row.get("confidence", "")).lower() != "low"]
        if not rows:
            return {"maintenance_events": 0, "low_confidence": self.count_low_confidence(data), "pending_review": len(pending_reviews)}
        query = """
        UNWIND $rows AS row
        MATCH (e:Equipment {id: row.Asset_ID})
        MERGE (m:MaintenanceEvent {
            asset_id: row.Asset_ID,
            date: row.Date,
            failure_mode: row.Failure_Mode
        })
        SET m.notes = row.Technician_Notes,
            m.confidence = row.confidence,
            m.source_document_id = row.source_document_id,
            m.updated_at = datetime()
        MERGE (e)-[:HAD_EVENT]->(m)
        """
        self._write(query, {"rows": rows})
        return {"maintenance_events": len(rows), "low_confidence": self.count_low_confidence(data), "pending_review": len(pending_reviews)}

    def merge_compliance_rule(self, rule: dict[str, Any]) -> None:
        """Create or update a compliance rule node and its regulatory/category anchors."""

        query = """
        MERGE (r:ComplianceRule {code: $rule_code})
        SET r.title = $title,
            r.full_text = $full_text,
            r.category = $category,
            r.regulation_body = $regulation_body,
            r.is_active = $is_active,
            r.updated_at = datetime()
        MERGE (body:RegulationBody {name: $regulation_body})
        MERGE (category:ComplianceCategory {name: $category})
        MERGE (body)-[:ISSUES]->(r)
        MERGE (r)-[:APPLIES_TO_CATEGORY]->(category)
        """
        self._write(query, rule)

    def merge_compliance_check(
        self,
        rule: dict[str, Any],
        status: str,
        findings: str,
        document_id: str | None,
        equipment_tags: list[str],
    ) -> None:
        """Link a compliance check result to the rule, document, and mentioned assets."""

        query = """
        MERGE (r:ComplianceRule {code: $rule_code})
        SET r.title = coalesce($title, r.title),
            r.regulation_body = coalesce($regulation_body, r.regulation_body),
            r.category = coalesce($category, r.category)
        MERGE (check:ComplianceCheck {
            rule_code: $rule_code,
            document_id: $document_id,
            checked_at_key: $checked_at_key
        })
        SET check.status = $status,
            check.findings = $findings,
            check.updated_at = datetime()
        MERGE (check)-[:EVALUATES]->(r)
        FOREACH (_ IN CASE WHEN $document_id IS NULL OR $document_id = '' THEN [] ELSE [1] END |
          MERGE (d:Document {id: $document_id})
          MERGE (d)-[:HAS_COMPLIANCE_CHECK]->(check)
        )
        WITH r, check
        UNWIND $equipment_tags AS tag
        MERGE (e:Equipment {id: tag})
        MERGE (e)-[:SUBJECT_TO]->(r)
        MERGE (e)-[:HAS_COMPLIANCE_CHECK]->(check)
        """
        payload = {
            **rule,
            "status": status,
            "findings": findings,
            "document_id": document_id or "",
            "equipment_tags": [tag.strip().upper() for tag in equipment_tags if tag],
            "checked_at_key": f"{rule.get('rule_code')}:{document_id or 'ad_hoc'}:{status}",
        }
        self._write(query, payload)

    def find_equipment_ids_in_text(self, text: str) -> list[str]:
        """Find known graph node ids mentioned in text."""

        candidates = self._dedupe_preserve_order([match.group(1).upper() for match in self.EQUIPMENT_TAG_PATTERN.finditer(text or "")])
        if not candidates or not self.configured():
            return candidates
        query = """
        MATCH (n)
        WHERE n.id IN $ids AND (n:Equipment OR n:Valve OR n:Instrument)
        RETURN n.id AS id
        """
        records = self._read(query, {"ids": candidates})
        known = {record["id"] for record in records}
        return [candidate for candidate in candidates if candidate in known]

    def build_graph_rag_context(self, question: str, depth: int = 2, limit: int = 30) -> dict[str, Any]:
        """Return question-specific Neo4j context for Graph-RAG prompts."""

        tags = self.find_equipment_ids_in_text(question)
        paths: list[dict[str, Any]] = []
        impacted_rules: list[dict[str, Any]] = []
        related_events: list[dict[str, Any]] = []
        if tags:
            path_query = """
            UNWIND $tags AS tag
            MATCH path = (start {id: tag})-[rels*1..3]-(neighbor)
            WHERE length(path) <= $depth
            RETURN [node IN nodes(path) | {id: coalesce(node.id, node.code, node.name), labels: labels(node), properties: properties(node)}] AS nodes,
                   [rel IN relationships(path) | type(rel)] AS relationships
            LIMIT $limit
            """
            records = self._read(path_query, {"tags": tags, "depth": depth, "limit": limit})
            paths = [dict(record) for record in records]

            rule_query = """
            UNWIND $tags AS tag
            MATCH (asset {id: tag})-[*0..2]-(rule:ComplianceRule)
            RETURN DISTINCT rule.code AS code,
                   rule.title AS title,
                   rule.regulation_body AS regulation_body,
                   rule.category AS category
            LIMIT 15
            """
            impacted_rules = [dict(record) for record in self._read(rule_query, {"tags": tags})]

            event_query = """
            UNWIND $tags AS tag
            MATCH (asset {id: tag})-[:HAD_EVENT|HAS_COMPLIANCE_CHECK]-(event)
            RETURN DISTINCT tag AS asset_id, labels(event) AS labels, properties(event) AS event
            LIMIT 20
            """
            related_events = [dict(record) for record in self._read(event_query, {"tags": tags})]

        compliance_rules = self._find_relevant_compliance_rules(question)
        return {
            "graph_backend": "neo4j",
            "seed_tags": tags,
            "paths": paths,
            "compliance_rules": self._dedupe_rule_context([*impacted_rules, *compliance_rules]),
            "events": related_events,
        }

    def format_graph_context(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert Neo4j graph context into LLM-friendly records."""

        items: list[dict[str, Any]] = []
        for path in context.get("paths", [])[:30]:
            nodes = path.get("nodes", [])
            relationships = path.get("relationships", [])
            chain = []
            for index, node in enumerate(nodes):
                chain.append(str(node.get("id") or "unknown"))
                if index < len(relationships):
                    chain.append(f"-[:{relationships[index]}]-")
            items.append({"type": "neo4j_path", "path": " ".join(chain), "nodes": nodes})
        for rule in context.get("compliance_rules", [])[:15]:
            items.append({"type": "compliance_rule", **rule})
        for event in context.get("events", [])[:20]:
            items.append({"type": "event", **event})
        return items
    def get_equipment(self, tag: str) -> dict[str, Any] | None:
        query = """
        MATCH (e:Equipment {id: $id})
        OPTIONAL MATCH (e)-[r]->(n)
        RETURN e, collect({tag: coalesce(n.id, n.name), labels: labels(n), relationship: type(r), attributes: properties(n)}) AS neighbors
        """
        record = self._read_one(query, {"id": tag.strip().upper()})
        if not record:
            return None
        return self._node_payload(record["e"], record.get("neighbors", []))

    def list_equipment(self, equipment_type: str = "") -> list[dict[str, Any]]:
        query = """
        MATCH (e:Equipment)
        WHERE $equipment_type = '' OR toLower(coalesce(e.type, e.equipment_type, '')) = toLower($equipment_type)
        OPTIONAL MATCH (e)--(n)
        RETURN e, count(n) AS neighbor_count
        ORDER BY e.id
        LIMIT 500
        """
        records = self._read(query, {"equipment_type": equipment_type})
        return [self._equipment_list_payload(record["e"], int(record["neighbor_count"] or 0)) for record in records]

    def get_neighbors(self, tag: str, depth: int = 1) -> list[dict[str, Any]]:
        query = """
        MATCH (e {id: $id})-[r*1..3]->(n)
        WHERE length(r) <= $depth
        RETURN n, last(r) AS rel, length(r) AS depth
        LIMIT 100
        """
        records = self._read(query, {"id": tag.strip().upper(), "depth": depth})
        return [
            {
                "tag": dict(record["n"]).get("id") or dict(record["n"]).get("name"),
                "attributes": dict(record["n"]),
                "relationship": record["rel"].type,
                "depth": int(record["depth"]),
            }
            for record in records
        ]

    def get_graph_stats(self) -> dict[str, Any]:
        query = """
        CALL { MATCH (n) RETURN count(n) AS nodes }
        CALL { MATCH ()-[r]->() RETURN count(r) AS edges }
        CALL { MATCH (e:Equipment) RETURN count(e) AS equipment_count }
        CALL { MATCH (v:Valve) RETURN count(v) AS valve_count }
        CALL { MATCH (i:Instrument) RETURN count(i) AS instrument_count }
        CALL { MATCH (m:MaintenanceEvent) RETURN count(m) AS maintenance_event_count }
        CALL {
          MATCH (n)
          OPTIONAL MATCH (n)--(x)
          WITH n, count(x) AS degree
          ORDER BY degree DESC
          LIMIT 10
          RETURN collect({tag: coalesce(n.id, n.name), labels: labels(n), connections: degree}) AS top_connected
        }
        RETURN nodes, edges, equipment_count, valve_count, instrument_count, maintenance_event_count, top_connected
        """
        record = self._read_one(query, {})
        if not record:
            return {"nodes": 0, "edges": 0, "equipment_count": 0, "top_connected": []}
        return dict(record)

    def export_graph(self, limit: int = 500) -> dict[str, list[dict[str, Any]]]:
        query = """
        MATCH (n)
        WITH n LIMIT $limit
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN collect(DISTINCT {id: coalesce(n.id, n.name), labels: labels(n), attributes: properties(n)}) AS nodes,
               collect(DISTINCT {source: coalesce(n.id, n.name), target: coalesce(m.id, m.name), relationship: type(r), attributes: properties(r)}) AS edges
        """
        record = self._read_one(query, {"limit": limit})
        if not record:
            return {"nodes": [], "edges": []}
        edges = [edge for edge in record["edges"] if edge.get("source") and edge.get("target") and edge.get("relationship")]
        return {"nodes": record["nodes"], "edges": edges}

    def count_low_confidence(self, data: dict[str, Any]) -> int:
        objects = []
        for key in ("equipment", "valves", "instruments", "entries"):
            objects.extend(data.get(key, []) or [])
        return sum(1 for item in objects if str(item.get("confidence", "")).lower() == "low") + len(data.get("confidence_flags", []) or [])

    def list_pending_reviews(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return pending low-confidence graph writes awaiting human review."""

        query = """
        MATCH (p:PendingReview)
        WHERE coalesce(p.status, 'pending') = 'pending'
        RETURN p
        ORDER BY p.created_at DESC
        LIMIT $limit
        """
        return [self._pending_review_payload(record["p"]) for record in self._read(query, {"limit": limit})]

    def promote_pending_review(self, review_id: str, corrected_fields: dict[str, Any] | None = None) -> dict[str, Any]:
        """Promote one PendingReview item into the real graph, applying optional corrections."""

        review = self._get_pending_review(review_id)
        if review is None:
            raise ValueError(f"PendingReview not found: {review_id}")
        payload = json.loads(review.get("payload_json") or "{}")
        payload.update(corrected_fields or {})
        entity_type = str(review.get("entity_type") or payload.get("entity_type") or "")

        if entity_type == "equipment":
            self.merge_equipment(str(payload.get("id") or payload.get("tag") or ""), payload)
        elif entity_type == "valve":
            self._write(
                """
                MERGE (v:Valve {id: $valve_id})
                SET v.type = $valve_type,
                    v.confidence = coalesce($confidence, 'reviewed'),
                    v.zone = $zone,
                    v.source_document_id = $source_document_id,
                    v.reviewed = true,
                    v.updated_at = datetime()
                WITH v
                OPTIONAL MATCH (from:Equipment {id: $connects_from})
                OPTIONAL MATCH (to:Equipment {id: $connects_to})
                FOREACH (_ IN CASE WHEN from IS NULL OR to IS NULL THEN [] ELSE [1] END |
                  MERGE (from)-[:CONNECTED_THROUGH {valve_id: $valve_id}]->(to)
                  MERGE (from)-[:CONNECTED_TO]->(v)
                  MERGE (v)-[:CONNECTED_TO]->(to)
                )
                """,
                payload,
            )
        elif entity_type == "instrument":
            self._write(
                """
                MERGE (i:Instrument {id: $tag})
                SET i.confidence = coalesce($confidence, 'reviewed'),
                    i.zone = $zone,
                    i.source_document_id = $source_document_id,
                    i.reviewed = true,
                    i.updated_at = datetime()
                """,
                payload,
            )
        elif entity_type == "maintenance_event":
            self._write(
                """
                MERGE (e:Equipment {id: $Asset_ID})
                MERGE (m:MaintenanceEvent {
                    asset_id: $Asset_ID,
                    date: $Date,
                    failure_mode: $Failure_Mode
                })
                SET m.notes = $Technician_Notes,
                    m.confidence = coalesce($confidence, 'reviewed'),
                    m.source_document_id = $source_document_id,
                    m.reviewed = true,
                    m.updated_at = datetime()
                MERGE (e)-[:HAD_EVENT]->(m)
                """,
                payload,
            )
        else:
            raise ValueError(f"Unsupported PendingReview entity type: {entity_type}")

        self._archive_pending_review(review_id, "promoted", corrected_fields or {})
        return {"id": review_id, "status": "promoted", "entity_type": entity_type, "payload": payload}

    def reject_pending_review(self, review_id: str, reason: str = "") -> dict[str, Any]:
        """Archive a PendingReview item without promoting it."""

        self._archive_pending_review(review_id, "rejected", {"reject_reason": reason})
        return {"id": review_id, "status": "rejected", "reason": reason}

    def _get_pending_review(self, review_id: str) -> dict[str, Any] | None:
        record = self._read_one(
            """
            MATCH (p:PendingReview {id: $id})
            WHERE coalesce(p.status, 'pending') = 'pending'
            RETURN p
            """,
            {"id": review_id},
        )
        return dict(record["p"]) if record else None

    def _archive_pending_review(self, review_id: str, status: str, fields: dict[str, Any]) -> None:
        self._write(
            """
            MATCH (p:PendingReview {id: $id})
            SET p.status = $status,
                p.archive_fields_json = $fields_json,
                p.archived_at = datetime()
            """,
            {"id": review_id, "status": status, "fields_json": json.dumps(fields, sort_keys=True)},
        )

    def _write_pending_reviews(self, rows: list[dict[str, Any]]) -> None:
        query = """
        UNWIND $rows AS row
        MERGE (p:PendingReview {id: row.id})
        SET p.entity_type = row.entity_type,
            p.source_document_id = row.source_document_id,
            p.payload_json = row.payload_json,
            p.reason = row.reason,
            p.confidence = row.confidence,
            p.status = 'pending',
            p.updated_at = datetime(),
            p.created_at = coalesce(p.created_at, datetime())
        """
        self._write(query, {"rows": rows})

    def _pending_reviews_from_pid_rows(self, rows: dict[str, Any], data: dict[str, Any], document_low_confidence: bool) -> list[dict[str, Any]]:
        pending: list[dict[str, Any]] = []
        for entity_type, key, items in (
            ("equipment", "id", rows.get("equipment", [])),
            ("valve", "valve_id", rows.get("valves", [])),
            ("instrument", "tag", rows.get("instruments", [])),
        ):
            for item in items:
                if document_low_confidence or str(item.get("confidence", "")).lower() == "low":
                    pending.append(self._pending_review_row(entity_type, item.get(key), item, document_low_confidence))
        for flag in data.get("confidence_flags", []) or []:
            pending.append(self._pending_review_row("confidence_flag", str(uuid4()), {"flag": flag, "source_document_id": rows.get("source_document_id")}, document_low_confidence))
        return pending

    def _pending_reviews_from_log_rows(self, rows: list[dict[str, Any]], data: dict[str, Any], document_low_confidence: bool) -> list[dict[str, Any]]:
        pending = [
            self._pending_review_row("maintenance_event", row.get("Asset_ID"), row, document_low_confidence)
            for row in rows
            if document_low_confidence or str(row.get("confidence", "")).lower() == "low"
        ]
        for flag in data.get("confidence_flags", []) or []:
            source_document_id = rows[0].get("source_document_id") if rows else ""
            pending.append(self._pending_review_row("confidence_flag", str(uuid4()), {"flag": flag, "source_document_id": source_document_id}, document_low_confidence))
        return pending

    @staticmethod
    def _pending_review_row(entity_type: str, entity_id: Any, payload: dict[str, Any], document_low_confidence: bool) -> dict[str, Any]:
        source_document_id = str(payload.get("source_document_id") or "")
        review_id = f"{source_document_id}:{entity_type}:{entity_id or uuid4()}"
        reason = "document_low_confidence" if document_low_confidence else "low_confidence_extraction"
        return {
            "id": review_id,
            "entity_type": entity_type,
            "source_document_id": source_document_id,
            "payload_json": json.dumps(payload, sort_keys=True),
            "reason": reason,
            "confidence": payload.get("confidence", "low"),
        }

    @staticmethod
    def _pending_review_payload(node: Any) -> dict[str, Any]:
        attrs = dict(node)
        payload_json = attrs.get("payload_json") or "{}"
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            payload = {}
        return {"id": attrs.get("id"), "entity_type": attrs.get("entity_type"), "reason": attrs.get("reason"), "confidence": attrs.get("confidence"), "payload": payload}
    def _find_relevant_compliance_rules(self, question: str) -> list[dict[str, Any]]:
        terms = [term.upper() for term in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", question or "")]
        bodies = [term for term in terms if term in {"OISD", "PESO", "FACTORY_ACT", "FACTORY"}]
        if not terms:
            return []
        query = """
        MATCH (rule:ComplianceRule)
        WHERE any(term IN $terms WHERE
            toUpper(coalesce(rule.code, '')) CONTAINS term OR
            toUpper(coalesce(rule.title, '')) CONTAINS term OR
            toUpper(coalesce(rule.category, '')) CONTAINS term OR
            toUpper(coalesce(rule.regulation_body, '')) CONTAINS term OR
            toUpper(coalesce(rule.full_text, '')) CONTAINS term
        ) OR rule.regulation_body IN $bodies
        RETURN DISTINCT rule.code AS code,
               rule.title AS title,
               rule.regulation_body AS regulation_body,
               rule.category AS category
        LIMIT 15
        """
        return [dict(record) for record in self._read(query, {"terms": terms, "bodies": bodies})]

    @staticmethod
    def _dedupe_rule_context(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for rule in rules:
            code = str(rule.get("code") or "")
            if code and code not in seen:
                seen.add(code)
                deduped.append(rule)
        return deduped

    @staticmethod
    def _dedupe_preserve_order(values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                deduped.append(value)
        return deduped
    @staticmethod
    def _pid_rows(data: dict[str, Any], source_document_id: str) -> dict[str, Any]:
        zone = data.get("zone")
        equipment = [
            {
                "id": str(item.get("id") or "").strip().upper(),
                "type": item.get("type"),
                "confidence": item.get("confidence", "low"),
                "zone": zone,
                "source_document_id": source_document_id,
            }
            for item in data.get("equipment", [])
            if item.get("id")
        ]
        valves = [
            {
                "valve_id": str(item.get("valve_id") or "").strip().upper(),
                "valve_type": item.get("valve_type"),
                "connects_from": str(item.get("connects_from") or "").strip().upper(),
                "connects_to": str(item.get("connects_to") or "").strip().upper(),
                "confidence": item.get("confidence", "low"),
                "zone": zone,
                "source_document_id": source_document_id,
            }
            for item in data.get("valves", [])
            if item.get("valve_id") and item.get("connects_from") and item.get("connects_to")
        ]
        instruments = [
            {
                "tag": str(item.get("tag") or "").strip().upper(),
                "attached_to_line_between": [str(tag).strip().upper() for tag in item.get("attached_to_line_between", []) if tag],
                "confidence": item.get("confidence", "low"),
                "zone": zone,
                "source_document_id": source_document_id,
            }
            for item in data.get("instruments", [])
            if item.get("tag")
        ]
        return {
            "zone": zone,
            "source_document_id": source_document_id,
            "equipment": equipment,
            "valves": valves,
            "instruments": instruments,
        }

    def _read(self, query: str, parameters: dict[str, Any]) -> list[Any]:
        GraphDatabase = self._driver_class()
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        try:
            with driver.session() as session:
                return list(session.run(query, parameters))
        finally:
            driver.close()

    def _read_one(self, query: str, parameters: dict[str, Any]) -> Any | None:
        rows = self._read(query, parameters)
        return rows[0] if rows else None

    def _write(self, query: str, parameters: dict[str, Any]) -> None:
        GraphDatabase = self._driver_class()
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        try:
            with driver.session() as session:
                session.execute_write(lambda tx: tx.run(query, parameters).consume())
        finally:
            driver.close()

    def _write_return_node(self, query: str, parameters: dict[str, Any]) -> dict[str, Any]:
        record = self._read_one(query, parameters)
        node = record["e"] if record else None
        return dict(node) if node else {}

    @staticmethod
    def _node_payload(node: Any, neighbors: list[dict[str, Any]]) -> dict[str, Any]:
        attrs = dict(node)
        return {"tag": attrs.get("id"), "attributes": attrs, "neighbors": [item for item in neighbors if item.get("tag")]}

    @staticmethod
    def _equipment_list_payload(node: Any, neighbor_count: int) -> dict[str, Any]:
        attrs = dict(node)
        return {
            "tag": attrs.get("id"),
            "name": attrs.get("name"),
            "equipment_type": attrs.get("type") or attrs.get("equipment_type"),
            "location": attrs.get("location"),
            "attributes": attrs,
            "neighbor_count": neighbor_count,
        }

    @staticmethod
    def _cypher_relationship(relationship_type: str) -> str:
        allowed = {
            "feeds_into": "FEEDS_INTO",
            "controls": "CONTROLS",
            "bypasses": "BYPASSES",
            "connected_to": "CONNECTED_TO",
            "part_of": "PART_OF",
        }
        return allowed.get(relationship_type, "CONNECTED_TO")

    @staticmethod
    def _driver_class():
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise RuntimeError("Install the neo4j package to enable Neo4j graph loading") from exc
        return GraphDatabase


neo4j_service = Neo4jService()

__all__ = ["Neo4jService", "neo4j_service"]

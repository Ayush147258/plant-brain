"""Knowledge decay scoring and trust-gate summaries for PlantBrain answers."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


class KnowledgeDecayService:
    """Compute source freshness, knowledge decay, and answer trust gates."""

    REVIEW_INTERVALS = {
        "standard": 365,
        "procedure": 730,
        "drawing": 365,
        "maintenance_log": 365,
        "manual": 1095,
        "document": 730,
    }

    DATE_PATTERNS = (
        re.compile(
            r"(?:last\s+reviewed|reviewed|review\s+date|last\s+validated|validated|revision\s+date|rev(?:ision)?(?:\s+date)?)"
            r"[^\n\r]{0,32}?"
            r"(?P<date>\b\d{4}-\d{1,2}-\d{1,2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}\b|\b20\d{2}\b)",
            re.IGNORECASE,
        ),
        re.compile(r"\b(?:revision|rev\.?|review)\s*(?P<date>20\d{2})\b", re.IGNORECASE),
    )

    DATE_FORMATS = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%b %Y",
        "%B %Y",
        "%Y",
    )

    def build_trust_summary(
        self,
        question: str,
        retrieved_chunks: list[dict[str, Any]],
        graph_context: list[dict[str, Any]] | None = None,
        equipment_tags: list[str] | None = None,
        documents_by_id: dict[str, Any] | None = None,
        answer_confidence: str | float | int | None = "Medium",
    ) -> dict[str, Any]:
        """Return a deterministic freshness and trust summary for an answer."""

        documents = self._build_document_rows(retrieved_chunks, documents_by_id or {})
        if not documents:
            documents = [self._unknown_document_row()]

        freshness_score = min(int(doc["freshness_score"]) for doc in documents)
        knowledge_decay = max(0, min(100, 100 - freshness_score))
        freshness = self._freshness_label(freshness_score)
        confidence = self._confidence_percent(answer_confidence, bool(retrieved_chunks))
        graph_assets = self._count_graph_assets(graph_context or [], equipment_tags or [])
        risk = self._risk_level(freshness_score, confidence, bool(retrieved_chunks))
        trust_gate = self._trust_gate(risk)
        flags = self._confidence_flags(documents, risk, bool(retrieved_chunks))

        return {
            "engine": "Knowledge Decay Engine",
            "knowledge_decay": knowledge_decay,
            "freshness_score": freshness_score,
            "freshness": freshness,
            "confidence": confidence,
            "risk": risk,
            "sources": len(retrieved_chunks),
            "source_documents": len(documents),
            "graph_assets": graph_assets,
            "trust_gate": trust_gate,
            "recommendation": self._recommendation(risk),
            "reason": self._summary_reason(documents, risk),
            "documents": documents,
            "confidence_flags": flags,
            "pipeline": [
                "Metadata Extraction",
                "Review Date",
                "Revision Comparison",
                "Standards Mapping",
                "Graph Cross-check",
                "Decay Score",
                "Trust Gate",
                "Final Answer",
            ],
            "question_scope": question[:240],
        }

    def render_trust_summary(self, summary: dict[str, Any]) -> str:
        """Render the summary as plain text that is visible in every answer."""

        lines = [
            "Trust Summary",
            f"Knowledge Decay: {summary.get('knowledge_decay', 100)}%",
            f"Freshness: {summary.get('freshness', 'Unknown')}",
            f"Confidence: {summary.get('confidence', 0)}%",
            f"Risk: {summary.get('risk', 'Unknown')}",
            f"Sources: {summary.get('sources', 0)}",
            f"Graph Assets: {summary.get('graph_assets', 0)}",
            f"Trust Gate: {summary.get('trust_gate', 'Review required')}",
        ]
        reason = str(summary.get("reason") or "")
        if reason:
            lines.extend(["", "Reason:", reason])

        documents = summary.get("documents") or []
        if documents:
            lines.extend(["", "Freshness Evidence:"])
            for doc in documents[:4]:
                reviewed = doc.get("last_reviewed") or "unknown review date"
                lines.append(
                    f"- {doc.get('filename', 'Unknown')}: {doc.get('freshness_score', 0)}% fresh, "
                    f"last reviewed {reviewed}, risk {doc.get('risk_level', 'Unknown')}"
                )

        recommendation = str(summary.get("recommendation") or "")
        if recommendation:
            lines.extend(["", "Recommendation:", recommendation])
        return "\n".join(lines)

    def decorate_answer(self, answer: str, summary: dict[str, Any]) -> str:
        """Prepend the trust summary unless the answer already starts with one."""

        clean_answer = (answer or "").strip()
        if clean_answer[:300].lower().startswith("trust summary"):
            return clean_answer
        rendered = self.render_trust_summary(summary)
        if not clean_answer:
            return rendered
        return f"{rendered}\n\nAnswer\n{clean_answer}"

    def format_for_prompt(self, summary: dict[str, Any] | None) -> str:
        """Return concise trust-gate context for the LLM prompt."""

        if not summary:
            return "No knowledge decay summary was computed. Treat the answer as requiring review."
        return (
            f"Knowledge Decay={summary.get('knowledge_decay')}%; "
            f"Freshness={summary.get('freshness')}; "
            f"Risk={summary.get('risk')}; "
            f"Trust Gate={summary.get('trust_gate')}; "
            f"Recommendation={summary.get('recommendation')}"
        )

    def _build_document_rows(self, retrieved_chunks: list[dict[str, Any]], documents_by_id: dict[str, Any]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for chunk in retrieved_chunks:
            metadata = chunk.get("metadata", {}) or {}
            doc_id = str(metadata.get("document_id") or metadata.get("doc_id") or metadata.get("filename") or "unknown")
            row = grouped.setdefault(
                doc_id,
                {
                    "document_id": doc_id,
                    "filename": str(metadata.get("filename") or metadata.get("doc_name") or "Unknown"),
                    "snippets": [],
                    "metadata": metadata,
                    "distance": chunk.get("distance"),
                },
            )
            row["snippets"].append(str(chunk.get("text") or ""))

        rows = []
        for doc_id, row in grouped.items():
            doc = documents_by_id.get(doc_id)
            rows.append(self._score_document(row, doc))
        return rows

    def _score_document(self, row: dict[str, Any], doc: Any | None) -> dict[str, Any]:
        filename = str(getattr(doc, "original_filename", None) or row.get("filename") or "Unknown")
        text = "\n".join(row.get("snippets") or [])
        metadata = row.get("metadata") or {}
        doc_type = self._classify_document(filename, text)
        interval = self.REVIEW_INTERVALS.get(doc_type, self.REVIEW_INTERVALS["document"])
        review_date, date_source = self._find_review_date(metadata, text, doc)

        if review_date is None:
            score = 50
            age_days = None
            reason = "No explicit review date found; route source for metadata cleanup."
        else:
            age_days = max(0, (datetime.utcnow() - review_date).days)
            score = max(0, min(100, round(100 - ((age_days / interval) * 100))))
            if score >= 85:
                reason = "Document is within expected review interval."
            elif score >= 60:
                reason = "Document is aging and should be reviewed soon."
            else:
                reason = "Document has exceeded or is near the expected review interval."
            if date_source == "upload_or_processed_date":
                reason = "No explicit review metadata found; using upload/processing date as fallback freshness evidence."

        risk = self._doc_risk(score)
        last_reviewed = review_date.date().isoformat() if review_date else None
        return {
            "document_id": row.get("document_id"),
            "filename": filename,
            "document_type": doc_type,
            "last_reviewed": last_reviewed,
            "review_date_source": date_source,
            "document_age_days": age_days,
            "expected_review_interval_days": interval,
            "freshness_score": score,
            "knowledge_decay": max(0, min(100, 100 - score)),
            "freshness_status": self._freshness_label(score),
            "risk_level": risk,
            "reason": reason,
        }

    def _find_review_date(self, metadata: dict[str, Any], text: str, doc: Any | None) -> tuple[datetime | None, str]:
        for key in ("last_reviewed", "review_date", "revision_date", "last_validated", "validated_at"):
            parsed = self._parse_date(metadata.get(key))
            if parsed:
                return parsed, key

        for pattern in self.DATE_PATTERNS:
            match = pattern.search(text or "")
            if match:
                parsed = self._parse_date(match.group("date"))
                if parsed:
                    return parsed, "content"

        for attr in ("processed_at", "uploaded_at"):
            parsed = self._parse_date(getattr(doc, attr, None)) if doc is not None else None
            if parsed:
                return parsed, "upload_or_processed_date"
        return None, "missing"

    def _parse_date(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        raw = str(value).strip()
        if not raw:
            return None
        normalized = raw.replace(",", "")
        if re.fullmatch(r"\d{2}/\d{2}/\d{2}", normalized):
            normalized = normalized[:-2] + "20" + normalized[-2:]
        for fmt in self.DATE_FORMATS:
            try:
                parsed = datetime.strptime(normalized, fmt)
                if fmt == "%Y":
                    return parsed.replace(month=1, day=1)
                if fmt in {"%b %Y", "%B %Y"}:
                    return parsed.replace(day=1)
                return parsed
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(normalized).replace(tzinfo=None)
        except ValueError:
            return None

    @staticmethod
    def _classify_document(filename: str, text: str) -> str:
        combined = f"{filename} {text[:1000]}".lower()
        if "oisd" in combined or "peso" in combined or "standard" in combined:
            return "standard"
        if "p&id" in combined or "pid" in combined or "drawing" in combined or "blueprint" in combined:
            return "drawing"
        if "log" in combined or "shift" in combined:
            return "maintenance_log"
        if "manual" in combined or "oem" in combined:
            return "manual"
        if "procedure" in combined or "sop" in combined or "maintenance" in combined:
            return "procedure"
        return "document"

    @staticmethod
    def _confidence_percent(value: str | float | int | None, has_sources: bool) -> int:
        if isinstance(value, int | float):
            percent = int(round(value * 100 if value <= 1 else value))
        else:
            lowered = str(value or "").lower()
            if "high" in lowered:
                percent = 96
            elif "low" in lowered:
                percent = 45
            else:
                percent = 72
        if not has_sources:
            percent = min(percent, 35)
        return max(0, min(100, percent))

    @staticmethod
    def _count_graph_assets(graph_context: list[dict[str, Any]], equipment_tags: list[str]) -> int:
        assets = {str(tag).upper() for tag in equipment_tags if tag}
        for item in graph_context:
            tag = item.get("tag") or item.get("source") or item.get("target")
            if tag:
                assets.add(str(tag).upper())
        return len(assets)

    @staticmethod
    def _freshness_label(score: int) -> str:
        if score >= 85:
            return "High"
        if score >= 60:
            return "Moderate Risk"
        if score >= 40:
            return "High Risk"
        return "Expired"

    @staticmethod
    def _doc_risk(score: int) -> str:
        if score >= 85:
            return "Low"
        if score >= 60:
            return "Moderate"
        if score >= 40:
            return "High"
        return "Critical"

    def _risk_level(self, freshness_score: int, confidence: int, has_sources: bool) -> str:
        if not has_sources:
            return "Critical"
        if freshness_score < 40 or confidence < 50:
            return "Critical"
        if freshness_score < 60 or confidence < 70:
            return "High"
        if freshness_score < 85:
            return "Moderate"
        return "Low"

    @staticmethod
    def _trust_gate(risk: str) -> str:
        if risk == "Low":
            return "ALLOW_WITH_CITATIONS"
        if risk == "Moderate":
            return "VERIFY_BEFORE_EXECUTION"
        if risk == "High":
            return "ENGINEERING_REVIEW_REQUIRED"
        return "BLOCK_FIELD_EXECUTION_UNTIL_CURRENT_SOURCE_CONFIRMED"

    @staticmethod
    def _recommendation(risk: str) -> str:
        if risk == "Low":
            return "Use the cited answer, keeping normal plant approval workflow."
        if risk == "Moderate":
            return "Prefer fresher cited sources and verify revision status before execution."
        if risk == "High":
            return "Verify the latest approved engineering revision before field action."
        return "Do not execute from this answer alone; obtain a current approved procedure or engineer sign-off."

    @staticmethod
    def _summary_reason(documents: list[dict[str, Any]], risk: str) -> str:
        worst = min(documents, key=lambda item: int(item.get("freshness_score", 0)))
        filename = worst.get("filename", "Unknown source")
        score = worst.get("freshness_score", 0)
        if risk in {"High", "Critical"}:
            return f"{filename} is the limiting source with freshness {score}%; trust gate requires review before execution."
        return f"Freshness gate passed using {len(documents)} source document(s); limiting source is {filename} at {score}%."

    @staticmethod
    def _confidence_flags(documents: list[dict[str, Any]], risk: str, has_sources: bool) -> list[str]:
        flags: list[str] = []
        if not has_sources:
            flags.append("No retrieved source chunks; answer must not be used operationally.")
        for doc in documents:
            if doc.get("review_date_source") == "missing":
                flags.append(f"{doc.get('filename', 'Unknown source')} has no explicit review date metadata.")
            if int(doc.get("freshness_score", 0)) < 60:
                flags.append(f"{doc.get('filename', 'Unknown source')} is stale or expired.")
        if risk in {"High", "Critical"}:
            flags.append("Trust gate escalated because one or more sources are stale, missing, or low confidence.")
        return list(dict.fromkeys(flags))[:8]

    @staticmethod
    def _unknown_document_row() -> dict[str, Any]:
        return {
            "document_id": "unknown",
            "filename": "No retrieved source",
            "document_type": "document",
            "last_reviewed": None,
            "review_date_source": "missing",
            "document_age_days": None,
            "expected_review_interval_days": 730,
            "freshness_score": 0,
            "knowledge_decay": 100,
            "freshness_status": "Expired",
            "risk_level": "Critical",
            "reason": "No source was retrieved, so freshness cannot be proven.",
        }


knowledge_decay_service = KnowledgeDecayService()

__all__ = ["KnowledgeDecayService", "knowledge_decay_service"]

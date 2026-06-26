"""Failure pattern analysis service for PlantBrain inspection data."""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.equipment import Equipment
from app.models.inspection import Inspection


logger = logging.getLogger(__name__)


class PatternService:
    """Analyze inspection records to surface reliability and safety risk patterns."""

    FAILURE_SEVERITIES = ("major", "critical")

    async def detect_failure_clusters(self, db: AsyncSession, min_occurrences: int = 2) -> list[dict]:
        """Detect repeated major or critical failures by equipment tag."""

        try:
            records = await self._load_failure_records(db)
            if not records:
                return []

            loop = asyncio.get_event_loop()
            cluster_inputs = await loop.run_in_executor(None, self._compute_failure_cluster_inputs, records, min_occurrences)
            clusters: list[dict] = []

            for cluster in cluster_inputs:
                ai_summary = await self._summarize_pattern(cluster.pop("records"))
                cluster["ai_summary"] = ai_summary
                clusters.append(cluster)

            clusters.sort(key=lambda item: item["risk_score"], reverse=True)
            return clusters
        except Exception:
            logger.exception("Failed to detect failure clusters")
            return []

    async def detect_overdue_inspections(
        self,
        db: AsyncSession,
        overdue_threshold_days: int = 180,
    ) -> list[dict]:
        """Detect equipment whose latest inspection is older than the threshold."""

        try:
            inspections_result = await db.execute(select(Inspection))
            inspections = inspections_result.scalars().all()
            if not inspections:
                return []

            equipment_result = await db.execute(select(Equipment))
            equipment_lookup = {equipment.tag: equipment for equipment in equipment_result.scalars().all()}

            records = [self._inspection_to_record(inspection) for inspection in inspections]
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._compute_overdue_inspections,
                records,
                equipment_lookup,
                overdue_threshold_days,
            )
        except Exception:
            logger.exception("Failed to detect overdue inspections")
            return []

    async def detect_cooccurrence_patterns(self, db: AsyncSession, window_days: int = 30) -> list[dict]:
        """Detect equipment pairs with major or critical failures close in time."""

        try:
            records = await self._load_failure_records(db)
            if not records:
                return []

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._compute_cooccurrence_patterns, records, window_days)
        except Exception:
            logger.exception("Failed to detect cooccurrence patterns")
            return []

    async def get_risk_summary(self, db: AsyncSession) -> dict:
        """Combine all pattern detections into a high-level risk summary."""

        try:
            failure_clusters = await self.detect_failure_clusters(db)
            overdue_inspections = await self.detect_overdue_inspections(db)
            cooccurrence_patterns = await self.detect_cooccurrence_patterns(db)

            critical_overdue = [item for item in overdue_inspections if item["risk_level"] == "high"]
            overall_risk_level = self._overall_risk_level(failure_clusters, overdue_inspections, critical_overdue)

            return {
                "failure_clusters": failure_clusters[:5],
                "overdue_inspections_count": len(overdue_inspections),
                "critical_overdue": critical_overdue,
                "cooccurrence_patterns": cooccurrence_patterns[:3],
                "overall_risk_level": overall_risk_level,
            }
        except Exception:
            logger.exception("Failed to build risk summary")
            return {
                "failure_clusters": [],
                "overdue_inspections_count": 0,
                "critical_overdue": [],
                "cooccurrence_patterns": [],
                "overall_risk_level": "Low",
            }

    async def _load_failure_records(self, db: AsyncSession) -> list[dict]:
        """Load major and critical inspection records into dictionaries."""

        result = await db.execute(
            select(Inspection).where(Inspection.severity.in_(self.FAILURE_SEVERITIES))
        )
        return [self._inspection_to_record(inspection) for inspection in result.scalars().all()]

    @staticmethod
    def _inspection_to_record(inspection: Inspection) -> dict[str, Any]:
        """Convert an Inspection ORM object to a plain analysis record."""

        inspection_date = inspection.inspection_date or inspection.created_at
        return {
            "equipment_tag": inspection.equipment_tag,
            "inspection_date": inspection_date,
            "severity": inspection.severity,
            "findings": inspection.findings,
        }

    @staticmethod
    def _compute_failure_cluster_inputs(records: list[dict], min_occurrences: int) -> list[dict]:
        """Build failure cluster metrics using pandas."""

        df = pd.DataFrame(records, columns=["equipment_tag", "inspection_date", "severity", "findings"])
        if df.empty:
            return []

        df["inspection_date"] = pd.to_datetime(df["inspection_date"])
        clusters: list[dict] = []
        counts = df.groupby("equipment_tag").size()
        clustered_tags = counts[counts >= min_occurrences].index.tolist()

        for tag in clustered_tags:
            tag_df = df[df["equipment_tag"] == tag].sort_values("inspection_date")
            first_seen = tag_df["inspection_date"].min()
            last_seen = tag_df["inspection_date"].max()
            occurrence_count = int(len(tag_df))
            months_span = max((last_seen - first_seen).days / 30.0, 1.0)
            severity_distribution = {
                "major": int((tag_df["severity"] == "major").sum()),
                "critical": int((tag_df["severity"] == "critical").sum()),
            }
            severity_weight = severity_distribution["major"] + (severity_distribution["critical"] * 2)
            risk_score = (occurrence_count * severity_weight) / months_span

            clusters.append(
                {
                    "equipment_tag": tag,
                    "occurrence_count": occurrence_count,
                    "severity_distribution": severity_distribution,
                    "first_seen": first_seen.isoformat(),
                    "last_seen": last_seen.isoformat(),
                    "frequency_per_month": round(occurrence_count / months_span, 2),
                    "risk_score": round(float(risk_score), 2),
                    "records": tag_df.to_dict(orient="records"),
                }
            )

        return clusters

    @staticmethod
    def _compute_overdue_inspections(
        records: list[dict],
        equipment_lookup: dict[str, Equipment],
        overdue_threshold_days: int,
    ) -> list[dict]:
        """Compute overdue inspection records using pandas."""

        df = pd.DataFrame(records, columns=["equipment_tag", "inspection_date", "severity", "findings"])
        if df.empty:
            return []

        df["inspection_date"] = pd.to_datetime(df["inspection_date"])
        today = pd.Timestamp(datetime.utcnow())
        latest_by_tag = df.groupby("equipment_tag")["inspection_date"].max()
        overdue: list[dict] = []

        for tag, last_inspection_date in latest_by_tag.items():
            days_since = int((today - last_inspection_date).days)
            if days_since <= overdue_threshold_days:
                continue

            equipment = equipment_lookup.get(tag)
            overdue.append(
                {
                    "equipment_tag": tag,
                    "equipment_name": equipment.name if equipment else "",
                    "equipment_type": equipment.equipment_type if equipment else "",
                    "last_inspection_date": last_inspection_date.isoformat(),
                    "days_since_last_inspection": days_since,
                    "overdue_by_days": days_since - overdue_threshold_days,
                    "risk_level": "high" if days_since > 365 else "medium",
                }
            )

        overdue.sort(key=lambda item: item["days_since_last_inspection"], reverse=True)
        return overdue

    @staticmethod
    def _compute_cooccurrence_patterns(records: list[dict], window_days: int) -> list[dict]:
        """Compute failure co-occurrence patterns using pandas."""

        df = pd.DataFrame(records, columns=["equipment_tag", "inspection_date", "severity", "findings"])
        if df.empty:
            return []

        df["inspection_date"] = pd.to_datetime(df["inspection_date"])
        df = df.sort_values("inspection_date").reset_index(drop=True)
        pairs: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"count": 0, "gaps": [], "last": None})

        for left_index, left_row in df.iterrows():
            for right_index in range(left_index + 1, len(df)):
                right_row = df.iloc[right_index]
                gap_days = abs((right_row["inspection_date"] - left_row["inspection_date"]).days)
                if gap_days > window_days:
                    break
                if left_row["equipment_tag"] == right_row["equipment_tag"]:
                    continue

                pair = tuple(sorted([left_row["equipment_tag"], right_row["equipment_tag"]]))
                pairs[pair]["count"] += 1
                pairs[pair]["gaps"].append(gap_days)
                pairs[pair]["last"] = max(left_row["inspection_date"], right_row["inspection_date"])

        patterns = []
        for pair, data in pairs.items():
            patterns.append(
                {
                    "equipment_pair": list(pair),
                    "co_occurrence_count": int(data["count"]),
                    "typical_gap_days": round(float(sum(data["gaps"]) / len(data["gaps"])), 2),
                    "last_occurrence": data["last"].isoformat() if data["last"] is not None else "",
                }
            )

        patterns.sort(key=lambda item: item["co_occurrence_count"], reverse=True)
        return patterns[:10]

    async def _summarize_pattern(self, records: list[dict]) -> str:
        """Summarize failure records using the LLM service without module-level service imports."""

        from app.services.llm_service import llm_service

        return await llm_service.summarize_pattern(records)

    @staticmethod
    def _overall_risk_level(
        failure_clusters: list[dict],
        overdue_inspections: list[dict],
        critical_overdue: list[dict],
    ) -> str:
        """Compute the overall risk level from detected patterns."""

        has_high_risk_cluster = any(cluster.get("risk_score", 0) > 10 for cluster in failure_clusters)
        has_overdue_365 = any(item["days_since_last_inspection"] > 365 for item in overdue_inspections)
        has_overdue_180 = any(item["days_since_last_inspection"] > 180 for item in overdue_inspections)

        if critical_overdue and has_high_risk_cluster:
            return "Critical"
        if has_overdue_365:
            return "High"
        if has_overdue_180:
            return "Medium"
        return "Low"


pattern_service = PatternService()

__all__ = ["PatternService", "pattern_service"]

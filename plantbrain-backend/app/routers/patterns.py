"""Failure pattern and risk detection API endpoints for PlantBrain."""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas import FailureCluster, ManualInspectionCreate, OverdueInspection, RiskSummaryResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.inspection import Inspection
from app.services.pattern_service import pattern_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/patterns", tags=["Pattern Detection"])



@router.get(
    "/clusters",
    summary="Detect failure clusters",
    description="Analyze major and critical inspection records to find recurring failures by equipment tag.",
    response_description="Failure clusters with AI summaries",
)
async def get_failure_clusters(
    min_occurrences: int = Query(default=2, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run repeated failure cluster detection."""

    try:
        clusters = await pattern_service.detect_failure_clusters(db, min_occurrences)
        limited_clusters = clusters[:limit]
        return {
            "clusters": [FailureCluster(**cluster) for cluster in limited_clusters],
            "total": len(clusters),
            "generated_at": datetime.utcnow().isoformat(),
            "analysis_note": "AI summaries generated for each cluster",
        }
    except Exception as exc:
        logger.exception("Failed to get failure clusters")
        raise HTTPException(status_code=500, detail=f"Failed to get failure clusters: {exc}") from exc


@router.get(
    "/overdue",
    summary="Detect overdue inspections",
    description="Find equipment with inspection dates older than the threshold and classify inspection risk.",
    response_description="Overdue inspection list",
)
async def get_overdue_inspections(
    threshold_days: int = Query(default=180, ge=1),
    risk_level: str = "",
    equipment_type: str = "",
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run overdue inspection detection."""

    try:
        overdue = await pattern_service.detect_overdue_inspections(db, threshold_days)
        if risk_level:
            overdue = [item for item in overdue if item.get("risk_level") == risk_level]
        if equipment_type:
            overdue = [item for item in overdue if item.get("equipment_type") == equipment_type]

        return {
            "overdue_inspections": [OverdueInspection(**item) for item in overdue],
            "total": len(overdue),
            "threshold_days": threshold_days,
        }
    except Exception as exc:
        logger.exception("Failed to get overdue inspections")
        raise HTTPException(status_code=500, detail=f"Failed to get overdue inspections: {exc}") from exc


@router.get(
    "/cooccurrence",
    summary="Detect co-occurring failures",
    description="Find pairs of equipment with major or critical failures occurring within a configurable time window.",
    response_description="Co-occurrence patterns",
)
async def get_cooccurrence_patterns(
    window_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run co-occurrence pattern detection."""

    try:
        patterns = await pattern_service.detect_cooccurrence_patterns(db, window_days)
        return {"patterns": patterns, "window_days": window_days, "total": len(patterns)}
    except Exception as exc:
        logger.exception("Failed to get cooccurrence patterns")
        raise HTTPException(status_code=500, detail=f"Failed to get cooccurrence patterns: {exc}") from exc


@router.get(
    "/risk-summary",
    response_model=RiskSummaryResponse,
    summary="Get risk dashboard summary",
    description="Return combined failure clusters, overdue inspections, co-occurrence patterns, and overall risk level.",
    response_description="Combined risk summary",
)
async def get_risk_summary(db: AsyncSession = Depends(get_db)) -> dict:
    """Return combined dashboard risk summary."""

    try:
        summary = await pattern_service.get_risk_summary(db)
        summary["generated_at"] = datetime.utcnow().isoformat()
        return summary
    except Exception as exc:
        logger.exception("Failed to get risk summary")
        raise HTTPException(status_code=500, detail=f"Failed to get risk summary: {exc}") from exc


@router.get(
    "/failure-intelligence",
    summary="Get lessons learned failure intelligence",
    description=(
        "Analyze inspection history, near-miss language, QMS review gaps, and recurring "
        "failure clusters to produce proactive operational warnings."
    ),
    response_description="Lessons-learned warnings, systemic patterns, QMS signals, and validation metrics",
)
async def get_failure_intelligence(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return proactive lessons-learned warnings for the demo risk dashboard."""

    try:
        intelligence = await pattern_service.get_failure_intelligence(db)
        intelligence["generated_at"] = datetime.utcnow().isoformat()
        return intelligence
    except Exception as exc:
        logger.exception("Failed to get failure intelligence")
        raise HTTPException(status_code=500, detail=f"Failed to get failure intelligence: {exc}") from exc

@router.post(
    "/inspections/seed",
    summary="Seed demo inspections",
    description="Create sample inspection records across demo equipment tags for hackathon testing.",
    response_description="Seeded inspection count",
)
async def seed_inspections(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Seed sample inspection records for demo and testing."""

    try:
        records = _sample_inspections()
        for record in records:
            db.add(Inspection(**record))
        await db.commit()
        equipment_tags = sorted({record["equipment_tag"] for record in records})
        logger.info("Seeded %s sample inspection records", len(records))
        return {"seeded": len(records), "equipment_tags": equipment_tags}
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to seed inspection records")
        raise HTTPException(status_code=500, detail=f"Failed to seed inspections: {exc}") from exc


@router.post(
    "/inspections/manual",
    summary="Create manual inspection",
    description="Add one inspection record manually from a dashboard form or typed technician note.",
    response_description="Created inspection record",
)
async def create_manual_inspection(
    inspection_request: ManualInspectionCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Manually add one inspection record."""

    try:
        inspection = Inspection(
            equipment_tag=inspection_request.equipment_tag.strip().upper(),
            inspection_date=inspection_request.inspection_date,
            inspector_name=inspection_request.inspector_name,
            inspection_type=inspection_request.inspection_type,
            findings=inspection_request.findings,
            severity=inspection_request.severity.lower(),
        )
        db.add(inspection)
        await db.commit()
        await db.refresh(inspection)
        logger.info("Created manual inspection %s for %s", inspection.id, inspection.equipment_tag)
        return _inspection_to_dict(inspection)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to create manual inspection")
        raise HTTPException(status_code=500, detail=f"Failed to create inspection: {exc}") from exc


def _inspection_to_dict(inspection: Inspection) -> dict[str, Any]:
    """Convert an Inspection ORM object into a response dictionary."""

    return {
        "id": inspection.id,
        "equipment_tag": inspection.equipment_tag,
        "inspection_date": inspection.inspection_date,
        "inspector_name": inspection.inspector_name,
        "inspection_type": inspection.inspection_type,
        "findings": inspection.findings,
        "severity": inspection.severity,
        "created_at": inspection.created_at,
    }


def _sample_inspections() -> list[dict[str, Any]]:
    """Return realistic sample inspections across demo equipment tags."""

    now = datetime.utcnow()
    samples = [
        ("P-201", 420, "corrective", "Mechanical seal leakage found after startup; maintenance note references Rev 2021 procedure after 2024 pump modification", "major", "K. Iyer"),
        ("P-201", 260, "near_miss", "Lockout tagout isolation near miss: connected valve XV-201 did not fully seat during drain-down", "critical", "M. Khan"),
        ("P-201", 35, "followup", "P-201 seal plan flush line cleaned and PT-201 alarm verified after corrective work", "ok", "K. Iyer"),
        ("V-101", 520, "statutory", "Corrosion found on shell side nozzle with localized pitting near weld seam", "major", "A. Sharma"),
        ("V-101", 410, "routine", "PRV set pressure drifted 5% above design during bench check", "critical", "N. Rao"),
        ("V-101", 95, "followup", "Nozzle corrosion repair verified and coating touch-up completed", "minor", "A. Sharma"),
        ("P-202", 500, "routine", "Bearing temperature high during loaded trial and vibration trend increasing", "major", "K. Iyer"),
        ("P-202", 300, "corrective", "Mechanical seal leakage found at pump casing drain area", "major", "M. Khan"),
        ("P-202", 45, "routine", "Pump alignment checked and found within acceptable tolerance", "ok", "K. Iyer"),
        ("HE-303", 470, "routine", "Tube side fouling observed with reduced heat transfer performance", "minor", "R. Patel"),
        ("HE-303", 260, "corrective", "Gasket leak found on channel cover after pressure test", "major", "S. Menon"),
        ("HE-303", 60, "routine", "Cleaning completed and exchanger pressure drop returned to normal", "ok", "R. Patel"),
        ("C-404", 530, "routine", "Compressor lube oil pressure fluctuation found during startup checks", "critical", "D. Singh"),
        ("C-404", 360, "corrective", "Interstage vibration high and coupling guard rubbing marks observed", "major", "D. Singh"),
        ("C-404", 120, "routine", "Compressor anti-surge valve stroke check completed successfully", "ok", "P. Nair"),
        ("V-105", 480, "statutory", "Internal lining blistering found near bottom dish drain area", "major", "L. Das"),
        ("V-105", 275, "routine", "Level transmitter impulse line choking found during functional check", "minor", "L. Das"),
        ("V-105", 30, "followup", "Lining repair inspected and holiday test accepted", "ok", "A. Sharma"),
    ]

    return [
        {
            "equipment_tag": tag,
            "inspection_date": now - timedelta(days=days_ago),
            "inspector_name": inspector,
            "inspection_type": inspection_type,
            "findings": findings,
            "severity": severity,
        }
        for tag, days_ago, inspection_type, findings, severity, inspector in samples
    ]


"""Compliance monitoring API endpoints for PlantBrain."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas import ComplianceCheckRequest, ComplianceCheckResult, ComplianceRuleCreate
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.compliance import ComplianceCheck, ComplianceRule
from app.models.document import Document
from app.services.llm_service import llm_service
from app.services.vector_store import vector_store


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/compliance", tags=["Compliance"])



@router.post(
    "/rules",
    status_code=status.HTTP_201_CREATED,
    summary="Create a compliance rule",
    description="Create an OISD, PESO, or Factory Act compliance rule for later procedure checks.",
    response_description="Created compliance rule",
)
async def create_rule(
    rule: ComplianceRuleCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new compliance rule."""

    rule_code = rule.rule_code.strip()
    existing = await _get_rule_by_code(rule_code, db)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Compliance rule already exists")

    try:
        compliance_rule = ComplianceRule(
            rule_code=rule_code,
            regulation_body=rule.regulation_body,
            title=rule.title,
            full_text=rule.full_text,
            category=rule.category,
            is_active=True,
        )
        db.add(compliance_rule)
        await db.commit()
        await db.refresh(compliance_rule)
        logger.info("Created compliance rule %s", rule_code)
        return _rule_to_dict(compliance_rule)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to create compliance rule %s", rule_code)
        raise HTTPException(status_code=500, detail=f"Failed to create compliance rule: {exc}") from exc


@router.get(
    "/rules",
    summary="List compliance rules",
    description="List active compliance rules with optional regulation body and category filters.",
    response_description="Compliance rule list",
)
async def list_rules(
    regulation_body: str = "",
    category: str = "",
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List active compliance rules with optional filters."""

    try:
        filters = [ComplianceRule.is_active.is_(True)]
        if regulation_body:
            filters.append(ComplianceRule.regulation_body == regulation_body)
        if category:
            filters.append(ComplianceRule.category == category)

        count_query = select(func.count()).select_from(ComplianceRule).where(*filters)
        rules_query = select(ComplianceRule).where(*filters).order_by(ComplianceRule.rule_code).offset(skip).limit(limit)
        total_result = await db.execute(count_query)
        rules_result = await db.execute(rules_query)
        rules = rules_result.scalars().all()
        return {
            "rules": [_rule_to_dict(rule) for rule in rules],
            "total": int(total_result.scalar_one()),
        }
    except Exception as exc:
        logger.exception("Failed to list compliance rules")
        raise HTTPException(status_code=500, detail=f"Failed to list rules: {exc}") from exc


@router.get(
    "/rules/{rule_code}",
    summary="Get a compliance rule",
    description="Return one compliance rule by rule code, including full rule text.",
    response_description="Compliance rule details",
)
async def get_rule(rule_code: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return a single compliance rule by rule code."""

    rule = await _get_rule_by_code(rule_code, db)
    if rule is None:
        raise HTTPException(status_code=404, detail="Compliance rule not found")
    return _rule_to_dict(rule)


@router.delete(
    "/rules/{rule_code}",
    summary="Deactivate a compliance rule",
    description="Soft delete a compliance rule by marking it inactive while preserving historical checks.",
    response_description="Deletion confirmation",
)
async def delete_rule(rule_code: str, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Soft delete a compliance rule by marking it inactive."""

    rule = await _get_rule_by_code(rule_code, db)
    if rule is None:
        raise HTTPException(status_code=404, detail="Compliance rule not found")

    try:
        rule.is_active = False
        await db.commit()
        logger.info("Soft deleted compliance rule %s", rule_code)
        return {"message": "Compliance rule deleted"}
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to delete compliance rule %s", rule_code)
        raise HTTPException(status_code=500, detail=f"Failed to delete rule: {exc}") from exc


@router.post(
    "/check",
    summary="Run compliance check",
    description="Check procedure text or an uploaded document against selected active compliance rules using Gemini.",
    response_description="Compliance check results",
)
async def check_compliance(
    request: ComplianceCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Check a document or direct procedure text against compliance rules."""

    try:
        procedure_text = request.procedure_text.strip()
        if not procedure_text:
            if not request.document_id:
                raise HTTPException(status_code=400, detail="document_id is required when procedure_text is empty")
            document = await db.get(Document, request.document_id)
            if document is None:
                raise HTTPException(status_code=404, detail="Document not found")
            chunks = await vector_store.search(
                "procedure compliance safety operating requirements",
                top_k=10,
                filter_document_id=request.document_id,
            )
            procedure_text = "\n\n".join(chunk.get("text", "") for chunk in chunks)
            if not procedure_text.strip():
                raise HTTPException(status_code=400, detail="No document text available for compliance check")

        rules = await _get_rules_for_check(request.rule_codes, db)
        skipped_count = max(len(rules) - 10, 0)
        rules_to_process = rules[:10]
        results: list[ComplianceCheckResult] = []

        for rule in rules_to_process:
            llm_result = await llm_service.check_compliance(
                procedure_text,
                rule.full_text or "",
                rule.rule_code,
            )
            findings = llm_result.get("findings", "")
            recommendation = llm_result.get("recommendation", "")
            db.add(
                ComplianceCheck(
                    rule_id=rule.id,
                    document_id=request.document_id or None,
                    status=llm_result.get("status", "INSUFFICIENT_INFORMATION"),
                    findings=f"{findings}\n\nRECOMMENDATION: {recommendation}".strip(),
                )
            )
            results.append(
                ComplianceCheckResult(
                    rule_code=rule.rule_code,
                    rule_title=rule.title or "",
                    status=llm_result.get("status", "INSUFFICIENT_INFORMATION"),
                    findings=findings,
                    recommendation=recommendation,
                )
            )

        await db.commit()
        response: dict[str, Any] = {"results": results}
        if skipped_count:
            response["message"] = f"Processed first 10 rules; skipped {skipped_count} remaining rules."
        return response
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to run compliance check")
        raise HTTPException(status_code=500, detail=f"Failed to run compliance check: {exc}") from exc


@router.get(
    "/checks/document/{document_id}",
    summary="List document compliance checks",
    description="Return all compliance checks previously run for a document plus a status summary.",
    response_description="Compliance checks for the document",
)
async def get_document_checks(document_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return all compliance checks ever run for a document."""

    try:
        query = (
            select(ComplianceCheck, ComplianceRule)
            .join(ComplianceRule, ComplianceCheck.rule_id == ComplianceRule.id)
            .where(ComplianceCheck.document_id == document_id)
            .order_by(ComplianceCheck.checked_at.desc())
        )
        result = await db.execute(query)
        rows = result.all()

        checks = [
            {
                "rule_code": rule.rule_code,
                "status": check.status,
                "findings": check.findings,
                "checked_at": check.checked_at,
            }
            for check, rule in rows
        ]
        summary = {
            "compliant": sum(1 for item in checks if item["status"] == "COMPLIANT"),
            "non_compliant": sum(1 for item in checks if item["status"] == "NON_COMPLIANT"),
            "partial": sum(1 for item in checks if item["status"] == "PARTIAL"),
        }
        return {"document_id": document_id, "checks": checks, "summary": summary}
    except Exception as exc:
        logger.exception("Failed to get compliance checks for document %s", document_id)
        raise HTTPException(status_code=500, detail=f"Failed to get document checks: {exc}") from exc


@router.post(
    "/seed-rules",
    summary="Seed built-in rules",
    description="Seed the database with built-in OISD, PESO, and Factory Act demo compliance rules.",
    response_description="Number of rules seeded",
)
async def seed_rules(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    """Seed built-in OISD, PESO, and Factory Act compliance rules."""

    seeded_count = 0
    try:
        for rule_data in _built_in_rules():
            existing = await _get_rule_by_code(rule_data["rule_code"], db)
            if existing is not None:
                continue
            db.add(ComplianceRule(**rule_data, is_active=True))
            seeded_count += 1

        await db.commit()
        logger.info("Seeded %s built-in compliance rules", seeded_count)
        return {"seeded": seeded_count}
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to seed compliance rules")
        raise HTTPException(status_code=500, detail=f"Failed to seed rules: {exc}") from exc


async def _get_rule_by_code(rule_code: str, db: AsyncSession) -> ComplianceRule | None:
    """Fetch a compliance rule by code."""

    result = await db.execute(select(ComplianceRule).where(ComplianceRule.rule_code == rule_code.strip()))
    return result.scalar_one_or_none()


async def _get_rules_for_check(rule_codes: list[str], db: AsyncSession) -> list[ComplianceRule]:
    """Return specific active rules or all active rules for a compliance check."""

    if rule_codes:
        normalized_codes = [code.strip() for code in rule_codes if code.strip()]
        result = await db.execute(
            select(ComplianceRule).where(
                ComplianceRule.is_active.is_(True),
                ComplianceRule.rule_code.in_(normalized_codes),
            )
        )
    else:
        result = await db.execute(
            select(ComplianceRule).where(ComplianceRule.is_active.is_(True)).order_by(ComplianceRule.rule_code)
        )

    rules = list(result.scalars().all())
    if not rules:
        raise HTTPException(status_code=404, detail="No active compliance rules found")
    return rules


def _rule_to_dict(rule: ComplianceRule) -> dict[str, Any]:
    """Convert a ComplianceRule ORM object into a response dictionary."""

    return {
        "id": rule.id,
        "rule_code": rule.rule_code,
        "regulation_body": rule.regulation_body,
        "title": rule.title,
        "full_text": rule.full_text,
        "category": rule.category,
        "is_active": rule.is_active,
        "created_at": rule.created_at,
    }


def _built_in_rules() -> list[dict[str, str]]:
    """Return built-in compliance rules for initial seeding."""

    return [
        {
            "rule_code": "OISD-116-3.1",
            "regulation_body": "OISD",
            "title": "Fire & Gas detection systems must be installed in all process areas",
            "full_text": "All hydrocarbon process areas must have suitable fire and gas detection coverage based on credible leak and fire scenarios. Detectors should be maintained, calibrated, and connected to alarms or shutdown actions appropriate to the hazard.",
            "category": "fire_safety",
        },
        {
            "rule_code": "OISD-116-3.2",
            "regulation_body": "OISD",
            "title": "Pressure relief valves must be tested every 2 years",
            "full_text": "Pressure relief valves protecting process equipment must be inspected and tested at intervals not exceeding two years unless a stricter internal standard applies. Records should include set pressure, test date, corrective action, and next due date.",
            "category": "pressure_vessel",
        },
        {
            "rule_code": "OISD-118-4.1",
            "regulation_body": "OISD",
            "title": "Earthing and bonding for flammable liquid storage",
            "full_text": "Flammable liquid storage tanks and transfer systems must be effectively earthed and bonded to prevent static accumulation. Continuity and earth resistance checks should be documented at defined maintenance intervals.",
            "category": "electrical",
        },
        {
            "rule_code": "PESO-2016-5.3",
            "regulation_body": "PESO",
            "title": "Safe distance between storage tanks",
            "full_text": "Storage tanks for petroleum or flammable substances must maintain minimum separation distances according to capacity, product class, and installation layout. Site drawings and tank registers should demonstrate that spacing requirements are met.",
            "category": "fire_safety",
        },
        {
            "rule_code": "PESO-2016-6.1",
            "regulation_body": "PESO",
            "title": "Static electricity grounding for tanker loading",
            "full_text": "Tanker loading and unloading operations must include static grounding or bonding before product transfer begins. Procedures should verify grounding connection, prohibit transfer if grounding fails, and document operator checks.",
            "category": "electrical",
        },
        {
            "rule_code": "Factory_Act-41B",
            "regulation_body": "Factory_Act",
            "title": "Hazardous process safety committee requirements",
            "full_text": "Factories carrying out hazardous processes must maintain safety management arrangements including worker participation and periodic safety review. The site should document committee meetings, hazard communication, emergency planning, and corrective action tracking.",
            "category": "general",
        },
        {
            "rule_code": "OISD-144-2.1",
            "regulation_body": "OISD",
            "title": "Preventive maintenance schedule for rotating equipment",
            "full_text": "Rotating equipment such as pumps, compressors, and turbines should be covered by a preventive maintenance schedule based on criticality and service conditions. Maintenance records should capture inspections, vibration checks, lubrication, defects, and actions taken.",
            "category": "general",
        },
        {
            "rule_code": "OISD-150-3.3",
            "regulation_body": "OISD",
            "title": "Hot work permit system",
            "full_text": "Hot work in operating or hazardous areas must be controlled through a written permit system with gas testing, isolation, fire watch, and area preparation requirements. Permits should specify validity, precautions, authorizations, and closeout checks.",
            "category": "fire_safety",
        },
        {
            "rule_code": "OISD-116-7.2",
            "regulation_body": "OISD",
            "title": "Emergency shutdown system testing frequency",
            "full_text": "Emergency shutdown systems must be periodically tested to confirm sensors, logic, final elements, and alarms operate as intended. Test frequency and bypass controls should be documented, approved, and reviewed after failures or modifications.",
            "category": "general",
        },
        {
            "rule_code": "OISD-GDN-192-4.1",
            "regulation_body": "OISD",
            "title": "Safe operating limits documentation",
            "full_text": "Operating procedures must define safe operating limits for critical process parameters such as pressure, temperature, level, and flow. The documentation should describe consequences of deviation, operator response, and escalation requirements.",
            "category": "general",
        },
    ]


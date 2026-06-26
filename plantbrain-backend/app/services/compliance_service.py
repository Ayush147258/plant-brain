"""Compliance service scaffolding for future shared compliance workflows."""

from app.models.compliance import ComplianceRule


class ComplianceService:
    """Placeholder service boundary for compliance workflow helpers."""

    model = ComplianceRule


compliance_service = ComplianceService()

__all__ = ["ComplianceService", "compliance_service"]

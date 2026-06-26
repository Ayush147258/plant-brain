"""Compliance ORM models for regulatory rules and document checks."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ComplianceRule(Base):
    """ORM model representing a compliance rule or requirement."""

    __tablename__ = "compliance_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    rule_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    regulation_body: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str | None] = mapped_column(String(500))
    full_text: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """Return a concise string representation for debugging."""

        return f"ComplianceRule(id={self.id!r}, rule_code={self.rule_code!r})"


class ComplianceCheck(Base):
    """ORM model representing the result of checking a document against a rule."""

    __tablename__ = "compliance_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    rule_id: Mapped[str] = mapped_column(String(36), nullable=False)
    document_id: Mapped[str | None] = mapped_column(String(36))
    status: Mapped[str | None] = mapped_column(String(50))
    findings: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """Return a concise string representation for debugging."""

        return f"ComplianceCheck(id={self.id!r}, rule_id={self.rule_id!r}, status={self.status!r})"

"""Inspection event ORM model for plant maintenance observations."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Inspection(Base):
    """ORM model representing an equipment inspection event."""

    __tablename__ = "inspections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    equipment_tag: Mapped[str] = mapped_column(String(100), nullable=False)
    inspection_date: Mapped[datetime | None] = mapped_column(DateTime)
    inspector_name: Mapped[str | None] = mapped_column(String(255))
    inspection_type: Mapped[str | None] = mapped_column(String(100))
    findings: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(String(50))
    source_document_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """Return a concise string representation for debugging."""

        return f"Inspection(id={self.id!r}, equipment_tag={self.equipment_tag!r}, severity={self.severity!r})"

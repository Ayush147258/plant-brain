"""Query history ORM model for recorded PlantBrain Q&A interactions."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QueryLog(Base):
    """ORM model representing a user query and generated answer."""

    __tablename__ = "query_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    answer: Mapped[str | None] = mapped_column(Text)
    sources: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    channel: Mapped[str] = mapped_column(String(50), default="web")
    session_id: Mapped[str | None] = mapped_column(String(100))
    helpful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    feedback_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """Return a concise string representation for debugging."""

        return f"QueryLog(id={self.id!r}, language={self.language!r}, channel={self.channel!r})"

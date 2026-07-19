from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import Boolean, Double, ForeignKey, String, Text, Uuid, JSON, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.trace import Trace


class Span(Base):
    __tablename__ = "spans"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    trace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "traces.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    parent_span_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    service_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="unknown-service",
    )

    start_time: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )

    end_time: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    duration_ms: Mapped[float | None] = mapped_column(
        Double,
        nullable=True,
    )

    error: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    stack_trace: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    meta: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    trace: Mapped["Trace"] = relationship(
        "Trace",
        back_populates="spans",
    )

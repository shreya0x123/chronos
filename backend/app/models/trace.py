from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Double, String, Uuid, JSON, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class Trace(Base):
    __tablename__ = "traces"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

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

    has_error: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    meta: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )


    spans: Mapped[list["Span"]] = relationship(
        "Span",
        back_populates="trace",
        cascade="all, delete-orphan",
    )

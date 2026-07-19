import uuid
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
from app.models.trace import Trace


class TraceRepository:

    def get_by_id(self, db: Session, trace_id: uuid.UUID) -> Optional[Trace]:
        return db.scalar(select(Trace).where(Trace.id == trace_id))

    def get_traces(
        self,
        db: Session,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        has_error: Optional[bool] = None,
        min_duration: Optional[float] = None,
    ) -> List[Trace]:
        stmt = select(Trace)
        filters = []
        if search:
            filters.append(Trace.name.icontains(search))
        if has_error is not None:
            filters.append(Trace.has_error == has_error)
        if min_duration is not None:
            filters.append(Trace.duration_ms >= min_duration)

        if filters:
            stmt = stmt.where(and_(*filters))

        # Order by start_time descending
        stmt = stmt.order_by(Trace.start_time.desc()).limit(limit).offset(offset)
        return list(db.scalars(stmt).all())

    def get_traces_count(
        self,
        db: Session,
        search: Optional[str] = None,
        has_error: Optional[bool] = None,
        min_duration: Optional[float] = None,
    ) -> int:
        stmt = select(func.count()).select_from(Trace)
        filters = []
        if search:
            filters.append(Trace.name.icontains(search))
        if has_error is not None:
            filters.append(Trace.has_error == has_error)
        if min_duration is not None:
            filters.append(Trace.duration_ms >= min_duration)

        if filters:
            stmt = stmt.where(and_(*filters))

        return db.scalar(stmt) or 0

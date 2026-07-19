import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.span import Span
from app.schemas.span import SpanCreate


class SpanRepository:

    def get_by_id(self, db: Session, span_id: uuid.UUID) -> Optional[Span]:
        return db.scalar(select(Span).where(Span.id == span_id))

    def get_spans_by_trace(self, db: Session, trace_id: uuid.UUID) -> List[Span]:
        return list(
            db.scalars(
                select(Span)
                .where(Span.trace_id == trace_id)
                .order_by(Span.start_time.asc())
            ).all()
        )

    def get_all_spans(self, db: Session) -> List[Span]:
        return list(db.scalars(select(Span)).all())

    def create(self, db: Session, span_in: SpanCreate) -> Span:
        # Convert float timestamps (seconds) to offset-naive UTC datetime objects
        start_time_dt = datetime.fromtimestamp(span_in.start_time, tz=timezone.utc).replace(tzinfo=None)
        end_time_dt = (
            datetime.fromtimestamp(span_in.end_time, tz=timezone.utc).replace(tzinfo=None)
            if span_in.end_time is not None
            else None
        )


        duration_ms = None
        if end_time_dt and start_time_dt:
            duration_ms = (end_time_dt - start_time_dt).total_seconds() * 1000.0

        # Extract error status from attributes
        is_error = span_in.attributes.get("error", False)
        error_message = span_in.attributes.get("error.message")
        stack_trace = span_in.attributes.get("error.stack_trace")

        # Compile metadata containing attributes and events
        metadata = {
            "attributes": span_in.attributes,
            "events": [
                {
                    "name": event.name,
                    "timestamp": event.timestamp,
                    "attributes": event.attributes,
                }
                for event in span_in.events
            ],
        }

        span = Span(
            id=uuid.UUID(span_in.span_id),
            trace_id=uuid.UUID(span_in.trace_id),
            parent_span_id=uuid.UUID(span_in.parent_span_id)
            if span_in.parent_span_id
            else None,
            name=span_in.name,
            service_name=span_in.service_name,
            start_time=start_time_dt,
            end_time=end_time_dt,
            duration_ms=duration_ms,
            error=is_error,
            error_message=error_message,
            stack_trace=stack_trace,
            meta=metadata,
        )

        db.add(span)
        db.flush()  # Make it available in the current transaction
        return span

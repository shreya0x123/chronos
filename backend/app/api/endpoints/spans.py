from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.span import SpanCreate, SpanResponse
from app.services.trace_service import TraceService
from app.repositories.trace_repository import TraceRepository
from app.models.span import Span as DbSpan
from app.api.endpoints.websocket import manager
import asyncio

router = APIRouter()
trace_service = TraceService()
trace_repo = TraceRepository()


@router.post("/", response_model=SpanResponse, status_code=status.HTTP_201_CREATED)
async def create_span(span_in: SpanCreate, db: Session = Depends(get_db)):
    try:
        span = trace_service.ingest_span(db, span_in)

        # Retrieve trace aggregation parameters to notify client WebSockets
        trace = trace_repo.get_by_id(db, span.trace_id)
        if trace:
            span_count = (
                db.scalar(
                    select(func.count())
                    .select_from(DbSpan)
                    .where(DbSpan.trace_id == trace.id)
                )
                or 0
            )

            trace_info = {
                "id": str(trace.id),
                "name": trace.name,
                "start_time": trace.start_time.isoformat(),
                "end_time": trace.end_time.isoformat() if trace.end_time else None,
                "duration_ms": trace.duration_ms,
                "has_error": trace.has_error,
                "span_count": span_count,
            }

            # Fire-and-forget WebSocket broadcast
            asyncio.create_task(
                manager.broadcast({"type": "trace_updated", "trace": trace_info})
            )

        return span
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to ingest span: {str(e)}")

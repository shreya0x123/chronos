import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.span import TraceResponse, TraceDetailResponse
from app.repositories.trace_repository import TraceRepository
from app.repositories.span_repository import SpanRepository
from app.models.span import Span as DbSpan

router = APIRouter()
trace_repo = TraceRepository()
span_repo = SpanRepository()


@router.get("/", response_model=List[TraceResponse])
def get_traces(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    has_error: Optional[bool] = None,
    min_duration: Optional[float] = None,
    db: Session = Depends(get_db),
):
    traces = trace_repo.get_traces(
        db,
        limit=limit,
        offset=offset,
        search=search,
        has_error=has_error,
        min_duration=min_duration,
    )

    response_data = []
    for trace in traces:
        span_count = (
            db.scalar(
                select(func.count())
                .select_from(DbSpan)
                .where(DbSpan.trace_id == trace.id)
            )
            or 0
        )
        response_data.append(
            {
                "id": trace.id,
                "name": trace.name,
                "start_time": trace.start_time,
                "end_time": trace.end_time,
                "duration_ms": trace.duration_ms,
                "has_error": trace.has_error,
                "span_count": span_count,
            }
        )
    return response_data


@router.get("/{trace_id}", response_model=TraceDetailResponse)
def get_trace_detail(trace_id: uuid.UUID, db: Session = Depends(get_db)):
    trace = trace_repo.get_by_id(db, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    spans = span_repo.get_spans_by_trace(db, trace_id)

    return {
        "id": trace.id,
        "name": trace.name,
        "start_time": trace.start_time,
        "end_time": trace.end_time,
        "duration_ms": trace.duration_ms,
        "has_error": trace.has_error,
        "metadata": trace.meta,
        "spans": spans,
    }

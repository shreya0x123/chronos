from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


class EventSchema(BaseModel):
    name: str
    timestamp: float
    attributes: Dict[str, Any] = Field(default_factory=dict)


class SpanCreate(BaseModel):
    name: str
    span_id: str
    trace_id: str
    service_name: str = "unknown-service"
    parent_span_id: Optional[str] = None
    start_time: float
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[EventSchema] = Field(default_factory=list)


class SpanResponse(BaseModel):
    id: uuid.UUID
    trace_id: uuid.UUID
    parent_span_id: Optional[uuid.UUID] = None
    name: str
    service_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    error: bool
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def resolve_metadata(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            # Resolve db ORM object to serialize meta column
            return {
                "id": data.id,
                "trace_id": data.trace_id,
                "parent_span_id": data.parent_span_id,
                "name": data.name,
                "service_name": data.service_name,
                "start_time": data.start_time,
                "end_time": data.end_time,
                "duration_ms": data.duration_ms,
                "error": data.error,
                "error_message": data.error_message,
                "stack_trace": data.stack_trace,
                "metadata": data.meta,
            }
        if "meta" in data:
            data["metadata"] = data.pop("meta")
        return data

    class Config:
        from_attributes = True


class TraceResponse(BaseModel):
    id: uuid.UUID
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    has_error: bool
    span_count: int

    class Config:
        from_attributes = True


class TraceDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    has_error: bool
    metadata: Optional[Dict[str, Any]] = None
    spans: List[SpanResponse]

    @model_validator(mode="before")
    @classmethod
    def resolve_metadata(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return {
                "id": data.id,
                "name": data.name,
                "start_time": data.start_time,
                "end_time": data.end_time,
                "duration_ms": data.duration_ms,
                "has_error": data.has_error,
                "metadata": data.meta,
                "spans": data.spans,
            }
        if "meta" in data:
            data["metadata"] = data.pop("meta")
        return data

    class Config:
        from_attributes = True


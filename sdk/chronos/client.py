import uuid
from typing import Optional, List, Dict
from .models import Span
from .exporter import SpanExporter, ConsoleSpanExporter


class ChronosClient:
    _instance: Optional["ChronosClient"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ChronosClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, service_name: str = "unknown-service", exporter: Optional[SpanExporter] = None):
        # Prevent re-initialization if already initialized
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.service_name = service_name
        self.exporter = exporter or ConsoleSpanExporter()
        self._active_spans: List[Span] = []
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "ChronosClient":
        if not cls._instance:
            cls._instance = ChronosClient()
        return cls._instance

    def start_span(
        self,
        name: str,
        parent_span_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> Span:
        # Resolve trace_id (either passed from parent context or active span, or new one)
        t_id = trace_id
        if not t_id:
            t_id = (
                self._active_spans[-1].trace_id
                if self._active_spans
                else uuid.uuid4().hex
            )
        
        # Resolve parent_span_id
        parent_id = parent_span_id
        if not parent_id and self._active_spans:
            parent_id = self._active_spans[-1].span_id

        span = Span(
            name=name,
            span_id=uuid.uuid4().hex,  # Full 32-char UUID hex representation
            trace_id=t_id,
            parent_span_id=parent_id,
            service_name=self.service_name,
        )
        self._active_spans.append(span)
        return span

    def finish_span(self, span: Span) -> None:
        span.finish()
        if span in self._active_spans:
            self._active_spans.remove(span)
        # Export the finished span
        self.exporter.export([span])

    def inject_context(self, span: Span, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into request headers."""
        headers["x-chronos-trace-id"] = span.trace_id
        headers["x-chronos-span-id"] = span.span_id
        return headers

    def extract_context(self, headers: Dict[str, str]) -> Dict[str, Optional[str]]:
        """Extract trace context from request headers."""
        # Normalize headers to lowercase to be case-insensitive
        headers_lower = {k.lower(): v for k, v in headers.items()}
        return {
            "trace_id": headers_lower.get("x-chronos-trace-id"),
            "parent_span_id": headers_lower.get("x-chronos-span-id"),
        }


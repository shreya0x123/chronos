import json
from abc import ABC, abstractmethod
from typing import List
import urllib.request
from .models import Span


class SpanExporter(ABC):

    @abstractmethod
    def export(self, spans: List[Span]) -> None:
        pass


class ConsoleSpanExporter(SpanExporter):

    def export(self, spans: List[Span]) -> None:
        for span in spans:
            print(f"[Chronos Trace] Exported Span: {span}")


class HTTPSpanExporter(SpanExporter):

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def export(self, spans: List[Span]) -> None:
        for span in spans:
            # Simple conversion of Span dataclass to dict
            span_data = {
                "name": span.name,
                "span_id": span.span_id,
                "trace_id": span.trace_id,
                "parent_span_id": span.parent_span_id,
                "start_time": span.start_time,
                "end_time": span.end_time,
                "attributes": span.attributes,
                "events": [
                    {
                        "name": e.name,
                        "timestamp": e.timestamp,
                        "attributes": e.attributes,
                    }
                    for e in span.events
                ],
            }
            try:
                data = json.dumps(span_data).encode("utf-8")
                req = urllib.request.Request(
                    self.endpoint,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req):
                    pass  # Export successful
            except Exception as e:
                # Fallback to printing error in console for debugging
                print(f"[Chronos Trace] Failed to export span to {self.endpoint}: {e}")

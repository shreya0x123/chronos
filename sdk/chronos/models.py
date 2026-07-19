import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Event:
    name: str
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    name: str
    span_id: str
    trace_id: str
    service_name: str = "unknown-service"
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Event] = field(default_factory=list)

    def finish(self) -> None:
        self.end_time = time.time()

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a metadata attribute on the span."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Record an event/log on the span."""
        self.events.append(Event(name=name, attributes=attributes or {}))

    def record_exception(self, exc: Exception) -> None:
        """Record an exception attribute and stack trace on the span."""
        self.set_attribute("error", True)
        self.set_attribute("error.message", str(exc))
        self.set_attribute(
            "error.stack_trace",
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        )

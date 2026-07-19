import functools
from typing import Any, Callable, Optional
from .client import ChronosClient


class TraceContextManager:

    def __init__(
        self,
        name: str,
        parent_span_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ):
        self.name = name
        self.parent_span_id = parent_span_id
        self.trace_id = trace_id
        self.client = ChronosClient.get_instance()
        self.span = None

    def __enter__(self):
        self.span = self.client.start_span(
            name=self.name,
            parent_span_id=self.parent_span_id,
            trace_id=self.trace_id,
        )
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_val:
                self.span.record_exception(exc_val)
            self.client.finish_span(self.span)


def trace(name: Optional[str] = None) -> Callable:
    """Decorator to trace functions.

    Usage:
        @trace("my_function")
        def my_func():
            pass
    """

    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with TraceContextManager(span_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


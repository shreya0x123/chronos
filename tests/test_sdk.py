import sys
import os

# Add local path to test imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../sdk")))

from chronos import ChronosClient, ConsoleSpanExporter


def test_sdk_span_creation_and_fields():
    client = ChronosClient(service_name="test-service", exporter=ConsoleSpanExporter())
    span = client.start_span("test_operation")

    assert span.name == "test_operation"
    assert span.service_name == "test-service"
    assert len(span.span_id) == 32
    assert len(span.trace_id) == 32
    assert span.parent_span_id is None
    assert span.end_time is None

    client.finish_span(span)
    assert span.end_time is not None


def test_sdk_attributes_and_events():
    client = ChronosClient(service_name="test-service")
    span = client.start_span("test_ops")

    span.set_attribute("key1", "val1")
    span.add_event("event1", {"info": "details"})

    assert span.attributes["key1"] == "val1"
    assert len(span.events) == 1
    assert span.events[0].name == "event1"
    assert span.events[0].attributes["info"] == "details"

    client.finish_span(span)


def test_sdk_exception_recording():
    client = ChronosClient(service_name="test-service")
    span = client.start_span("test_ops")

    err = ValueError("Test Exception")
    span.record_exception(err)

    assert span.attributes["error"] is True
    assert span.attributes["error.message"] == "Test Exception"
    assert "ValueError" in span.attributes["error.stack_trace"]

    client.finish_span(span)


def test_sdk_context_propagation():
    client = ChronosClient(service_name="test-service")
    span1 = client.start_span("parent")

    headers = {}
    client.inject_context(span1, headers)

    assert headers["x-chronos-trace-id"] == span1.trace_id
    assert headers["x-chronos-span-id"] == span1.span_id

    ctx = client.extract_context(headers)
    assert ctx["trace_id"] == span1.trace_id
    assert ctx["parent_span_id"] == span1.span_id

    client.finish_span(span1)

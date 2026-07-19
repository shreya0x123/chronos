import pytest
import uuid
import sys
import os
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Add local path to test imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from main import app
from app.db.session import get_db

mock_db = MagicMock()

def override_get_db():
    yield mock_db

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)



def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Chronos API"}


@patch("app.api.endpoints.spans.trace_service.ingest_span")
@patch("app.api.endpoints.spans.trace_repo.get_by_id")
def test_ingest_span_mocked(mock_get_trace, mock_ingest):
    trace_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    payload = {
        "name": "test_span",
        "span_id": span_id,
        "trace_id": trace_id,
        "service_name": "test-service",
        "parent_span_id": None,
        "start_time": 1690000000.0,
        "end_time": 1690000000.5,
        "attributes": {"error": False},
        "events": [],
    }

    # Mock database span return object
    mock_span = MagicMock()
    mock_span.id = uuid.UUID(span_id)
    mock_span.trace_id = uuid.UUID(trace_id)
    mock_span.parent_span_id = None
    mock_span.name = "test_span"
    mock_span.service_name = "test-service"
    mock_span.start_time = MagicMock()
    mock_span.end_time = MagicMock()
    mock_span.duration_ms = 500.0
    mock_span.error = False
    mock_span.error_message = None
    mock_span.stack_trace = None
    mock_span.meta = {"attributes": {"error": False}, "events": []}


    mock_ingest.return_value = mock_span
    mock_get_trace.return_value = None  # Mock no trace found to skip WebSocket counts

    response = client.post("/api/v1/spans/", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == "test_span"
    assert response.json()["service_name"] == "test-service"


@patch("app.api.endpoints.traces.trace_repo.get_traces")
def test_get_traces_list_mocked(mock_get_traces):
    mock_trace = MagicMock()
    mock_trace.id = uuid.uuid4()
    mock_trace.name = "root_transaction"
    mock_trace.start_time = MagicMock()
    mock_trace.end_time = MagicMock()
    mock_trace.duration_ms = 120.0
    mock_trace.has_error = False

    mock_get_traces.return_value = [mock_trace]

    response = client.get("/api/v1/traces/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "root_transaction"

from datetime import datetime, timezone
from typing import List, Dict, Any
import uuid
from sqlalchemy.orm import Session
from app.models.trace import Trace
from app.models.span import Span
from app.repositories.trace_repository import TraceRepository
from app.repositories.span_repository import SpanRepository
from app.schemas.span import SpanCreate


class TraceService:

    def __init__(self):
        self.trace_repo = TraceRepository()
        self.span_repo = SpanRepository()

    def ingest_span(self, db: Session, span_in: SpanCreate) -> Span:
        # Check if the Trace already exists
        trace_id = uuid.UUID(span_in.trace_id)
        trace = self.trace_repo.get_by_id(db, trace_id)

        span_start_dt = datetime.fromtimestamp(span_in.start_time, tz=timezone.utc).replace(tzinfo=None)
        span_end_dt = (
            datetime.fromtimestamp(span_in.end_time, tz=timezone.utc).replace(tzinfo=None)
            if span_in.end_time is not None
            else None
        )


        is_error = span_in.attributes.get("error", False)

        if not trace:
            # If trace doesn't exist, initialize it
            trace_duration = None
            if span_end_dt and span_start_dt:
                trace_duration = (span_end_dt - span_start_dt).total_seconds() * 1000.0

            trace = Trace(
                id=trace_id,
                name=span_in.name,  # Fallback trace name is the first span we see
                start_time=span_start_dt,
                end_time=span_end_dt,
                duration_ms=trace_duration,
                has_error=is_error,
                metadata={},
            )
            db.add(trace)
        else:
            # Update trace parameters incrementally as spans flow in
            if span_start_dt < trace.start_time:
                trace.start_time = span_start_dt

            if span_end_dt:
                if not trace.end_time or span_end_dt > trace.end_time:
                    trace.end_time = span_end_dt

            if trace.end_time and trace.start_time:
                trace.duration_ms = (
                    (trace.end_time - trace.start_time).total_seconds() * 1000.0
                )

            if is_error:
                trace.has_error = True

            # If this is the root span, update the trace name to be the root name
            if not span_in.parent_span_id:
                trace.name = span_in.name

        # Flush the trace to DB first so spans foreign key constraints pass
        db.flush()

        # Create the Span database record
        span = self.span_repo.create(db, span_in)

        db.commit()
        db.refresh(trace)
        db.refresh(span)
        return span

    def get_service_map(self, db: Session) -> Dict[str, Any]:
        """Generate network nodes and edges from parent-child relationships across service boundaries."""
        spans = self.span_repo.get_all_spans(db)
        span_map = {span.id: span for span in spans}

        nodes = set()
        edges = {}

        for span in spans:
            nodes.add(span.service_name)

            if span.parent_span_id and span.parent_span_id in span_map:
                parent_span = span_map[span.parent_span_id]
                source = parent_span.service_name
                target = span.service_name

                # Check if it crosses a service boundary
                if source != target:
                    edge_key = (source, target)
                    if edge_key not in edges:
                        edges[edge_key] = {"calls": 0, "errors": 0, "durations": []}

                    edges[edge_key]["calls"] += 1
                    if span.error:
                        edges[edge_key]["errors"] += 1
                    if span.duration_ms is not None:
                        edges[edge_key]["durations"].append(span.duration_ms)

        # Format graph nodes
        formatted_nodes = [{"id": node, "label": node} for node in nodes]

        # Format graph edges with averages
        formatted_edges = []
        for (source, target), stats in edges.items():
            durs = stats["durations"]
            avg_duration = sum(durs) / len(durs) if durs else 0.0
            formatted_edges.append(
                {
                    "source": source,
                    "target": target,
                    "calls": stats["calls"],
                    "errors": stats["errors"],
                    "avg_duration_ms": round(avg_duration, 2),
                }
            )

        return {"nodes": formatted_nodes, "edges": formatted_edges}

    def get_service_metrics(self, db: Session) -> List[Dict[str, Any]]:
        """Calculate throughput, error rates, and response latency percentiles grouped by service."""
        spans = self.span_repo.get_all_spans(db)

        service_stats = {}
        for span in spans:
            svc = span.service_name
            if svc not in service_stats:
                service_stats[svc] = {"calls": 0, "errors": 0, "durations": []}

            service_stats[svc]["calls"] += 1
            if span.error:
                service_stats[svc]["errors"] += 1
            if span.duration_ms is not None:
                service_stats[svc]["durations"].append(span.duration_ms)

        metrics = []
        for svc, stats in service_stats.items():
            durs = sorted(stats["durations"])
            count = len(durs)

            p50 = durs[int(count * 0.5)] if count > 0 else 0.0
            p90 = durs[int(count * 0.9)] if count > 0 else 0.0
            p99 = durs[int(count * 0.99)] if count > 0 else 0.0
            avg = sum(durs) / count if count > 0 else 0.0

            metrics.append(
                {
                    "service_name": svc,
                    "calls": stats["calls"],
                    "errors": stats["errors"],
                    "error_rate": round((stats["errors"] / stats["calls"]) * 100.0, 2)
                    if stats["calls"] > 0
                    else 0.0,
                    "avg_duration_ms": round(avg, 2),
                    "p50_ms": round(p50, 2),
                    "p90_ms": round(p90, 2),
                    "p99_ms": round(p99, 2),
                }
            )

        return metrics

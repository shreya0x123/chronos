import React, { useState, useEffect } from "react";
import { getTraceDetails } from "../services/api";
import { ArrowLeft, Clock, Server, AlertTriangle, Layers, Tag, Database } from "lucide-react";

export default function TraceDetails({ traceId, onBack }) {
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSpan, setSelectedSpan] = useState(null);
  const [activeTab, setActiveTab] = useState("attributes");
  const [collapsedSpans, setCollapsedSpans] = useState(new Set());

  useEffect(() => {
    const loadDetails = async () => {
      try {
        setLoading(true);
        const data = await getTraceDetails(traceId);
        setTrace(data);
        // Default select root span if available
        if (data.spans && data.spans.length > 0) {
          // Root is typically the span with no parent_span_id, or first span
          const rootSpan = data.spans.find((s) => !s.parent_span_id) || data.spans[0];
          setSelectedSpan(rootSpan);
        }
        setError(null);
      } catch (err) {
        setError("Failed to load trace details");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (traceId) {
      loadDetails();
    }
  }, [traceId]);

  if (loading) {
    return (
      <div className="content-body" style={{ textAlign: "center", padding: "4rem" }}>
        Loading trace details...
      </div>
    );
  }

  if (error || !trace) {
    return (
      <div className="content-body" style={{ textAlign: "center", padding: "4rem", color: "var(--error)" }}>
        <p>{error || "Trace not found"}</p>
        <button className="btn btn-secondary" onClick={onBack} style={{ marginTop: "1rem" }}>
          Back to Dashboard
        </button>
      </div>
    );
  }

  // Build Span Tree and sort them for Pre-order traversal
  const buildOrderedSpans = () => {
    const spanMap = {};
    const roots = [];
    
    trace.spans.forEach((span) => {
      spanMap[span.id] = { ...span, children: [] };
    });

    trace.spans.forEach((span) => {
      if (span.parent_span_id && spanMap[span.parent_span_id]) {
        spanMap[span.parent_span_id].children.push(spanMap[span.id]);
      } else {
        roots.push(spanMap[span.id]);
      }
    });

    const ordered = [];
    const traverse = (node, depth = 0) => {
      ordered.push({ ...node, depth });
      // Sort children by start time
      node.children.sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
      node.children.forEach((child) => traverse(child, depth + 1));
    };

    roots.sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
    roots.forEach((root) => traverse(root, 0));
    return ordered;
  };

  const orderedSpans = buildOrderedSpans();

  // Collapsible toggle helper
  const toggleCollapse = (spanId, e) => {
    e.stopPropagation();
    setCollapsedSpans((prev) => {
      const next = new Set(prev);
      if (next.has(spanId)) {
        next.delete(spanId);
      } else {
        next.add(spanId);
      }
      return next;
    });
  };

  // Filter out spans whose parents are collapsed
  const isSpanVisible = (span) => {
    let currentParentId = span.parent_span_id;
    while (currentParentId) {
      if (collapsedSpans.has(currentParentId)) {
        return false;
      }
      const parent = trace.spans.find((s) => s.id === currentParentId);
      currentParentId = parent ? parent.parent_span_id : null;
    }
    return true;
  };

  const visibleSpans = orderedSpans.filter(isSpanVisible);

  // Time calculations
  const traceStart = new Date(trace.start_time).getTime();
  const traceEnd = trace.end_time ? new Date(trace.end_time).getTime() : traceStart + (trace.duration_ms || 1);
  const traceDuration = Math.max(traceEnd - traceStart, 1);

  return (
    <div className="content-body" style={{ flexGrow: 1, display: "flex", flexDirection: "column", padding: "1.5rem" }}>
      {/* Detail Header */}
      <div style={{ display: "flex", gap: "1rem", alignItems: "center", marginBottom: "1.5rem" }}>
        <button className="btn btn-secondary" onClick={onBack} style={{ padding: "0.5rem" }}>
          <ArrowLeft size={18} />
        </button>
        <div style={{ flexGrow: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <h1 style={{ fontSize: "1.5rem", fontWeight: "600" }}>{trace.name}</h1>
            <span className={`badge ${trace.has_error ? "error" : "success"}`}>
              {trace.has_error ? "Failing" : "Success"}
            </span>
          </div>
          <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.25rem", color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
              <Clock size={14} /> Duration: {(trace.duration_ms || 0).toFixed(1)} ms
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
              <Layers size={14} /> Spans: {trace.spans.length}
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
              <Database size={14} /> ID: <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.8125rem" }}>{trace.id}</code>
            </span>
          </div>
        </div>
      </div>

      {/* Main Workspace split screen */}
      <div style={{ display: "flex", gap: "1.5rem", flexGrow: 1, height: "calc(100vh - 200px)" }}>
        {/* Left Side: Timeline Gantt list */}
        <div className="glass-panel" style={{ flexGrow: 1, padding: "1.25rem", overflowY: "auto", display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-secondary)", fontSize: "0.75rem", textTransform: "uppercase", paddingBottom: "0.75rem", borderBottom: "1px solid var(--border-glass)" }}>
            <span>Nesting & Span Operations</span>
            <span>Timeline Visualization</span>
          </div>

          <div className="gantt-chart" style={{ flexGrow: 1 }}>
            {visibleSpans.map((span) => {
              const spanStart = new Date(span.start_time).getTime();
              const spanEnd = span.end_time ? new Date(span.end_time).getTime() : spanStart + (span.duration_ms || 0);
              
              const leftOffset = Math.max(0, ((spanStart - traceStart) / traceDuration) * 100);
              const barWidth = Math.max(0.5, ((spanEnd - spanStart) / traceDuration) * 100);

              const hasChildren = orderedSpans.some((s) => s.parent_span_id === span.id);
              const isCollapsed = collapsedSpans.has(span.id);

              return (
                <div
                  key={span.id}
                  className={`gantt-row ${selectedSpan?.id === span.id ? "selected" : ""}`}
                  onClick={() => setSelectedSpan(span)}
                  style={{ cursor: "pointer" }}
                >
                  {/* Indentation / Metadata */}
                  <div className="gantt-info" style={{ paddingLeft: `${span.depth * 1.25}rem` }}>
                    <span
                      onClick={(e) => hasChildren && toggleCollapse(span.id, e)}
                      style={{
                        cursor: hasChildren ? "pointer" : "default",
                        opacity: hasChildren ? 0.7 : 0,
                        fontSize: "0.75rem",
                        width: "12px",
                        display: "inline-block",
                      }}
                    >
                      {isCollapsed ? "▶" : "▼"}
                    </span>
                    <div className="gantt-name-wrapper">
                      <span className="gantt-service-tag" style={{ marginRight: "0.5rem" }}>
                        {span.service_name}
                      </span>
                      <span style={{ fontWeight: "500", fontSize: "0.875rem" }}>{span.name}</span>
                    </div>
                  </div>

                  {/* Gantt Bar rendering */}
                  <div className="gantt-timeline-track">
                    <div
                      className={`gantt-bar ${span.error ? "error" : "success"}`}
                      style={{
                        left: `${leftOffset}%`,
                        width: `${barWidth}%`,
                      }}
                    >
                      <span className="gantt-bar-label">
                        {(span.duration_ms || 0).toFixed(1)} ms
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Side: Selected Span Details panel */}
        {selectedSpan && (
          <div className="details-drawer glass-panel">
            <div style={{ borderBottom: "1px solid var(--border-glass)", paddingBottom: "1rem", marginBottom: "1rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--text-secondary)", fontSize: "0.75rem", textTransform: "uppercase" }}>
                <Server size={12} /> {selectedSpan.service_name}
              </div>
              <h2 style={{ fontSize: "1.25rem", fontWeight: "600", marginTop: "0.25rem" }}>
                {selectedSpan.name}
              </h2>
              <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem", fontSize: "0.8125rem" }}>
                <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                  <Clock size={12} /> {(selectedSpan.duration_ms || 0).toFixed(2)} ms
                </span>
                {selectedSpan.error && (
                  <span className="badge error" style={{ padding: "0.1rem 0.4rem" }}>
                    <AlertTriangle size={10} style={{ marginRight: "2px" }} /> Error
                  </span>
                )}
              </div>
            </div>

            {/* Tabs selector */}
            <div className="tab-container" style={{ marginBottom: "1rem" }}>
              <button
                className={`tab-btn ${activeTab === "attributes" ? "active" : ""}`}
                onClick={() => setActiveTab("attributes")}
              >
                Attributes
              </button>
              <button
                className={`tab-btn ${activeTab === "events" ? "active" : ""}`}
                onClick={() => setActiveTab("events")}
              >
                Events ({selectedSpan.metadata?.events?.length || 0})
              </button>
              {selectedSpan.error && (
                <button
                  className={`tab-btn ${activeTab === "exception" ? "active" : ""}`}
                  style={{ color: "var(--error)" }}
                  onClick={() => setActiveTab("exception")}
                >
                  Stack Trace
                </button>
              )}
            </div>

            {/* Tab contents */}
            <div style={{ flexGrow: 1, overflowY: "auto" }}>
              {activeTab === "attributes" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {Object.entries(selectedSpan.metadata?.attributes || {}).length === 0 ? (
                    <div style={{ color: "var(--text-secondary)", fontSize: "0.875rem", textAlign: "center", padding: "1.5rem" }}>
                      No attributes set.
                    </div>
                  ) : (
                    Object.entries(selectedSpan.metadata.attributes).map(([k, v]) => (
                      <div
                        key={k}
                        style={{
                          background: "rgba(255,255,255,0.02)",
                          border: "1px solid var(--border-glass)",
                          borderRadius: "6px",
                          padding: "0.5rem 0.75rem",
                          fontSize: "0.8125rem",
                        }}
                      >
                        <div style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)", fontSize: "0.75rem", marginBottom: "0.25rem" }}>
                          {k}
                        </div>
                        <div style={{ wordBreak: "break-all", fontFamily: "var(--font-mono)" }}>
                          {typeof v === "object" ? JSON.stringify(v) : String(v)}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === "events" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {(!selectedSpan.metadata?.events || selectedSpan.metadata.events.length === 0) ? (
                    <div style={{ color: "var(--text-secondary)", fontSize: "0.875rem", textAlign: "center", padding: "1.5rem" }}>
                      No correlated logs or events recorded.
                    </div>
                  ) : (
                    selectedSpan.metadata.events.map((event, idx) => {
                      const eventTime = event.timestamp;
                      const timeOffset = (eventTime - selectedSpan.start_time) * 1000;
                      return (
                        <div
                          key={idx}
                          style={{
                            borderLeft: "2px solid var(--primary)",
                            paddingLeft: "0.75rem",
                            fontSize: "0.875rem",
                          }}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span style={{ fontWeight: "600" }}>{event.name}</span>
                            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                              +{timeOffset.toFixed(1)} ms
                            </span>
                          </div>
                          {event.attributes && Object.keys(event.attributes).length > 0 && (
                            <pre
                              style={{
                                fontFamily: "var(--font-mono)",
                                fontSize: "0.75rem",
                                background: "rgba(255,255,255,0.03)",
                                padding: "0.375rem",
                                borderRadius: "4px",
                                marginTop: "0.25rem",
                                overflowX: "auto",
                              }}
                            >
                              {JSON.stringify(event.attributes, null, 2)}
                            </pre>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              )}

              {activeTab === "exception" && selectedSpan.error && (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  <div style={{ color: "var(--error)", fontSize: "0.875rem", fontWeight: "600", display: "flex", alignItems: "center", gap: "0.25rem" }}>
                    <AlertTriangle size={16} /> Error Message
                  </div>
                  <div
                    style={{
                      background: "rgba(244,63,94,0.05)",
                      border: "1px solid rgba(244,63,94,0.15)",
                      borderRadius: "6px",
                      padding: "0.75rem",
                      fontSize: "0.875rem",
                      fontFamily: "var(--font-mono)",
                      wordBreak: "break-all",
                    }}
                  >
                    {selectedSpan.error_message || "Unknown error"}
                  </div>

                  {selectedSpan.stack_trace && (
                    <>
                      <div style={{ color: "var(--text-secondary)", fontSize: "0.8125rem", fontWeight: "500", marginTop: "0.5rem" }}>
                        Stack Trace Console
                      </div>
                      <pre className="terminal-block">{selectedSpan.stack_trace}</pre>
                    </>
                  )}
                </div>
              )}
            </div>

            <div style={{ borderTop: "1px solid var(--border-glass)", paddingTop: "1rem", marginTop: "1rem", fontSize: "0.75rem", color: "var(--text-muted)", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              <div>Span ID: {selectedSpan.id}</div>
              {selectedSpan.parent_span_id && <div>Parent Span ID: {selectedSpan.parent_span_id}</div>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

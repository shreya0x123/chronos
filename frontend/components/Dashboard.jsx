import React, { useState, useEffect, useRef } from "react";
import { getTraces } from "../services/api";
import { Search, AlertTriangle, Clock, List, RefreshCw, Activity } from "lucide-react";

export default function Dashboard({ onSelectTrace }) {
  const [traces, setTraces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [filters, setFilters] = useState({
    search: "",
    has_error: "",
    min_duration: "",
  });
  const [recentGlow, setRecentGlow] = useState(null);
  const wsRef = useRef(null);

  // Load traces on initial render and filter change
  const loadTraces = async () => {
    try {
      setLoading(true);
      const data = await getTraces(filters);
      setTraces(data);
      setError(null);
    } catch (err) {
      setError("Failed to fetch traces");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTraces();
  }, [filters]);

  // WebSocket Live Stream Integration
  useEffect(() => {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Connect to backend ws endpoint (proxied or direct)
    const wsUrl = `${wsProtocol}//${window.location.host === "localhost:5173" ? "localhost:8000" : window.location.host}/api/v1/ws`;
    
    const connectWs = () => {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
        console.log("WebSocket connected to live stream");
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "trace_updated") {
            const updatedTrace = msg.trace;
            setTraces((prevTraces) => {
              // Check if trace already exists in the list
              const exists = prevTraces.some((t) => t.id === updatedTrace.id);
              let newList;
              if (exists) {
                // Update and move to top
                newList = [
                  updatedTrace,
                  ...prevTraces.filter((t) => t.id !== updatedTrace.id),
                ];
              } else {
                // Prepend new trace
                newList = [updatedTrace, ...prevTraces];
              }
              return newList;
            });
            // Glow the updated trace row
            setRecentGlow(updatedTrace.id);
            setTimeout(() => setRecentGlow(null), 1000);
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        console.log("WebSocket closed. Reconnecting in 3s...");
        setTimeout(connectWs, 3000);
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        ws.close();
      };
    };

    connectWs();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Compute stat summaries
  const totalTraces = traces.length;
  const errorTraces = traces.filter((t) => t.has_error).length;
  const errorRate = totalTraces > 0 ? ((errorTraces / totalTraces) * 100).toFixed(1) : "0.0";
  const averageDuration =
    totalTraces > 0
      ? (traces.reduce((acc, t) => acc + (t.duration_ms || 0), 0) / totalTraces).toFixed(0)
      : "0";

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="content-body">
      {/* Dashboard Top Header & Stats */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: "600", marginBottom: "0.25rem" }}>
            Traces Explorer
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            Monitor and diagnose transactions across your distributed stack in real time.
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span className="badge" style={{ background: "rgba(255,255,255,0.05)", border: "1px solid var(--border-glass)" }}>
            <span className={wsConnected ? "pulsing-dot" : ""} style={{ marginRight: "0.5rem", background: wsConnected ? "var(--success)" : "var(--text-muted)" }} />
            {wsConnected ? "Live Feed Active" : "Live Feed Connecting"}
          </span>
          <button className="btn btn-secondary" onClick={loadTraces} title="Reload list">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card glass-panel">
          <div className="stat-icon primary">
            <List size={22} />
          </div>
          <div>
            <div className="stat-label">Total Traces</div>
            <div className="stat-value">{totalTraces}</div>
          </div>
        </div>

        <div className="stat-card glass-panel">
          <div className="stat-icon error">
            <AlertTriangle size={22} />
          </div>
          <div>
            <div className="stat-label">Error Rate</div>
            <div className="stat-value">{errorRate}%</div>
          </div>
        </div>

        <div className="stat-card glass-panel">
          <div className="stat-icon warning">
            <Clock size={22} />
          </div>
          <div>
            <div className="stat-label">Avg Latency</div>
            <div className="stat-value">{averageDuration}ms</div>
          </div>
        </div>

        <div className="stat-card glass-panel">
          <div className="stat-icon success">
            <Activity size={22} />
          </div>
          <div>
            <div className="stat-label">Throughput</div>
            <div className="stat-value">Live Stream</div>
          </div>
        </div>
      </div>

      {/* Advanced Filter Toolbar */}
      <div className="glass-panel" style={{ padding: "1.25rem", display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ position: "relative", flexGrow: 1, minWidth: "240px" }}>
          <Search size={18} style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
          <input
            type="text"
            className="input-field"
            placeholder="Search by Trace/Service name..."
            value={filters.search}
            onChange={(e) => handleFilterChange("search", e.target.value)}
            style={{ width: "100%", paddingLeft: "2.5rem" }}
          />
        </div>

        <select
          className="input-field"
          value={filters.has_error}
          onChange={(e) => handleFilterChange("has_error", e.target.value)}
          style={{ minWidth: "160px" }}
        >
          <option value="">All Statuses</option>
          <option value="false">Success Only</option>
          <option value="true">Errors Only</option>
        </select>

        <input
          type="number"
          className="input-field"
          placeholder="Min duration (ms)"
          value={filters.min_duration}
          onChange={(e) => handleFilterChange("min_duration", e.target.value)}
          style={{ minWidth: "160px" }}
        />
      </div>

      {/* Trace Table */}
      <div className="table-container glass-panel">
        {loading && traces.length === 0 ? (
          <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-secondary)" }}>
            Loading traces...
          </div>
        ) : error ? (
          <div style={{ padding: "3rem", textAlign: "center", color: "var(--error)" }}>
            {error}
          </div>
        ) : traces.length === 0 ? (
          <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-secondary)" }}>
            No traces found. Run the sample app simulator to generate traces!
          </div>
        ) : (
          <table className="custom-table">
            <thead>
              <tr>
                <th style={{ width: "120px" }}>Status</th>
                <th>Root Transaction</th>
                <th>Trace ID</th>
                <th>Start Time</th>
                <th>Span Count</th>
                <th style={{ width: "200px" }}>Duration</th>
              </tr>
            </thead>
            <tbody>
              {traces.map((trace) => {
                const maxDur = Math.max(...traces.map((t) => t.duration_ms || 1), 1);
                const percent = (((trace.duration_ms || 0) / maxDur) * 100).toFixed(0);

                return (
                  <tr
                    key={trace.id}
                    onClick={() => onSelectTrace(trace.id)}
                    className={recentGlow === trace.id ? "live-glow" : ""}
                  >
                    <td>
                      <span className={`badge ${trace.has_error ? "error" : "success"}`}>
                        {trace.has_error ? "Failing" : "Success"}
                      </span>
                    </td>
                    <td style={{ fontWeight: "600" }}>{trace.name}</td>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                      {trace.id.substring(0, 8)}...
                    </td>
                    <td style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                      {new Date(trace.start_time).toLocaleString()}
                    </td>
                    <td>
                      <span style={{ background: "rgba(255,255,255,0.06)", padding: "0.2rem 0.5rem", borderRadius: "4px", fontSize: "0.8125rem" }}>
                        {trace.span_count} spans
                      </span>
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                        <span style={{ fontSize: "0.875rem", fontWeight: "500", minWidth: "50px" }}>
                          {(trace.duration_ms || 0).toFixed(0)} ms
                        </span>
                        <div style={{ flexGrow: 1, height: "4px", background: "rgba(255,255,255,0.06)", borderRadius: "2px", overflow: "hidden", minWidth: "60px" }}>
                          <div
                            style={{
                              width: `${percent}%`,
                              height: "100%",
                              background: trace.has_error ? "var(--error)" : "var(--success)",
                            }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

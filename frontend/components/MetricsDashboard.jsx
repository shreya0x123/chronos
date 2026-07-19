import React, { useState, useEffect } from "react";
import { getServiceMetrics } from "../services/api";
import { RefreshCw, BarChart2, Zap, AlertTriangle, TrendingUp } from "lucide-react";

export default function MetricsDashboard() {
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      const res = await getServiceMetrics();
      setMetrics(res);
      setError(null);
    } catch (err) {
      setError("Failed to fetch service metrics");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
  }, []);

  if (loading) {
    return (
      <div className="content-body" style={{ textAlign: "center", padding: "4rem" }}>
        Loading service performance metrics...
      </div>
    );
  }

  if (error) {
    return (
      <div className="content-body" style={{ textAlign: "center", padding: "4rem", color: "var(--error)" }}>
        <p>{error}</p>
        <button className="btn btn-secondary" onClick={loadMetrics} style={{ marginTop: "1rem" }}>
          Retry
        </button>
      </div>
    );
  }

  // Get max values for visual scaling
  const maxCalls = Math.max(...metrics.map((m) => m.calls), 1);
  const maxLatency = Math.max(...metrics.map((m) => m.p99_ms), 1);

  return (
    <div className="content-body">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: "600", marginBottom: "0.25rem" }}>
            Performance Metrics
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            Analyze P50, P90, and P99 latency percentiles and error rates grouped by service.
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadMetrics}>
          <RefreshCw size={14} /> Refresh Metrics
        </button>
      </div>

      {metrics.length === 0 ? (
        <div className="glass-panel" style={{ padding: "4rem", textAlign: "center", color: "var(--text-secondary)" }}>
          No metrics available. Ingest some tracing spans first!
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
          {/* Summary grid */}
          <div className="stats-grid">
            {metrics.map((svc) => (
              <div key={svc.service_name} className="glass-panel" style={{ padding: "1.25rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <div style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "var(--text-secondary)", fontWeight: "600" }}>
                  {svc.service_name}
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
                  <div>
                    <span style={{ fontSize: "1.25rem", fontWeight: "600" }}>{svc.p99_ms.toFixed(0)}</span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginLeft: "0.15rem" }}>ms p99</span>
                  </div>
                  <span className={`badge ${svc.error_rate > 5 ? "error" : "success"}`} style={{ fontSize: "0.6875rem" }}>
                    {svc.error_rate}% errors
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Detailed metrics lists */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "1.5rem" }}>
            
            {/* Latency Percentiles Card */}
            <div className="glass-panel" style={{ padding: "1.5rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1.25rem", borderBottom: "1px solid var(--border-glass)", paddingBottom: "0.75rem" }}>
                <Zap size={18} style={{ color: "var(--warning)" }} />
                <h2 style={{ fontSize: "1.125rem", fontWeight: "600" }}>Latency Percentiles</h2>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                {metrics.map((svc) => {
                  const p50Width = (svc.p50_ms / maxLatency) * 100;
                  const p90Width = (svc.p90_ms / maxLatency) * 100;
                  const p99Width = (svc.p99_ms / maxLatency) * 100;

                  return (
                    <div key={svc.service_name} style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem" }}>
                        <span style={{ fontWeight: "600" }}>{svc.service_name}</span>
                        <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                          p50: <strong style={{ color: "white" }}>{svc.p50_ms.toFixed(0)}ms</strong> | 
                          p99: <strong style={{ color: "white" }}>{svc.p99_ms.toFixed(0)}ms</strong>
                        </span>
                      </div>
                      
                      {/* Percentile chart bar */}
                      <div style={{ height: "16px", background: "rgba(255,255,255,0.03)", borderRadius: "4px", position: "relative", overflow: "hidden" }}>
                        {/* P99 Bar (fullest) */}
                        <div
                          style={{
                            width: `${p99Width}%`,
                            height: "100%",
                            background: "rgba(99, 102, 241, 0.2)",
                            position: "absolute",
                            left: 0,
                            top: 0,
                          }}
                          title="P99 Latency"
                        />
                        {/* P90 Bar */}
                        <div
                          style={{
                            width: `${p90Width}%`,
                            height: "100%",
                            background: "rgba(99, 102, 241, 0.4)",
                            position: "absolute",
                            left: 0,
                            top: 0,
                          }}
                          title="P90 Latency"
                        />
                        {/* P50 Bar */}
                        <div
                          style={{
                            width: `${p50Width}%`,
                            height: "100%",
                            background: "var(--primary-gradient)",
                            position: "absolute",
                            left: 0,
                            top: 0,
                          }}
                          title="P50 Latency"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Ingestion volumes & Error Rates Card */}
            <div className="glass-panel" style={{ padding: "1.5rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1.25rem", borderBottom: "1px solid var(--border-glass)", paddingBottom: "0.75rem" }}>
                <TrendingUp size={18} style={{ color: "var(--success)" }} />
                <h2 style={{ fontSize: "1.125rem", fontWeight: "600" }}>Throughput & Errors</h2>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                {metrics.map((svc) => {
                  const throughputWidth = (svc.calls / maxCalls) * 100;
                  const hasHighErrors = svc.error_rate > 5.0;

                  return (
                    <div key={svc.service_name} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", alignItems: "center" }}>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                        <div style={{ fontSize: "0.875rem", fontWeight: "600" }}>{svc.service_name}</div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                          {svc.calls} calls processed
                        </div>
                      </div>
                      
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                        {/* Throughput volume bar */}
                        <div style={{ height: "6px", background: "rgba(255,255,255,0.04)", borderRadius: "3px", overflow: "hidden" }}>
                          <div
                            style={{
                              width: `${throughputWidth}%`,
                              height: "100%",
                              background: "var(--success)",
                            }}
                          />
                        </div>
                        {/* Error rate tag */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.75rem", marginTop: "0.15rem" }}>
                          <span style={{ color: "var(--text-secondary)" }}>Error rate:</span>
                          <span style={{ fontWeight: "600", color: hasHighErrors ? "var(--error)" : "var(--success)" }}>
                            {svc.error_rate}%
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}

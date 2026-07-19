import React, { useState } from "react";
import Dashboard from "./components/Dashboard";
import TraceDetails from "./components/TraceDetails";
import ServiceMap from "./components/ServiceMap";
import MetricsDashboard from "./components/MetricsDashboard";
import { Layers, Activity, GitBranch, Cpu } from "lucide-react";

export default function App() {
  const [activeTab, setActiveTab] = useState("traces");
  const [selectedTraceId, setSelectedTraceId] = useState(null);

  const handleSelectTrace = (traceId) => {
    setSelectedTraceId(traceId);
  };

  const handleBackToDashboard = () => {
    setSelectedTraceId(null);
  };

  const handleNavClick = (tab) => {
    setActiveTab(tab);
    // Reset trace selection when navigating away or switching tabs
    setSelectedTraceId(null);
  };

  return (
    <div className="app-container">
      {/* Sidebar navigation */}
      <aside className="sidebar">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "2rem", paddingBottom: "1rem", borderBottom: "1px solid var(--border-glass)" }}>
          <Cpu size={24} style={{ color: "var(--primary)" }} />
          <span style={{ fontSize: "1.25rem", fontWeight: "700", letterSpacing: "-0.02em" }}>
            Chronos
          </span>
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: "0.375rem", flexGrow: 1 }}>
          <button
            className={`tab-btn ${activeTab === "traces" ? "active" : ""}`}
            onClick={() => handleNavClick("traces")}
            style={{ display: "flex", alignItems: "center", gap: "0.75rem", width: "100%", textAlign: "left", padding: "0.75rem 1rem" }}
          >
            <Layers size={18} />
            <span>Traces</span>
          </button>

          <button
            className={`tab-btn ${activeTab === "map" ? "active" : ""}`}
            onClick={() => handleNavClick("map")}
            style={{ display: "flex", alignItems: "center", gap: "0.75rem", width: "100%", textAlign: "left", padding: "0.75rem 1rem" }}
          >
            <GitBranch size={18} />
            <span>Service Map</span>
          </button>

          <button
            className={`tab-btn ${activeTab === "metrics" ? "active" : ""}`}
            onClick={() => handleNavClick("metrics")}
            style={{ display: "flex", alignItems: "center", gap: "0.75rem", width: "100%", textAlign: "left", padding: "0.75rem 1rem" }}
          >
            <Activity size={18} />
            <span>Metrics</span>
          </button>
        </nav>

        <div style={{ padding: "0.5rem", fontSize: "0.75rem", color: "var(--text-muted)", textAlign: "center", borderTop: "1px solid var(--border-glass)", paddingTop: "1rem" }}>
          Chronos Engine v0.2.0
        </div>
      </aside>

      {/* Main Workspace Frame */}
      <main className="main-content">
        <header className="header">
          <div style={{ fontSize: "0.875rem", fontWeight: "500", color: "var(--text-secondary)" }}>
            Environment: <strong style={{ color: "white" }}>Development</strong>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              Endpoint: <code style={{ background: "rgba(255,255,255,0.06)", padding: "0.2rem 0.4rem", borderRadius: "4px" }}>http://localhost:8000/api/v1/spans</code>
            </span>
          </div>
        </header>

        {/* Dynamic page mount */}
        {activeTab === "traces" && (
          selectedTraceId ? (
            <TraceDetails traceId={selectedTraceId} onBack={handleBackToDashboard} />
          ) : (
            <Dashboard onSelectTrace={handleSelectTrace} />
          )
        )}

        {activeTab === "map" && <ServiceMap />}

        {activeTab === "metrics" && <MetricsDashboard />}
      </main>
    </div>
  );
}

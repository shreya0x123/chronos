import React, { useState, useEffect } from "react";
import { getServiceMap } from "../services/api";
import { Activity, RefreshCw } from "lucide-react";

export default function ServiceMap() {
  const [data, setData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [hoveredEdge, setHoveredEdge] = useState(null);

  const loadMap = async () => {
    try {
      setLoading(true);
      const res = await getServiceMap();
      setData(res);
      setError(null);
    } catch (err) {
      setError("Failed to fetch service map");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMap();
  }, []);

  if (loading) {
    return (
      <div className="content-body" style={{ textAlign: "center", padding: "4rem" }}>
        Loading service map topology...
      </div>
    );
  }

  if (error) {
    return (
      <div className="content-body" style={{ textAlign: "center", padding: "4rem", color: "var(--error)" }}>
        <p>{error}</p>
        <button className="btn btn-secondary" onClick={loadMap} style={{ marginTop: "1rem" }}>
          Retry
        </button>
      </div>
    );
  }

  const { nodes, edges } = data;

  // Calculate node positions in a circular ring layout to avoid overlapping
  const width = 800;
  const height = 450;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(centerX, centerY) - 80;

  const positionedNodes = nodes.reduce((acc, node, index) => {
    const angle = (index * 2 * Math.PI) / nodes.length - Math.PI / 2;
    acc[node.id] = {
      ...node,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
    return acc;
  }, {});

  // Check if a node has any error edges connected to it or is emitting errors
  const isNodeFailing = (nodeId) => {
    return edges.some(
      (e) => (e.source === nodeId || e.target === nodeId) && e.errors > 0
    );
  };

  return (
    <div className="content-body">
      <div>
        <h1 style={{ fontSize: "1.75rem", fontWeight: "600", marginBottom: "0.25rem" }}>
          Service Map
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
          Visualize service relationships and health topology of your distributed microservices.
        </p>
      </div>

      <div className="glass-panel" style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", gap: "1rem", fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
              <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "var(--primary)" }} /> Service Node
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
              <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "var(--error)", boxShadow: "0 0 6px var(--error)" }} /> Error / Failing Node
            </span>
          </div>
          <button className="btn btn-secondary" onClick={loadMap}>
            <RefreshCw size={14} /> Refresh Map
          </button>
        </div>

        {nodes.length === 0 ? (
          <div style={{ padding: "4rem", textAlign: "center", color: "var(--text-secondary)" }}>
            No services detected. Run the sample app simulator to populate the topology!
          </div>
        ) : (
          <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
            {/* SVG Visualizer */}
            <div className="topology-container" style={{ flexGrow: 1, minWidth: "400px" }}>
              <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} style={{ display: "block" }}>
                {/* Arrow markers */}
                <defs>
                  <marker
                    id="arrow"
                    viewBox="0 0 10 10"
                    refX="25"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(255, 255, 255, 0.3)" />
                  </marker>
                  <marker
                    id="arrow-error"
                    viewBox="0 0 10 10"
                    refX="25"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--error)" />
                  </marker>
                  <marker
                    id="arrow-active"
                    viewBox="0 0 10 10"
                    refX="25"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--primary)" />
                  </marker>
                </defs>

                {/* Draw links / edges */}
                {edges.map((edge, idx) => {
                  const sourceNode = positionedNodes[edge.source];
                  const targetNode = positionedNodes[edge.target];
                  if (!sourceNode || !targetNode) return null;

                  const isHovered = hoveredEdge === edge || hoveredNode === edge.source || hoveredNode === edge.target;
                  const hasError = edge.errors > 0;

                  return (
                    <g key={`link-${idx}`}>
                      <path
                        d={`M ${sourceNode.x} ${sourceNode.y} L ${targetNode.x} ${targetNode.y}`}
                        className={`topology-link ${hasError ? "has-error" : ""}`}
                        style={{
                          stroke: isHovered
                            ? (hasError ? "var(--error)" : "var(--primary)")
                            : (hasError ? "rgba(244, 63, 94, 0.4)" : "rgba(255, 255, 255, 0.12)"),
                          strokeWidth: isHovered ? 2.5 : 1.5,
                          cursor: "pointer",
                        }}
                        markerEnd={
                          isHovered
                            ? (hasError ? "url(#arrow-error)" : "url(#arrow-active)")
                            : (hasError ? "url(#arrow-error)" : "url(#arrow)")
                        }
                        onMouseEnter={() => setHoveredEdge(edge)}
                        onMouseLeave={() => setHoveredEdge(null)}
                      />
                      {/* Midpoint Label for calls metadata */}
                      {isHovered && (
                        <foreignObject
                          x={(sourceNode.x + targetNode.x) / 2 - 50}
                          y={(sourceNode.y + targetNode.y) / 2 - 15}
                          width="100"
                          height="30"
                        >
                          <div
                            style={{
                              background: "rgba(17, 24, 39, 0.9)",
                              border: `1px solid ${hasError ? "var(--error)" : "var(--primary)"}`,
                              borderRadius: "4px",
                              fontSize: "0.6875rem",
                              padding: "0.125rem 0.25rem",
                              textAlign: "center",
                              color: "white",
                              boxShadow: "0 2px 4px rgba(0,0,0,0.5)",
                            }}
                          >
                            {edge.calls} reqs / {edge.avg_duration_ms}ms
                          </div>
                        </foreignObject>
                      )}
                    </g>
                  );
                })}

                {/* Draw nodes */}
                {Object.values(positionedNodes).map((node) => {
                  const hasError = isNodeFailing(node.id);
                  const isHovered = hoveredNode === node.id || (hoveredEdge && (hoveredEdge.source === node.id || hoveredEdge.target === node.id));

                  return (
                    <g
                      key={node.id}
                      onMouseEnter={() => setHoveredNode(node.id)}
                      onMouseLeave={() => setHoveredNode(null)}
                      style={{ cursor: "pointer" }}
                    >
                      <circle
                        cx={node.x}
                        cy={node.y}
                        r="20"
                        className={`topology-node ${hasError ? "has-error" : ""}`}
                        style={{
                          fill: isHovered ? (hasError ? "rgba(244, 63, 94, 0.2)" : "rgba(99, 102, 241, 0.2)") : "var(--bg-surface-solid)",
                          strokeWidth: isHovered ? 3.5 : 2.5,
                        }}
                      />
                      <text
                        x={node.x}
                        y={node.y + 35}
                        className="topology-text"
                        textAnchor="middle"
                      >
                        {node.label}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Sidebar details summary */}
            <div className="glass-panel" style={{ width: "300px", padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
              <h2 style={{ fontSize: "1.125rem", fontWeight: "600", borderBottom: "1px solid var(--border-glass)", paddingBottom: "0.5rem" }}>
                Topology Inspector
              </h2>
              {hoveredNode ? (
                <div>
                  <div style={{ fontSize: "1rem", fontWeight: "600", color: "var(--primary)", display: "flex", alignItems: "center", gap: "0.25rem" }}>
                    <Activity size={16} /> {hoveredNode}
                  </div>
                  <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
                    Hovering over node. See connected edge links for latencies and throughput stats.
                  </p>
                </div>
              ) : hoveredEdge ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "0.875rem", fontWeight: "600" }}>Call Dependency</span>
                    <span className={`badge ${hoveredEdge.errors > 0 ? "error" : "success"}`}>
                      {hoveredEdge.errors > 0 ? "Errors Present" : "Healthy"}
                    </span>
                  </div>
                  <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-glass)", borderRadius: "6px", padding: "0.75rem", fontSize: "0.8125rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    <div>
                      <span style={{ color: "var(--text-secondary)" }}>From:</span> {hoveredEdge.source}
                    </div>
                    <div>
                      <span style={{ color: "var(--text-secondary)" }}>To:</span> {hoveredEdge.target}
                    </div>
                    <div>
                      <span style={{ color: "var(--text-secondary)" }}>Total Calls:</span> {hoveredEdge.calls}
                    </div>
                    {hoveredEdge.errors > 0 && (
                      <div>
                        <span style={{ color: "var(--error)" }}>Error Calls:</span> {hoveredEdge.errors}
                      </div>
                    )}
                    <div>
                      <span style={{ color: "var(--text-secondary)" }}>Avg Latency:</span> {hoveredEdge.avg_duration_ms} ms
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ color: "var(--text-secondary)", fontSize: "0.875rem", textAlign: "center", padding: "3rem 1rem" }}>
                  Hover over services or link lines to inspect detailed transaction stats.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

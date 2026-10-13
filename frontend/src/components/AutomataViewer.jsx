import React, { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import { buildAutomatonLayout, LARGE_INPUT_THRESHOLD } from '../utils/dagreLayout.js';

export default function AutomataViewer({
  automaton,
  activeStage,
  activeStateId,
  activeTransition,
  xaiExplanation,
  showEdgeImportance,
  setShowEdgeImportance,
}) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState({ x: 0, y: 0 });
  const [hoveredState, setHoveredState] = useState(null);
  const [viewAsTable, setViewAsTable] = useState(false);

  const containerRef = useRef(null);
  const svgRef = useRef(null);

  const states = automaton?.states || [];
  const transitions = automaton?.transitions || [];

  // Build hierarchical layout coordinates
  const layout = useMemo(() => {
    return buildAutomatonLayout(automaton, { nodeRadius: 21 });
  }, [automaton]);

  // Reset pan/zoom on automaton change
  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setHoveredState(null);
  }, [automaton?.id]);

  // Edge importance lookup from XAIExplanation
  const edgeImportanceMap = useMemo(() => {
    const map = {};
    (xaiExplanation?.edge_importance || []).forEach((e) => {
      const key = `${e.from_state}->${e.to_state}:${e.symbol}`;
      map[key] = e.importance;
    });
    return map;
  }, [xaiExplanation]);

  // Pan interaction
  const handleMouseDown = (e) => {
    if (e.button !== 0) return; // Primary click only
    setIsPanning(true);
    setStartPan({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e) => {
    if (!isPanning) return;
    setPan({ x: e.clientX - startPan.x, y: e.clientY - startPan.y });
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom((prev) => Math.min(Math.max(prev * zoomFactor, 0.35), 3.0));
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, [handleWheel]);

  // Fit to view
  const handleFitToView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // Export handlers
  const handleExportSVG = () => {
    if (!svgRef.current) return;
    const svgData = new XMLSerializer().serializeToString(svgRef.current);
    const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${automaton?.name || 'automaton'}.svg`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleExportPNG = () => {
    if (!svgRef.current) return;
    const svgData = new XMLSerializer().serializeToString(svgRef.current);
    const canvas = document.createElement('canvas');
    canvas.width = layout.width * 2;
    canvas.height = layout.height * 2;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {
      ctx.fillStyle = '#f8f9fa';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      const pngUrl = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.href = pngUrl;
      link.download = `${automaton?.name || 'automaton'}.png`;
      link.click();
    };
    img.src = url;
  };

  const handleExportJSON = () => {
    if (!automaton) return;
    const blob = new Blob([JSON.stringify(automaton, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${automaton?.name || 'automaton'}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Find origin NFA states / merged states for the currently hovered state
  const hoveredStateData = useMemo(() => {
    if (!hoveredState) return null;
    return states.find((s) => s.id === hoveredState) || null;
  }, [hoveredState, states]);

  return (
    <div className="drawing-area" id="drawing-area" role="region" aria-label="Automaton railway schematic">
      {/* Controls Bar: Pan, Zoom, Fit, View Table, Export */}
      <div className="drawing-canvas-controls" role="toolbar" aria-label="Diagram controls">
        <button
          type="button"
          className="btn-quiet"
          onClick={() => setZoom((z) => Math.min(z * 1.2, 3))}
          title="Zoom in (+)"
          aria-label="Zoom in"
        >
          Zoom +
        </button>
        <button
          type="button"
          className="btn-quiet"
          onClick={() => setZoom((z) => Math.max(z / 1.2, 0.35))}
          title="Zoom out (-)"
          aria-label="Zoom out"
        >
          Zoom −
        </button>
        <button
          type="button"
          className="btn-quiet"
          onClick={handleFitToView}
          title="Reset zoom and center view"
        >
          Fit view
        </button>

        <span style={{ width: '1px', background: 'var(--ink-border)', margin: '0 0.2rem' }} />

        <button
          type="button"
          className="btn-quiet"
          onClick={() => setViewAsTable(!viewAsTable)}
          aria-pressed={viewAsTable}
        >
          {viewAsTable ? 'View diagram' : 'View as table'}
        </button>

        {setShowEdgeImportance && (
          <button
            type="button"
            className="btn-quiet"
            style={showEdgeImportance ? { backgroundColor: 'var(--amber-tint)', borderColor: 'var(--amber-signal)' } : {}}
            onClick={() => setShowEdgeImportance(!showEdgeImportance)}
            aria-pressed={showEdgeImportance}
          >
            {showEdgeImportance ? 'Edge weight: on' : 'Edge weight'}
          </button>
        )}

        <span style={{ width: '1px', background: 'var(--ink-border)', margin: '0 0.2rem' }} />

        <button type="button" className="btn-quiet" onClick={handleExportSVG}>
          SVG
        </button>
        <button type="button" className="btn-quiet" onClick={handleExportPNG}>
          PNG
        </button>
        <button type="button" className="btn-quiet" onClick={handleExportJSON}>
          JSON
        </button>
      </div>

      {/* Large Input Warning Banner */}
      {layout.isLarge && (
        <div
          style={{
            position: 'absolute',
            top: '3.25rem',
            left: '0.75rem',
            right: '0.75rem',
            zIndex: 9,
            padding: '0.4rem 0.8rem',
            background: 'var(--amber-tint)',
            border: '1px solid var(--amber-signal)',
            borderRadius: 'var(--radius-control)',
            fontSize: 'var(--text-xs)',
            color: 'var(--ink-slate)',
          }}
          role="status"
        >
          <strong>Large automaton ({layout.stateCount} states):</strong> Simplified layout active to prevent browser freezing. Use Zoom controls to inspect nodes.
        </div>
      )}

      {/* Hover Linkage Inspector Tooltip */}
      {hoveredStateData && (
        <div
          style={{
            position: 'absolute',
            bottom: '1rem',
            left: '1rem',
            zIndex: 10,
            background: 'var(--paper-panel)',
            border: '1px solid var(--ink-slate)',
            borderRadius: 'var(--radius-control)',
            padding: '0.5rem 0.75rem',
            fontSize: 'var(--text-xs)',
            maxWidth: '320px',
            boxShadow: '0 2px 6px rgba(0,0,0,0.08)',
          }}
        >
          <div>
            <strong>State: </strong>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 'bold' }}>
              {hoveredStateData.label || hoveredStateData.id}
            </span>
            {hoveredStateData.is_start && ' (Start)'}
            {hoveredStateData.is_accepting && ' (Accepting)'}
          </div>

          {/* NFA subset provenance */}
          {hoveredStateData.metadata?.nfa_subset && (
            <div style={{ marginTop: '0.2rem', color: 'var(--ink-secondary)' }}>
              <strong>Origin NFA states: </strong>
              <span style={{ fontFamily: 'var(--font-mono)' }}>
                {hoveredStateData.metadata.nfa_subset.length > 0
                  ? `{${hoveredStateData.metadata.nfa_subset.join(', ')}}`
                  : '∅ (dead state)'}
              </span>
            </div>
          )}

          {/* Merged DFA states */}
          {hoveredStateData.metadata?.merged_states && (
            <div style={{ marginTop: '0.2rem', color: 'var(--ink-secondary)' }}>
              <strong>Merged DFA states: </strong>
              <span style={{ fontFamily: 'var(--font-mono)' }}>
                {`{${hoveredStateData.metadata.merged_states.join(', ')}}`}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Main View Area: Either Diagram SVG or Accessible Table */}
      {viewAsTable ? (
        <div
          style={{
            padding: '4rem 1.5rem 1.5rem',
            overflow: 'auto',
            width: '100%',
            height: '100%',
          }}
        >
          <h3 style={{ marginBottom: '0.75rem' }}>Transition Table: {automaton?.name || activeStage}</h3>
          <table className="greenbar-table" style={{ background: '#fff', border: 'var(--border-rule)' }}>
            <thead>
              <tr>
                <th>From State</th>
                <th>Input Symbol</th>
                <th>To State</th>
                <th>Properties</th>
              </tr>
            </thead>
            <tbody>
              {transitions.map((t, idx) => (
                <tr key={idx} className="greenbar-row">
                  <td>{t.from_state}</td>
                  <td>{t.symbol}</td>
                  <td>{t.to_state}</td>
                  <td>
                    {t.from_state === t.to_state ? 'Self-loop' : ''}
                    {t.symbol === 'ε' ? ' Epsilon transition' : ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div
          className="drawing-canvas-container"
          ref={containerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <svg
            ref={svgRef}
            className="automaton-svg"
            viewBox={`0 0 ${layout.width} ${layout.height}`}
            width={layout.width}
            height={layout.height}
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: 'center center',
              transition: isPanning ? 'none' : 'transform 0.05s ease-out',
            }}
          >
            <defs>
              {/* Directed Edge Arrow Marker */}
              <marker
                id="arrow-slate"
                viewBox="0 0 10 10"
                refX="25"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--ink-slate)" />
              </marker>

              {/* Active Traversal Amber Arrow Marker */}
              <marker
                id="arrow-amber"
                viewBox="0 0 10 10"
                refX="25"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--amber-signal)" />
              </marker>
            </defs>

            {/* Render Edges (Tracks) */}
            {layout.edges.map((edge, idx) => {
              const u = layout.coords[edge.from_state];
              const v = layout.coords[edge.to_state];
              if (!u || !v) return null;

              const isSelf = edge.isSelfLoop;
              const isActive =
                activeTransition &&
                String(activeTransition.from_state) === String(edge.from_state) &&
                String(activeTransition.to_state) === String(edge.to_state);

              // Calculate importance stroke width if toggle enabled
              let strokeWidth = isActive ? 3.4 : 1.6;
              if (showEdgeImportance && edge.importance > 0) {
                strokeWidth = Math.max(strokeWidth, 1.6 + edge.importance * 3.5);
              }

              const strokeColor = isActive ? 'var(--amber-signal)' : 'var(--ink-slate)';
              const markerId = isActive ? 'url(#arrow-amber)' : 'url(#arrow-slate)';

              if (isSelf) {
                // Self-loop on top of node
                const loopPath = `M ${u.x - 12} ${u.y - 18} C ${u.x - 30} ${u.y - 65}, ${u.x + 30} ${u.y - 65}, ${u.x + 12} ${u.y - 18}`;
                const labelX = u.x;
                const labelY = u.y - 56;
                const labelWidth = Math.max(22, edge.label.length * 8 + 8);

                return (
                  <g key={`edge-${idx}`}>
                    <path
                      d={loopPath}
                      className={`svg-edge-path ${isActive ? 'active' : ''}`}
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      markerEnd={markerId}
                    />
                    <rect
                      x={labelX - labelWidth / 2}
                      y={labelY - 8}
                      width={labelWidth}
                      height={16}
                      rx={2}
                      className="svg-edge-label-bg"
                    />
                    <text x={labelX} y={labelY + 1} className="svg-edge-label-text">
                      {edge.label}
                    </text>
                  </g>
                );
              }

              // Normal directed edge with slight curve
              let pathD = '';
              let labelX = (u.x + v.x) / 2;
              let labelY = (u.y + v.y) / 2;

              if (edge.points && edge.points.length >= 3) {
                // Dagre bezier control points
                const pts = edge.points;
                pathD = `M ${pts[0].x} ${pts[0].y} `;
                for (let i = 1; i < pts.length - 1; i++) {
                  const xc = (pts[i].x + pts[i + 1].x) / 2;
                  const yc = (pts[i].y + pts[i + 1].y) / 2;
                  pathD += `Q ${pts[i].x} ${pts[i].y}, ${xc} ${yc} `;
                }
                const last = pts[pts.length - 1];
                pathD += `L ${last.x} ${last.y}`;
                const mid = pts[Math.floor(pts.length / 2)];
                labelX = mid.x;
                labelY = mid.y;
              } else {
                // Curved arc with perpendicular offset
                const dx = v.x - u.x;
                const dy = v.y - u.y;
                const len = Math.sqrt(dx * dx + dy * dy) || 1;
                const nx = -dy / len;
                const ny = dx / len;
                const curveOffset = 18;
                const ctrlX = labelX + nx * curveOffset;
                const ctrlY = labelY + ny * curveOffset;
                pathD = `M ${u.x} ${u.y} Q ${ctrlX} ${ctrlY} ${v.x} ${v.y}`;
                labelX = ctrlX;
                labelY = ctrlY;
              }

              const labelWidth = Math.max(20, edge.label.length * 8 + 8);

              return (
                <g key={`edge-${idx}`}>
                  <path
                    d={pathD}
                    className={`svg-edge-path ${isActive ? 'active' : ''}`}
                    stroke={strokeColor}
                    strokeWidth={strokeWidth}
                    markerEnd={markerId}
                  />
                  <rect
                    x={labelX - labelWidth / 2}
                    y={labelY - 8}
                    width={labelWidth}
                    height={16}
                    rx={2}
                    className="svg-edge-label-bg"
                  />
                  <text x={labelX} y={labelY + 1} className="svg-edge-label-text">
                    {edge.label}
                  </text>
                </g>
              );
            })}

            {/* Render States (Nodes) */}
            {states.map((s) => {
              const pos = layout.coords[s.id];
              if (!pos) return null;

              const isStart = s.is_start || automaton.start_state === s.id;
              const isAccepting = s.is_accepting;
              const isActive = String(activeStateId) === String(s.id);

              return (
                <g
                  key={s.id}
                  className={`svg-state-group ${isActive ? 'active' : ''}`}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onMouseEnter={() => setHoveredState(s.id)}
                  onMouseLeave={() => setHoveredState(null)}
                  tabIndex={0}
                  role="button"
                  aria-label={`State ${s.label || s.id}${isStart ? ', start state' : ''}${isAccepting ? ', accepting state' : ''}`}
                >
                  {/* Start state incoming arrow */}
                  {isStart && (
                    <g className="svg-start-arrow">
                      <path d="M -46 0 L -25 0" stroke="var(--ink-slate)" strokeWidth="2" />
                      <path d="M -32 -5 L -25 0 L -32 5" fill="var(--ink-slate)" />
                    </g>
                  )}

                  {/* Outer accepting ring (double ring for non-color identification) */}
                  {isAccepting && (
                    <circle
                      r={layout.nodeRadius + 4.5}
                      className="svg-state-circle accepting-outer"
                    />
                  )}

                  {/* Core State Circle */}
                  <circle
                    r={layout.nodeRadius}
                    className="svg-state-circle"
                  />

                  {/* State Monospace Label */}
                  <text className="svg-state-label">
                    {s.label || s.id}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      )}
    </div>
  );
}

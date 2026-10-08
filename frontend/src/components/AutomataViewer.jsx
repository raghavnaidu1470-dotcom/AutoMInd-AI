import React, { useMemo } from 'react';

export default function AutomataViewer({
  automaton,
  activeTab,
  setActiveTab,
  activeStateId,
  activeTransition,
  xaiExplanation,
  showHeatmap,
  setShowHeatmap,
}) {
  const states = automaton?.states || [];
  const transitions = automaton?.transitions || [];

  // Calculate layout coordinates for states in SVG canvas (auto-scales for large automata)
  const layout = useMemo(() => {
    const n = states.length;
    // Scale canvas dynamically for large automata so nodes don't overlap
    const width = Math.max(680, n * 55);
    const height = Math.max(360, n > 8 ? 440 : 360);
    const padding = 70;
    const coords = {};

    if (n === 0) return { coords, width, height, nodeRadius: 21 };

    const nodeRadius = n > 12 ? 18 : 21;

    if (n <= 4) {
      // Horizontal linear layout with vertical jitter
      const stepX = (width - 2 * padding) / Math.max(n - 1, 1);
      states.forEach((s, idx) => {
        coords[s.id] = {
          x: padding + idx * stepX,
          y: height / 2 + (idx % 2 === 1 ? -25 : 25),
        };
      });
    } else {
      // Circular / elliptical layout with ample radius
      const cx = width / 2;
      const cy = height / 2;
      const rx = (width - 2 * padding) / 2;
      const ry = (height - 2 * padding) / 2;
      states.forEach((s, idx) => {
        const angle = (2 * Math.PI * idx) / n - Math.PI / 2;
        coords[s.id] = {
          x: cx + rx * Math.cos(angle),
          y: cy + ry * Math.sin(angle),
        };
      });
    }

    return { coords, width, height, nodeRadius };
  }, [states]);

  // Node importance lookup
  const nodeImportance = xaiExplanation?.node_importance || {};

  // Edge importance lookup
  const edgeImportanceMap = useMemo(() => {
    const map = {};
    (xaiExplanation?.edge_importance || []).forEach((e) => {
      const key = `${e.from_state}->${e.to_state}:${e.symbol}`;
      map[key] = e.importance;
    });
    return map;
  }, [xaiExplanation]);

  const getNodeColor = (stateId, isAccepting) => {
    if (showHeatmap && nodeImportance[stateId] !== undefined) {
      const imp = nodeImportance[stateId];
      if (imp > 0.8) return '#f43f5e'; // High importance: Rose
      if (imp > 0.5) return '#f59e0b'; // Moderate: Amber
      if (imp > 0.25) return '#06b6d4'; // Noticeable: Cyan
    }
    return isAccepting ? '#10b981' : '#38bdf8';
  };

  return (
    <div className="glass-panel diagram-card" id="automata-viewer-card">
      {/* Tab Controls & View Mode */}
      <div className="tabs-header">
        <div className="tab-buttons">
          <button
            className={`tab-btn ${activeTab === 'minimized_dfa' ? 'active' : ''}`}
            onClick={() => setActiveTab('minimized_dfa')}
          >
            Minimized DFA
          </button>
          <button
            className={`tab-btn ${activeTab === 'dfa' ? 'active' : ''}`}
            onClick={() => setActiveTab('dfa')}
          >
            DFA
          </button>
          <button
            className={`tab-btn ${activeTab === 'nfa' ? 'active' : ''}`}
            onClick={() => setActiveTab('nfa')}
          >
            NFA (Thompson)
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            id="btn-toggle-heatmap"
            className="btn-secondary"
            style={{
              borderColor: showHeatmap ? 'var(--accent-rose)' : 'var(--border-subtle)',
              color: showHeatmap ? '#fda4af' : 'var(--text-secondary)',
            }}
            onClick={() => setShowHeatmap(!showHeatmap)}
          >
            <span style={{ fontSize: '0.9rem' }}>🔥</span> {showHeatmap ? 'Heatmap: On' : 'XAI Heatmap'}
          </button>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {states.length} states | {transitions.length} transitions
          </span>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="svg-canvas-wrapper" id="svg-canvas-container">
        <svg
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          style={{
            width: layout.width > 680 ? `${layout.width}px` : '100%',
            height: '100%',
            minHeight: '360px',
            maxHeight: layout.height > 360 ? '460px' : '420px',
          }}
        >
          <defs>
            {/* Arrow marker for standard directed edges */}
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="26"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
            </marker>

            {/* Active traversal arrow marker */}
            <marker
              id="arrow-active"
              viewBox="0 0 10 10"
              refX="26"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
            </marker>

            {/* XAI High-importance arrow marker */}
            <marker
              id="arrow-xai"
              viewBox="0 0 10 10"
              refX="26"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#f43f5e" />
            </marker>
          </defs>

          {/* Render Transitions (Edges) */}
          {transitions.map((t, idx) => {
            const u = layout.coords[t.from_state];
            const v = layout.coords[t.to_state];
            if (!u || !v) return null;

            const isSelfLoop = t.from_state === t.to_state;
            const edgeKey = `${t.from_state}->${t.to_state}:${t.symbol}`;
            const imp = edgeImportanceMap[edgeKey] || 0;
            const isActive =
              activeTransition &&
              activeTransition.from_state === t.from_state &&
              activeTransition.to_state === t.to_state &&
              activeTransition.symbol === t.symbol;

            const strokeColor = isActive
              ? '#10b981'
              : showHeatmap && imp > 0.6
              ? '#f43f5e'
              : showHeatmap && imp > 0.3
              ? '#f59e0b'
              : '#475569';

            const strokeWidth = isActive ? 3.5 : showHeatmap && imp > 0.6 ? 3 : 1.8;
            const markerId = isActive ? 'url(#arrow-active)' : showHeatmap && imp > 0.6 ? 'url(#arrow-xai)' : 'url(#arrow)';

            if (isSelfLoop) {
              // Self loop curve on top
              const loopPath = `M ${u.x - 12} ${u.y - 18} C ${u.x - 30} ${u.y - 65}, ${u.x + 30} ${u.y - 65}, ${u.x + 12} ${u.y - 18}`;
              return (
                <g key={`trans-${idx}`} className={`svg-transition-edge ${isActive ? 'active-traversal' : ''}`}>
                  <path
                    d={loopPath}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={strokeWidth}
                    markerEnd={markerId}
                  />
                  <rect
                    x={u.x - 12}
                    y={u.y - 62}
                    width="24"
                    height="16"
                    rx="4"
                    fill="rgba(15, 23, 42, 0.9)"
                  />
                  <text
                    x={u.x}
                    y={u.y - 50}
                    textAnchor="middle"
                    fill="#e2e8f0"
                    fontSize="11"
                    fontFamily="var(--font-mono)"
                    fontWeight="bold"
                  >
                    {t.symbol}
                  </text>
                </g>
              );
            }

            // Direct line / slight arc
            const midX = (u.x + v.x) / 2;
            const midY = (u.y + v.y) / 2;
            // Add curve offset to prevent overlapping reverse edges
            const dx = v.x - u.x;
            const dy = v.y - u.y;
            const len = Math.sqrt(dx * dx + dy * dy) || 1;
            const nx = -dy / len;
            const ny = dx / len;
            const curveOffset = 18;
            const ctrlX = midX + nx * curveOffset;
            const ctrlY = midY + ny * curveOffset;

            const pathD = `M ${u.x} ${u.y} Q ${ctrlX} ${ctrlY} ${v.x} ${v.y}`;

            return (
              <g key={`trans-${idx}`} className={`svg-transition-edge ${isActive ? 'active-traversal' : ''}`}>
                <path
                  d={pathD}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  markerEnd={markerId}
                />
                <rect
                  x={ctrlX - 10}
                  y={ctrlY - 10}
                  width="20"
                  height="16"
                  rx="4"
                  fill="rgba(15, 23, 42, 0.85)"
                />
                <text
                  x={ctrlX}
                  y={ctrlY + 2}
                  textAnchor="middle"
                  fill="#e2e8f0"
                  fontSize="11"
                  fontFamily="var(--font-mono)"
                  fontWeight="bold"
                >
                  {t.symbol}
                </text>
              </g>
            );
          })}

          {/* Render States (Nodes) */}
          {states.map((s) => {
            const pos = layout.coords[s.id];
            if (!pos) return null;

            const isActive = activeStateId === s.id;
            const isStart = s.is_start || automaton.start_state === s.id;
            const isAccepting = s.is_accepting;
            const nodeColor = getNodeColor(s.id, isAccepting);

            return (
              <g
                key={s.id}
                className={`svg-state-node ${isActive ? 'active-step' : ''}`}
                transform={`translate(${pos.x}, ${pos.y})`}
              >
                {/* Start State Indicator Arrow */}
                {isStart && (
                  <path
                    d="M -50 0 L -30 0 M -38 -6 L -30 0 L -38 6"
                    stroke="#38bdf8"
                    strokeWidth="2.5"
                    fill="none"
                  />
                )}

                {/* Outer accepting ring if accepting */}
                {isAccepting && (
                  <circle
                    r={layout.nodeRadius + 5}
                    fill="none"
                    stroke={nodeColor}
                    strokeWidth="1.8"
                    opacity="0.9"
                  />
                )}

                {/* Main state circle */}
                <circle
                  r={layout.nodeRadius}
                  fill="rgba(15, 23, 42, 0.95)"
                  stroke={nodeColor}
                  strokeWidth={isActive ? '4' : '2'}
                  style={{
                    filter: isActive
                      ? 'drop-shadow(0 0 10px rgba(16, 185, 129, 0.8))'
                      : showHeatmap && (nodeImportance[s.id] || 0) > 0.7
                      ? 'drop-shadow(0 0 8px rgba(244, 63, 94, 0.6))'
                      : 'none',
                  }}
                />

                {/* State Label */}
                <text
                  textAnchor="middle"
                  dy="4"
                  fill="#f8fafc"
                  fontFamily="var(--font-mono)"
                  fontSize="12"
                  fontWeight="600"
                >
                  {s.label || s.id}
                </text>

                {/* XAI score tag if heatmap is active */}
                {showHeatmap && nodeImportance[s.id] !== undefined && (
                  <text
                    textAnchor="middle"
                    dy="36"
                    fill="#f43f5e"
                    fontSize="10"
                    fontFamily="var(--font-mono)"
                    fontWeight="700"
                  >
                    {nodeImportance[s.id].toFixed(2)}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

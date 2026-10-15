import React, { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import { buildAutomatonLayout, LARGE_INPUT_THRESHOLD } from '../utils/dagreLayout.js';
import { exportSvgFile, exportPngFile } from '../utils/diagramExport.js';
import MinimizationModal from './MinimizationModal.jsx';

export default function AutomataViewer({
  automaton,
  activeStage,
  setActiveStage,
  automataBundle,
  activeStateId,
  activeStates = [],
  activeTransition,
  xaiExplanation,
  showEdgeImportance,
  setShowEdgeImportance,
  sidebarVisible = true,
  onToggleSidebar,
}) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState({ x: 0, y: 0 });
  const [hoveredState, setHoveredState] = useState(null);
  const [selectedState, setSelectedState] = useState(null);
  const [viewAsTable, setViewAsTable] = useState(false);
  const [showMinimizationModal, setShowMinimizationModal] = useState(false);

  const containerRef = useRef(null);
  const svgRef = useRef(null);

  const states = automaton?.states || [];
  const transitions = automaton?.transitions || [];

  // Build hierarchical layout coordinates
  const layout = useMemo(() => {
    return buildAutomatonLayout(automaton, { nodeRadius: 22 });
  }, [automaton]);

  // Reset pan/zoom on automaton change
  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setHoveredState(null);
    setSelectedState(null);
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

  // Export handlers with high-resolution, unclipped standalone styling
  const handleExportSVG = () => {
    if (!svgRef.current) return;
    const filename = `${automaton?.name || automaton?.type || 'automaton'}.svg`;
    exportSvgFile(svgRef.current, layout, automaton, filename);
  };

  const handleExportPNG = () => {
    if (!svgRef.current) return;
    const filename = `${automaton?.name || automaton?.type || 'automaton'}.png`;
    exportPngFile(svgRef.current, layout, automaton, filename, 3); // 3x high-DPI resolution
  };

  const handleExportJSON = () => {
    if (!automaton) return;
    const blob = new Blob([JSON.stringify(automaton, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${automaton?.name || automaton?.type || 'automaton'}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Find origin NFA states / merged states for the currently hovered state
  const hoveredStateData = useMemo(() => {
    if (!hoveredState) return null;
    return states.find((s) => s.id === hoveredState) || null;
  }, [hoveredState, states]);

  // List of active states (handles both single activeStateId and array of activeStates)
  const activeList = useMemo(() => {
    if (Array.isArray(activeStates) && activeStates.length > 0) {
      return activeStates.map(String);
    }
    if (activeStateId !== undefined && activeStateId !== null) {
      return [String(activeStateId)];
    }
    return [];
  }, [activeStates, activeStateId]);

  return (
    <div className="drawing-area" id="drawing-area" role="region" aria-label="Automaton railway schematic">
      {/* Representation Selector Tabs Bar */}
      <div className="automata-representation-bar" role="tablist" aria-label="Automaton representation">
        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
          {setActiveStage && (
            <>
              <button
                type="button"
                className={`rep-tab ${activeStage === 'nfa' ? 'active' : ''}`}
                onClick={() => setActiveStage('nfa')}
                role="tab"
                aria-selected={activeStage === 'nfa'}
              >
                <span>NFA (Thompson)</span>
                <span className="rep-tab-count">{automataBundle?.nfa?.states?.length ?? 0} states</span>
              </button>

              <button
                type="button"
                className={`rep-tab ${activeStage === 'dfa' ? 'active' : ''}`}
                onClick={() => setActiveStage('dfa')}
                role="tab"
                aria-selected={activeStage === 'dfa'}
              >
                <span>DFA (Subset)</span>
                <span className="rep-tab-count">{automataBundle?.dfa?.states?.length ?? 0} states</span>
              </button>

              <button
                type="button"
                className={`rep-tab ${activeStage === 'minimized_dfa' ? 'active' : ''}`}
                onClick={() => setActiveStage('minimized_dfa')}
                role="tab"
                aria-selected={activeStage === 'minimized_dfa'}
              >
                <span>Minimized DFA</span>
                <span className="rep-tab-count">{automataBundle?.minimized_dfa?.states?.length ?? 0} states</span>
              </button>
            </>
          )}

          {/* Minimization Comparison Button */}
          {automataBundle?.dfa && automataBundle?.minimized_dfa && (
            <button
              type="button"
              className="btn-quiet-pill"
              onClick={() => setShowMinimizationModal(true)}
              style={{ fontSize: '11px', marginLeft: '0.3rem' }}
            >
              ⚖️ Compare Minimization
            </button>
          )}
        </div>

        {/* Current Automaton Meta Label */}
        <div style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span>
            Showing: <strong>{automaton?.type || 'Automaton'}</strong> ({states.length} states, {transitions.length} transitions)
          </span>
        </div>
      </div>

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
          {viewAsTable ? 'View diagram' : 'View table'}
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

        {/* Export Group */}
        <button type="button" className="btn-quiet" onClick={handleExportSVG} title="Download vector SVG diagram">
          SVG
        </button>
        <button type="button" className="btn-quiet" onClick={handleExportPNG} title="Download high-resolution 3× PNG">
          PNG
        </button>
        <button type="button" className="btn-quiet" onClick={handleExportJSON} title="Download canonical JSON schema">
          JSON
        </button>

        {onToggleSidebar && (
          <>
            <span style={{ width: '1px', background: 'var(--ink-border)', margin: '0 0.2rem' }} />
            <button
              type="button"
              className="btn-quiet"
              id="btn-toolbar-toggle-sidebar"
              onClick={onToggleSidebar}
              aria-label={sidebarVisible ? 'Hide sidebar' : 'Open sidebar'}
              aria-expanded={sidebarVisible}
              title={sidebarVisible ? 'Collapse sidebar' : 'Open sidebar'}
            >
              {sidebarVisible ? 'Hide sidebar' : 'Open sidebar'}
            </button>
          </>
        )}
      </div>

      {/* Persistent Reopen Sidebar Button when sidebar is collapsed */}
      {!sidebarVisible && onToggleSidebar && (
        <button
          type="button"
          id="btn-persistent-open-sidebar"
          className="persistent-open-sidebar-btn"
          onClick={onToggleSidebar}
          aria-label="Open sidebar"
          aria-expanded={false}
          title="Open sidebar: Trace log and Explainability"
        >
          <span aria-hidden="true" style={{ marginRight: '4px' }}>◀</span> Open sidebar
        </button>
      )}

      {/* Large Input Warning Banner */}
      {layout.isLarge && (
        <div
          style={{
            position: 'absolute',
            top: '5.2rem',
            left: '1rem',
            right: '1rem',
            background: 'var(--amber-tint)',
            border: '1px solid var(--amber-signal)',
            padding: '0.4rem 0.8rem',
            fontSize: 'var(--text-xs)',
            zIndex: 10,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
          role="note"
        >
          <span>
            Large automaton ({states.length} states). Simplified rendering active for performance.
          </span>
          <button
            type="button"
            className="btn-quiet"
            onClick={() => setViewAsTable(true)}
            style={{ fontSize: 'var(--text-xs)' }}
          >
            Switch to transition table
          </button>
        </div>
      )}

      {/* Hovered State Subsets Info Pill */}
      {hoveredStateData?.metadata?.nfa_subset && (
        <div
          className="hover-subset-pill"
          style={{
            position: 'absolute',
            bottom: selectedState ? '140px' : '0.85rem',
            left: '0.85rem',
            zIndex: 10,
            background: 'var(--paper-panel)',
            border: '1px solid var(--ink-border)',
            borderRadius: 'var(--radius-control)',
            padding: '0.35rem 0.65rem',
            fontSize: 'var(--text-xs)',
            boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
          }}
          role="status"
        >
          <strong>State {hoveredStateData.id}:</strong>{' '}
          <span style={{ color: 'var(--ink-secondary)' }}>
            Corresponds to NFA states: {'{' + (hoveredStateData.metadata.nfa_subset || []).join(', ') + '}'}
          </span>
        </div>
      )}

      {/* Selected State Inspector Card (Click to inspect) */}
      {selectedState && (
        <div className="state-inspector-drawer" role="region" aria-label="State details">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <strong style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
                State {selectedState.label || selectedState.id}
              </strong>
              {selectedState.is_start && <span className="state-badge-start">Start State</span>}
              {selectedState.is_accepting ? (
                <span className="state-badge-accept">Accepting State (Double Ring)</span>
              ) : (
                <span className="state-badge-nonaccept">Non-Accepting</span>
              )}
            </div>
            <button
              type="button"
              className="btn-quiet"
              onClick={() => setSelectedState(null)}
              aria-label="Close state inspector"
              style={{ padding: '0.1rem 0.35rem' }}
            >
              ✕
            </button>
          </div>

          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-slate)', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            {selectedState.metadata?.nfa_subset && (
              <div>
                <strong>Corresponds to NFA states: </strong>
                <code>{'{' + selectedState.metadata.nfa_subset.join(', ') + '}'}</code>
              </div>
            )}
            {selectedState.metadata?.merged_states && (
              <div>
                <strong>Merged from DFA states: </strong>
                <code>{'{' + selectedState.metadata.merged_states.join(', ') + '}'}</code>
              </div>
            )}
            <div>
              <strong>Outgoing transitions: </strong>
              <span>
                {transitions
                  .filter((t) => t.from_state === selectedState.id)
                  .map((t) => `'${t.symbol}' → ${t.to_state}`)
                  .join(', ') || 'None (dead end)'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Table View Toggle */}
      {viewAsTable ? (
        <div className="automata-table-view-container" style={{ padding: '1rem', overflowY: 'auto' }}>
          <h4 style={{ margin: '0 0 0.5rem 0', fontSize: 'var(--text-sm)' }}>
            Transition Table for {automaton?.name || automaton?.type}
          </h4>
          <table className="syntax-table">
            <thead>
              <tr>
                <th>State ID</th>
                <th>Type</th>
                <th>Underlying NFA Subset</th>
                {automaton?.alphabet?.map((sym) => (
                  <th key={sym}>On '{sym}'</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {states.map((s) => (
                <tr key={s.id} className={activeList.includes(String(s.id)) ? 'active-row' : ''}>
                  <td>
                    <strong style={{ fontFamily: 'var(--font-mono)' }}>{s.label || s.id}</strong>
                  </td>
                  <td>
                    {s.is_start ? 'Start ' : ''}
                    {s.is_accepting ? 'Accepting' : 'Normal'}
                  </td>
                  <td>
                    <code>{'{' + (s.metadata?.nfa_subset || [s.id]).join(', ') + '}'}</code>
                  </td>
                  {automaton?.alphabet?.map((sym) => {
                    const matchTrans = transitions.filter((t) => t.from_state === s.id && t.symbol === sym);
                    return (
                      <td key={sym}>
                        {matchTrans.length > 0 ? (
                          matchTrans.map((t) => t.to_state).join(', ')
                        ) : (
                          <span style={{ color: 'var(--ink-secondary)' }}>—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        /* Interactive SVG Canvas */
        <div
          ref={containerRef}
          className="canvas-container"
          style={{ width: '100%', height: '100%', cursor: isPanning ? 'grabbing' : 'grab' }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        >
          <svg
            ref={svgRef}
            id="automaton-svg"
            className="automata-svg"
            viewBox={`0 0 ${layout.width || 600} ${layout.height || 400}`}
            style={{
              width: '100%',
              height: '100%',
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: 'center center',
            }}
          >
            <defs>
              <pattern id="dot-grid" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
                <circle cx="2" cy="2" r="1" fill="#cbd5e1" opacity="0.4" />
              </pattern>
              <marker id="arrowhead" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
                <path d="M 0 1.5 L 8 4.5 L 0 7.5 Z" fill="var(--ink-slate)" />
              </marker>
              <marker id="arrowhead-active" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
                <path d="M 0 1.5 L 8 4.5 L 0 7.5 Z" fill="var(--amber-signal)" />
              </marker>
            </defs>

            {/* Grid Background */}
            <rect width="100%" height="100%" fill="url(#dot-grid)" />

            {/* Render Transitions (Edges) */}
            {layout.edges.map((edge, idx) => {
              const fromId = edge.from ?? edge.from_state;
              const toId = edge.to ?? edge.to_state;
              const u = layout.coords[fromId];
              const v = layout.coords[toId];
              if (!u || !v) return null;

              const isSelfLoop = fromId === toId;
              const isActive =
                activeTransition &&
                String(activeTransition.from_state) === String(fromId) &&
                String(activeTransition.to_state) === String(toId) &&
                String(activeTransition.symbol) === String(edge.label);

              const edgeKey = `${fromId}->${toId}:${edge.label}`;
              const importance = edgeImportanceMap[edgeKey] || 0;

              let strokeColor = isActive ? 'var(--amber-signal)' : 'var(--ink-slate)';
              let strokeWidth = isActive ? 3 : 1.75;
              let markerId = isActive ? 'url(#arrowhead-active)' : 'url(#arrowhead)';

              if (showEdgeImportance && importance > 0) {
                strokeWidth = Math.max(1.75, importance * 5);
                strokeColor = `rgba(217, 119, 6, ${Math.max(0.4, importance)})`;
              }

              let pathD = '';
              let labelX = (u.x + v.x) / 2;
              let labelY = (u.y + v.y) / 2;

              if (isSelfLoop) {
                const r = layout.nodeRadius;
                const loopHeight = 38;
                pathD = `M ${u.x - 10} ${u.y - r} C ${u.x - 25} ${u.y - r - loopHeight}, ${u.x + 25} ${u.y - r - loopHeight}, ${u.x + 10} ${u.y - r}`;
                labelX = u.x;
                labelY = u.y - r - loopHeight + 8;
              } else {
                const dx = v.x - u.x;
                const dy = v.y - u.y;
                const dist = Math.hypot(dx, dy) || 1;
                const nx = -dy / dist;
                const ny = dx / dist;
                const curveOffset = 18;

                const ctrlX = labelX + nx * curveOffset;
                const ctrlY = labelY + ny * curveOffset;
                pathD = `M ${u.x} ${u.y} Q ${ctrlX} ${ctrlY} ${v.x} ${v.y}`;
                labelX = ctrlX;
                labelY = ctrlY;
              }

              const labelWidth = Math.max(22, edge.label.length * 8 + 8);

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
              const isActive = activeList.includes(String(s.id));
              const isDead = s.id.toLowerCase().includes('dead') || s.label?.toLowerCase().includes('dead');
              const isSelected = selectedState?.id === s.id;

              return (
                <g
                  key={s.id}
                  className={`svg-state-group ${isActive ? 'active' : ''} ${isDead ? 'dead' : ''} ${isSelected ? 'selected' : ''}`}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onMouseEnter={() => setHoveredState(s.id)}
                  onMouseLeave={() => setHoveredState(null)}
                  onClick={() => setSelectedState(s)}
                  tabIndex={0}
                  role="button"
                  aria-label={`State ${s.label || s.id}${isStart ? ', start state' : ''}${isAccepting ? ', accepting state' : ''}${isActive ? ', active' : ''}`}
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
                    className={`svg-state-circle ${isActive ? 'active' : ''}`}
                    strokeDasharray={isDead ? '3 3' : undefined}
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

      {/* Hopcroft Minimization Comparison Modal */}
      <MinimizationModal
        isOpen={showMinimizationModal}
        onClose={() => setShowMinimizationModal(false)}
        dfa={automataBundle?.dfa}
        minDfa={automataBundle?.minimized_dfa}
      />
    </div>
  );
}

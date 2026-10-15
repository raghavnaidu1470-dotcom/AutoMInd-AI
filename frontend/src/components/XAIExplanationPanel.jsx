import React, { useState } from 'react';

const FEATURE_NAME_MAP = {
  is_cyclic: 'Cyclic paths detected',
  has_cycle: 'Cyclic path present',
  avg_branching_factor: 'Average branching factor',
  branching_factor: 'Branching factor',
  is_deterministic: 'Deterministic structure',
  start_to_accept_path_len: 'Distance from start to accepting state',
  path_len: 'Path traversal length',
  max_out_degree: 'Maximum outgoing transitions per state',
  num_states: 'Total state count',
  num_transitions: 'Total transition count',
  num_accepting_states: 'Accepting state count',
  density: 'Transition density',
  alphabet_size: 'Alphabet cardinality',
};

function formatFeatureName(rawName) {
  if (FEATURE_NAME_MAP[rawName]) return FEATURE_NAME_MAP[rawName];
  return rawName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function XAIExplanationPanel({
  xaiExplanation,
  loading,
  showEdgeImportance,
  setShowEdgeImportance,
  isAdvancedMode = false,
}) {
  const [showAdvancedDiagnostics, setShowAdvancedDiagnostics] = useState(isAdvancedMode);

  if (loading) {
    return (
      <div style={{ padding: '0.85rem', fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)' }}>
        Computing explanation and state reachability...
      </div>
    );
  }

  if (!xaiExplanation) {
    return (
      <div style={{ padding: '0.85rem', fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)' }}>
        Run a candidate string to inspect model explanation analytics.
      </div>
    );
  }

  const {
    predicted_accepted,
    confidence = 0.0,
    edge_importance = [],
    feature_attributions = {},
    explanation_summary,
  } = xaiExplanation;

  // Most influential transitions (top 4)
  const topEdges = edge_importance.slice(0, 4);

  // Plain lead sentence
  const leadSentence = explanation_summary || 
    `The automaton ${predicted_accepted ? 'accepts' : 'rejects'} the candidate string based on deterministic state transition traversal.`;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      {/* Plain Lead Sentence Callout */}
      <div className="engineering-callout">
        <div className="engineering-callout-title">Decision summary</div>
        <p style={{ margin: 0, color: 'var(--ink-slate)', lineHeight: 1.45, fontSize: 'var(--text-xs)' }}>
          {leadSentence}
        </p>
      </div>

      {/* Progressive Disclosure Toggle for Advanced GNN Metrics */}
      <div>
        <button
          type="button"
          className="btn-quiet"
          style={{ fontSize: '11px', color: 'var(--ink-secondary)', padding: '0.2rem 0.4rem' }}
          onClick={() => setShowAdvancedDiagnostics(!showAdvancedDiagnostics)}
        >
          {showAdvancedDiagnostics ? '▼ Hide GNN & SHAP Internals' : '▶ Inspect GNN & SHAP Internals (Optional)'}
        </button>
      </div>

      {showAdvancedDiagnostics && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', padding: '0.65rem', background: 'var(--paper-subtle)', borderRadius: 'var(--radius-control)' }}>
          {/* Model Confidence & Edge Weight Toggle */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>Heuristic confidence: </span>
              <strong style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{(confidence * 100).toFixed(1)}%</strong>
            </div>

            {setShowEdgeImportance && (
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '11px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={Boolean(showEdgeImportance)}
                  onChange={(e) => setShowEdgeImportance(e.target.checked)}
                />
                Edge weights
              </label>
            )}
          </div>

          {/* Most Influential Transitions */}
          <div>
            <h4 style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--ink-secondary)', margin: '0 0 0.3rem 0' }}>
              Influential Transitions
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              {topEdges.length === 0 ? (
                <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>
                  No critical edge weights recorded.
                </span>
              ) : (
                topEdges.map((e, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      padding: '0.2rem 0.35rem',
                      background: '#ffffff',
                      border: '1px solid var(--ink-border-light)',
                      borderRadius: '2px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                    }}
                  >
                    <span>
                      {e.from_state} --({e.symbol})--&gt; {e.to_state}
                    </span>
                    <strong>{(e.importance * 100).toFixed(0)}%</strong>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Feature-Level Attributions */}
          {Object.keys(feature_attributions).length > 0 && (
            <div>
              <h4 style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--ink-secondary)', margin: '0 0 0.3rem 0' }}>
                Structural Feature Attributions
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                {Object.entries(feature_attributions).slice(0, 5).map(([feat, score]) => (
                  <div key={feat} style={{ fontSize: '11px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.1rem' }}>
                      <span style={{ color: 'var(--ink-slate)' }}>{formatFeatureName(feat)}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                        {(score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div style={{ height: '3px', background: 'var(--ink-border-light)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${Math.min(score * 200, 100)}%`,
                          backgroundColor: 'var(--ink-slate)',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Honest Disclaimer */}
          <div style={{ fontSize: '10px', color: 'var(--ink-secondary)', lineHeight: 1.35 }}>
            <strong>Academic note:</strong> Graph message passing and SHAP feature attributions provide statistical heuristics. The formal automata simulator—not the neural model—always decides whether a string is accepted or rejected.
          </div>
        </div>
      )}
    </div>
  );
}

import React from 'react';

export default function XAIExplanationPanel({ xaiExplanation, loading }) {
  if (loading) {
    return (
      <div className="glass-panel xai-panel" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-secondary)' }}>Calculating GNN & SHAP Attributions...</p>
      </div>
    );
  }

  if (!xaiExplanation) {
    return (
      <div className="glass-panel xai-panel">
        <p style={{ color: 'var(--text-muted)' }}>Run a string execution to view explainability analytics.</p>
      </div>
    );
  }

  const {
    predicted_accepted,
    confidence,
    edge_importance = [],
    feature_attributions = {},
    critical_subgraph,
    explanation_summary,
  } = xaiExplanation;

  const topEdges = edge_importance.slice(0, 4);

  return (
    <div className="glass-panel xai-panel" id="xai-explanation-panel">
      {/* Header with Title & Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Explainable AI Analytics</h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            GNNExplainer + SHAP Attribution
          </span>
        </div>
        <span
          className="badge"
          style={{
            background: predicted_accepted ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
            color: predicted_accepted ? '#34d399' : '#fda4af',
            border: `1px solid ${predicted_accepted ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
          }}
        >
          {predicted_accepted ? 'GNN: ACCEPTED' : 'GNN: REJECTED'}
        </span>
      </div>

      {/* Metrics Row */}
      <div className="metric-row">
        <div className="metric-box">
          <div className="metric-label">Model Confidence</div>
          <div className="metric-val" style={{ color: 'var(--accent-cyan)' }}>
            {(confidence * 100).toFixed(1)}%
          </div>
          <div className="bar-track">
            <div className="bar-fill bar-fill-cyan" style={{ width: `${confidence * 100}%` }} />
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Critical Subgraph</div>
          <div className="metric-val" style={{ color: 'var(--accent-violet)' }}>
            {critical_subgraph?.nodes?.length || 0} states
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
            {critical_subgraph?.edges?.length || 0} critical transitions
          </div>
        </div>
      </div>

      {/* Natural Language Rationale Card */}
      <div
        className="glass-card"
        style={{ padding: '0.85rem 1rem', borderLeft: '3px solid var(--accent-cyan)' }}
      >
        <div style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--accent-cyan)', marginBottom: '0.25rem' }}>
          Decision Summary
        </div>
        <p style={{ fontSize: '0.85rem', lineHeight: '1.4', color: 'var(--text-secondary)' }}>
          {explanation_summary}
        </p>
      </div>

      {/* Top Edge Importance (GNNExplainer) */}
      <div>
        <h3 style={{ fontSize: '0.85rem', fontWeight: '600', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
          Key Transition Paths (GNNExplainer)
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {topEdges.map((e, idx) => (
            <div
              key={idx}
              className="glass-card"
              style={{ padding: '0.6rem 0.85rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                <span>
                  <strong style={{ color: '#fff' }}>{e.from_state}</strong>
                  <span style={{ color: 'var(--accent-cyan)' }}> --({e.symbol})--&gt; </span>
                  <strong style={{ color: '#fff' }}>{e.to_state}</strong>
                </span>
                <span style={{ color: e.importance > 0.8 ? '#fda4af' : 'var(--text-secondary)' }}>
                  {(e.importance * 100).toFixed(0)}% imp.
                </span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{
                    width: `${e.importance * 100}%`,
                    background: e.importance > 0.8 ? 'linear-gradient(90deg, #f43f5e, #fb7185)' : 'linear-gradient(90deg, #0284c7, var(--accent-cyan))',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* SHAP Feature-Level Attributions */}
      <div>
        <h3 style={{ fontSize: '0.85rem', fontWeight: '600', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
          Feature Attributions (SHAP)
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          {Object.entries(feature_attributions).map(([feat, score]) => (
            <div key={feat} style={{ fontSize: '0.78rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                <span style={{ textTransform: 'capitalize' }}>{feat.replace(/_/g, ' ')}</span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>{(score * 100).toFixed(1)}%</span>
              </div>
              <div className="bar-track">
                <div className="bar-fill bar-fill-violet" style={{ width: `${Math.min(score * 200, 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

import React from 'react';

export default function Header({ backendStatus }) {
  const isConnected = backendStatus?.status === 'healthy';

  return (
    <header className="app-header" id="app-header">
      <div className="brand-wrapper">
        <div className="brand-icon">
          <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#fff' }}>Ψ</span>
        </div>
        <div>
          <h1 className="brand-title">AutoMind AI</h1>
          <p className="brand-tagline">Explainable Formal Language Recognition & Automata Analysis</p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Module division indicators */}
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <span className="badge badge-member-a" title="Member A: Regex Parser, Thompson NFA, Subset DFA, Hopcroft Minimization">
            Member A: Automata
          </span>
          <span className="badge badge-member-b" title="Member B: PyG Graphs, GNN Model, GNNExplainer, SHAP">
            Member B: GNN & XAI
          </span>
          <span className="badge badge-member-c" title="Member C: FastAPI Orchestration, Storage, Interactive UI">
            Member C: API & UI
          </span>
        </div>

        {/* Backend health status badge */}
        <div
          id="status-indicator"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.3rem 0.75rem',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontFamily: 'var(--font-mono)',
            background: isConnected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
            border: `1px solid ${isConnected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
            color: isConnected ? '#34d399' : '#fbbf24',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isConnected ? '#10b981' : '#f59e0b',
              boxShadow: isConnected ? '0 0 8px #10b981' : '0 0 8px #f59e0b',
            }}
          />
          {isConnected ? 'API Live' : 'Offline / Standalone Preview'}
        </div>
      </div>
    </header>
  );
}

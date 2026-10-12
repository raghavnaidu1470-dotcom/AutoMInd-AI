import React, { useState } from 'react';
import { api } from '../services/api';

const PRESETS = [
  { label: '(a+)+$ (Exponential)', regex: '(a+)+$', risk: 'exponential' },
  { label: '(a|aa)+$ (Exponential)', regex: '(a|aa)+$', risk: 'exponential' },
  { label: '(a*)*b (Exponential)', regex: '(a*)*b', risk: 'exponential' },
  { label: 'a*a*b (Polynomial)', regex: 'a*a*b', risk: 'polynomial' },
  { label: '(a|b)*abb (Linear / Safe)', regex: '(a|b)*abb', risk: 'linear' },
];

export default function ReDoSGuardPanel({ onLoadIntoStudio }) {
  const [targetRegex, setTargetRegex] = useState('(a+)+$');
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [repairResult, setRepairResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [copiedAttack, setCopiedAttack] = useState(false);

  // Analyze regex
  const handleAnalyze = async (regexToAnalyze = targetRegex) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.analyzeReDoS(regexToAnalyze, true);
      setAnalysisResult(res);
      // Auto-trigger repair if vulnerable
      if (res.is_vulnerable) {
        handleRepair(regexToAnalyze);
      } else {
        setRepairResult(null);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  // Repair regex
  const handleRepair = async (regexToRepair = targetRegex) => {
    setLoading(true);
    try {
      const rep = await api.repairReDoS(regexToRepair, true);
      setRepairResult(rep);
    } catch (err) {
      console.error('Repair error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Select preset
  const handleSelectPreset = (presetRegex) => {
    setTargetRegex(presetRegex);
    handleAnalyze(presetRegex);
  };

  const riskClass = analysisResult?.risk_class;

  // Render highlighted spans in regex
  const renderHighlightedRegex = () => {
    if (!analysisResult) return targetRegex;
    const spans = analysisResult.highlighted_spans || [];
    if (spans.length === 0) {
      return (
        <span style={{ color: '#e2e8f0', fontFamily: 'var(--font-mono)' }}>
          {analysisResult.regex}
        </span>
      );
    }

    // Single or merged span highlighting
    const span = spans[0];
    const before = analysisResult.regex.slice(0, span.start);
    const highlighted = analysisResult.regex.slice(span.start, span.end);
    const after = analysisResult.regex.slice(span.end);

    return (
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.15rem' }}>
        <span style={{ color: '#94a3b8' }}>{before}</span>
        <span
          style={{
            background: 'rgba(239, 68, 68, 0.25)',
            border: '1px solid rgba(239, 68, 68, 0.8)',
            color: '#f87171',
            padding: '2px 6px',
            borderRadius: '4px',
            fontWeight: 700,
            boxShadow: '0 0 10px rgba(239, 68, 68, 0.3)',
          }}
          title={`Offending span [${span.start}..${span.end}]: ${span.fragment}`}
        >
          {highlighted}
        </span>
        <span style={{ color: '#94a3b8' }}>{after}</span>
      </span>
    );
  };

  // Copy attack string
  const handleCopyAttack = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedAttack(true);
    setTimeout(() => setCopiedAttack(false), 2000);
  };

  // Render before/after benchmark SVG chart
  const renderBenchmarkChart = () => {
    const beforePoints = repairResult?.before_benchmark?.points || analysisResult?.empirical_benchmark?.points || [];
    const afterPoints = repairResult?.after_benchmark?.points || [];

    if (beforePoints.length === 0) return null;

    const width = 560;
    const height = 220;
    const padding = { top: 25, right: 30, bottom: 35, left: 55 };

    const maxLen = Math.max(...beforePoints.map((p) => p.length), 30);
    const minLen = Math.min(...beforePoints.map((p) => p.length), 0);
    const maxTime = Math.max(
      ...beforePoints.map((p) => p.duration_ms),
      ...afterPoints.map((p) => p.duration_ms),
      50
    );

    const scaleX = (len) =>
      padding.left + ((len - minLen) / Math.max(maxLen - minLen, 1)) * (width - padding.left - padding.right);
    const scaleY = (time) =>
      height - padding.bottom - (time / Math.max(maxTime, 1)) * (height - padding.top - padding.bottom);

    const makePath = (points) => {
      if (!points || points.length === 0) return '';
      return points
        .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${scaleX(p.length)} ${scaleY(p.duration_ms)}`)
        .join(' ');
    };

    return (
      <div style={{ marginTop: '1rem', background: 'rgba(15, 23, 42, 0.6)', padding: '1rem', borderRadius: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <h4 style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            📈 Empirical Execution Scaling: Time vs. Input Length
          </h4>
          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.78rem' }}>
            <span style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: 10, height: 10, background: '#ef4444', display: 'inline-block', borderRadius: 2 }} />
              Original Regex ({analysisResult?.risk_class?.toUpperCase()})
            </span>
            {afterPoints.length > 0 && (
              <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: 10, height: 10, background: '#10b981', display: 'inline-block', borderRadius: 2 }} />
                Repaired Regex (LINEAR)
              </span>
            )}
          </div>
        </div>

        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const yVal = height - padding.bottom - pct * (height - padding.top - padding.bottom);
            const labelVal = Math.round(pct * maxTime);
            return (
              <g key={i}>
                <line x1={padding.left} y1={yVal} x2={width - padding.right} y2={yVal} stroke="#334155" strokeDasharray="3 3" />
                <text x={padding.left - 8} y={yVal + 4} fill="#64748b" fontSize="10" textAnchor="end">
                  {labelVal}ms
                </text>
              </g>
            );
          })}

          {/* X axis */}
          <line
            x1={padding.left}
            y1={height - padding.bottom}
            x2={width - padding.right}
            y2={height - padding.bottom}
            stroke="#475569"
          />

          {/* Before repair line (Red) */}
          <path d={makePath(beforePoints)} fill="none" stroke="#ef4444" strokeWidth="2.5" />
          {beforePoints.map((p, idx) => (
            <circle
              key={`b-${idx}`}
              cx={scaleX(p.length)}
              cy={scaleY(p.duration_ms)}
              r={p.timed_out ? 5 : 3.5}
              fill={p.timed_out ? '#dc2626' : '#ef4444'}
              stroke="#fff"
              strokeWidth={p.timed_out ? 1.5 : 1}
            >
              <title>{`Length: ${p.length}, Duration: ${p.duration_ms.toFixed(2)}ms ${p.timed_out ? '(TIMED OUT)' : ''}`}</title>
            </circle>
          ))}

          {/* After repair line (Green) */}
          {afterPoints.length > 0 && (
            <>
              <path d={makePath(afterPoints)} fill="none" stroke="#10b981" strokeWidth="2.5" />
              {afterPoints.map((p, idx) => (
                <circle
                  key={`a-${idx}`}
                  cx={scaleX(p.length)}
                  cy={scaleY(p.duration_ms)}
                  r={3.5}
                  fill="#10b981"
                  stroke="#fff"
                  strokeWidth="1"
                >
                  <title>{`Length: ${p.length}, Duration: ${p.duration_ms.toFixed(2)}ms`}</title>
                </circle>
              ))}
            </>
          )}

          {/* X-axis labels */}
          {beforePoints.map((p, idx) => (
            <text
              key={`lbl-${idx}`}
              x={scaleX(p.length)}
              y={height - padding.bottom + 16}
              fill="#94a3b8"
              fontSize="10"
              textAnchor="middle"
            >
              {p.length}
            </text>
          ))}
          <text x={width / 2} y={height - 5} fill="#64748b" fontSize="10" textAnchor="middle">
            Attack String Length (Characters)
          </text>
        </svg>
      </div>
    );
  };

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }} id="redos-guard-panel">
      {/* Title & Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '1.5rem' }}>🛡️</span>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', color: '#fff' }}>ReDoS Guard Studio</h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Explainable Risk Screening, AST Provenance Localization & Verified DFA Repair
            </p>
          </div>
        </div>

        {riskClass && (
          <div
            id="redos-risk-badge"
            style={{
              padding: '0.4rem 1rem',
              borderRadius: '9999px',
              fontWeight: 700,
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              background:
                riskClass === 'linear'
                  ? 'rgba(16, 185, 129, 0.2)'
                  : analysisResult.slowdown_confirmed
                  ? 'rgba(239, 68, 68, 0.25)'
                  : 'rgba(245, 158, 11, 0.25)',
              border: `1.5px solid ${
                riskClass === 'linear'
                  ? '#10b981'
                  : analysisResult.slowdown_confirmed
                  ? '#ef4444'
                  : '#f59e0b'
              }`,
              color:
                riskClass === 'linear'
                  ? '#6ee7b7'
                  : analysisResult.slowdown_confirmed
                  ? '#fca5a5'
                  : '#fde68a',
              boxShadow:
                analysisResult.slowdown_confirmed
                  ? '0 0 12px rgba(239, 68, 68, 0.35)'
                  : 'none',
            }}
          >
            <span>{riskClass === 'linear' ? '✅' : analysisResult.slowdown_confirmed ? '⚠️' : '⚡'}</span>
            <span>
              {riskClass === 'linear'
                ? 'LINEAR / SAFE'
                : analysisResult.slowdown_confirmed
                ? `CONFIRMED BY MEASUREMENT (${riskClass.toUpperCase()})`
                : `STRUCTURALLY AMBIGUOUS ONLY (${riskClass.toUpperCase()})`}
            </span>
          </div>
        )}
      </div>

      {/* Error alert */}
      {errorMessage && (
        <div
          style={{
            padding: '0.75rem 1rem',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            borderRadius: '6px',
            color: '#fca5a5',
            marginBottom: '1rem',
            fontSize: '0.85rem',
          }}
        >
          🚨 <strong>ERROR:</strong> {errorMessage}
        </div>
      )}

      {/* Input controls & Quick presets */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.75rem' }}>
          <input
            id="redos-regex-input"
            type="text"
            className="input-field"
            value={targetRegex}
            onChange={(e) => setTargetRegex(e.target.value)}
            placeholder="Enter regular expression (e.g. (a+)+$, a*a*b, (a|b)*abb)..."
            style={{ flex: 1, fontFamily: 'var(--font-mono)', fontSize: '1rem' }}
          />
          <button
            id="btn-analyze-redos"
            className="btn-primary"
            onClick={() => handleAnalyze()}
            disabled={loading || !targetRegex.trim()}
          >
            {loading ? '⚡ Analyzing...' : '🔍 Screen & Explain'}
          </button>
          <button
            id="btn-repair-redos"
            className="btn-secondary"
            onClick={() => handleRepair()}
            disabled={loading || !targetRegex.trim()}
          >
            🛠️ Verify Repair
          </button>
        </div>

        {/* Quick Presets */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Quick Presets:</span>
          {PRESETS.map((p, idx) => (
            <button
              key={idx}
              className="badge"
              style={{
                cursor: 'pointer',
                background: 'rgba(30, 41, 59, 0.8)',
                border: '1px solid var(--border-subtle)',
                color: '#cbd5e1',
                padding: '0.2rem 0.6rem',
                fontSize: '0.75rem',
              }}
              onClick={() => handleSelectPreset(p.regex)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Diagnostic Analysis Panel */}
      {analysisResult && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1.25rem',
            marginTop: '1rem',
          }}
        >
          {/* Column 1: Source Span Localization & Explanation */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.5)',
              padding: '1.25rem',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', color: 'var(--accent-cyan)' }}>
              🎯 Source-Level AST Provenance Localization
            </h3>

            <div
              style={{
                padding: '0.75rem',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '6px',
                marginBottom: '0.75rem',
                border: '1px dashed var(--border-subtle)',
              }}
            >
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>
                Regex with offending span highlighted:
              </span>
              <div>{renderHighlightedRegex()}</div>
            </div>

            <div style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: '1.45', marginBottom: '0.75rem' }}>
              <strong>Diagnosis:</strong> {analysisResult.explanation}
            </div>

            {analysisResult.engine_nuance_note && (
              <div
                id="redos-engine-nuance-callout"
                style={{
                  padding: '0.6rem 0.8rem',
                  background: 'rgba(59, 130, 246, 0.12)',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  borderRadius: '6px',
                  color: '#93c5fd',
                  fontSize: '0.8rem',
                  lineHeight: '1.4',
                  marginBottom: '0.75rem',
                }}
              >
                ℹ️ <strong>Engine Nuance:</strong> {analysisResult.engine_nuance_note}
              </div>
            )}

            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Confidence: {(analysisResult.confidence * 100).toFixed(1)}% | States involved:{' '}
              {analysisResult.offending_states.length || 'None'} | Exact Time: {analysisResult.execution_time_ms}ms
            </div>
          </div>

          {/* Column 2: Attack String Synthesizer & Empirical Scaling */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.5)',
              padding: '1.25rem',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', color: 'var(--accent-rose)' }}>
              💣 Pumpable Attack Synthesizer
            </h3>

            {analysisResult.attack_string ? (
              <div>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', fontSize: '0.82rem' }}>
                  <span className="badge">Prefix: '{analysisResult.attack_string.prefix}'</span>
                  <span className="badge" style={{ borderColor: '#f43f5e', color: '#fda4af' }}>
                    Pump: '{analysisResult.attack_string.pump}'
                  </span>
                  <span className="badge">Suffix: '{analysisResult.attack_string.suffix}'</span>
                </div>

                <div
                  style={{
                    padding: '0.5rem 0.75rem',
                    background: 'rgba(0, 0, 0, 0.4)',
                    borderRadius: '6px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.82rem',
                    color: '#f87171',
                    wordBreak: 'break-all',
                    marginBottom: '0.5rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span>{analysisResult.attack_string.sample_attack}</span>
                  <button
                    onClick={() => handleCopyAttack(analysisResult.attack_string.sample_attack)}
                    className="btn-secondary"
                    style={{ padding: '0.15rem 0.5rem', fontSize: '0.75rem' }}
                  >
                    {copiedAttack ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                  {analysisResult.empirical_benchmark?.summary || 'Empirical sandboxed test ready.'}
                </div>
                {analysisResult.empirical_benchmark && (
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    <span
                      id="empirical-status-tag"
                      className="badge"
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        background: analysisResult.slowdown_confirmed ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        borderColor: analysisResult.slowdown_confirmed ? '#ef4444' : '#f59e0b',
                        color: analysisResult.slowdown_confirmed ? '#fca5a5' : '#fde68a',
                      }}
                    >
                      Measurement Status: {analysisResult.status_label || (analysisResult.slowdown_confirmed ? 'confirmed by measurement' : 'structurally ambiguous only')}
                    </span>
                    {analysisResult.empirical_benchmark.match_mode && (
                      <span className="badge" style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                        Semantics: {analysisResult.empirical_benchmark.match_mode}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: '#10b981', fontSize: '0.85rem' }}>
                ✅ Safe regex: No pumpable attack string exists. All cycle traversals evaluate linearly.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Suggested Repair Section with Minimized-DFA Equivalence Verification */}
      {repairResult && (
        <div
          style={{
            marginTop: '1.25rem',
            padding: '1.25rem',
            background: repairResult.success ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
            border: `1.5px solid ${repairResult.success ? '#10b981' : '#ef4444'}`,
            borderRadius: '8px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ margin: 0, fontSize: '1rem', color: repairResult.success ? '#34d399' : '#f87171' }}>
              {repairResult.success ? '✨ Verified Language-Equivalent Repair' : '⚠️ Repair Unsuccessful'}
            </h3>
            {repairResult.equivalence_verified && (
              <span
                id="equivalence-verified-badge"
                style={{
                  background: 'rgba(16, 185, 129, 0.25)',
                  border: '1px solid #10b981',
                  color: '#6ee7b7',
                  padding: '0.2rem 0.75rem',
                  borderRadius: '9999px',
                  fontWeight: 700,
                  fontSize: '0.78rem',
                }}
              >
                ✓ Minimized DFA Language Equivalence Verified
              </span>
            )}
          </div>

          {repairResult.success ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem' }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', color: '#fff' }}>
                  <span style={{ textDecoration: 'line-through', color: '#94a3b8' }}>
                    {repairResult.original_regex}
                  </span>{' '}
                  <span style={{ color: '#10b981', fontWeight: 'bold' }}>➜ {repairResult.repaired_regex}</span>
                </div>
                <span className="badge" style={{ borderColor: '#10b981', color: '#6ee7b7' }}>
                  Technique: {repairResult.repair_technique}
                </span>
                {onLoadIntoStudio && (
                  <button
                    className="btn-secondary"
                    style={{ padding: '0.3rem 0.75rem', fontSize: '0.8rem', borderColor: '#10b981', color: '#6ee7b7' }}
                    onClick={() => onLoadIntoStudio(repairResult.repaired_regex)}
                  >
                    🚀 Load into Automata Studio
                  </button>
                )}
              </div>
              <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#cbd5e1' }}>
                {repairResult.explanation}
              </p>

              {/* Before/After empirical time benchmark chart */}
              {renderBenchmarkChart()}
            </div>
          ) : (
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#fca5a5' }}>
              {repairResult.explanation}
            </p>
          )}
        </div>
      )}

      {/* Academic Honesty & Literature References */}
      <div
        style={{
          marginTop: '1.25rem',
          padding: '0.75rem 1rem',
          background: 'rgba(15, 23, 42, 0.4)',
          borderRadius: '6px',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          borderTop: '1px solid var(--border-subtle)',
        }}
      >
        ℹ️ <strong>Academic Context:</strong> ReDoS detection and regex repair build on published research
        (e.g., <em>RegexScalpel</em>, <em>ReDoSHunter</em>, <em>FlashRegex</em>, Weber & Seidl 1991). AutoMind-AI's
        contribution is fast explainable GNN risk screening paired with source-level provenance within an educational
        automata theory pipeline.
      </div>
    </div>
  );
}

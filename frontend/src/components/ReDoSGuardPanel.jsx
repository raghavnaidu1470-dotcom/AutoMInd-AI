import React, { useState } from 'react';
import { api } from '../services/api';

const REDOS_PRESETS = [
  { label: 'Select a ReDoS pattern...', regex: '' },
  { label: '(a+)+$ (Exponential - Nested quantifiers)', regex: '(a+)+$' },
  { label: '(a|aa)+$ (Exponential - Overlapping alternation)', regex: '(a|aa)+$' },
  { label: '(a*)*b (Exponential - Kleene star nesting)', regex: '(a*)*b' },
  { label: 'a*a*b (Polynomial - Adjacent repetition)', regex: 'a*a*b' },
  { label: '(a|b)*abb (Linear / Safe)', regex: '(a|b)*abb' },
];

export default function ReDoSGuardPanel({ onLoadIntoStudio, initialRegex = '(a+)+$' }) {
  const [targetRegex, setTargetRegex] = useState(initialRegex);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [repairResult, setRepairResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [copiedAttack, setCopiedAttack] = useState(false);
  const [useLogScale, setUseLogScale] = useState(false);

  // Trigger ReDoS analysis
  const handleAnalyze = async (regexToAnalyze = targetRegex) => {
    if (!regexToAnalyze || !regexToAnalyze.trim()) return;
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.analyzeReDoS(regexToAnalyze, true);
      setAnalysisResult(res);

      if (res.is_vulnerable) {
        // Automatically attempt safe language-equivalent repair
        try {
          const rep = await api.repairReDoS(regexToAnalyze, true);
          setRepairResult(rep);
        } catch (repErr) {
          setRepairResult(null);
        }
      } else {
        setRepairResult(null);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPreset = (e) => {
    const val = e.target.value;
    if (val) {
      setTargetRegex(val);
      handleAnalyze(val);
    }
  };

  const handleCopyAttack = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedAttack(true);
    setTimeout(() => setCopiedAttack(false), 2000);
  };

  // Render regex with offending span highlighted
  const renderHighlightedRegex = () => {
    if (!analysisResult) return targetRegex;
    const spans = analysisResult.highlighted_spans || [];
    if (spans.length === 0) {
      return <span>{analysisResult.regex}</span>;
    }

    const span = spans[0];
    const before = analysisResult.regex.slice(0, span.start);
    const highlighted = analysisResult.regex.slice(span.start, span.end);
    const after = analysisResult.regex.slice(span.end);

    return (
      <span>
        <span>{before}</span>
        <span className="offending-span" title={`Offending span [${span.start}..${span.end}]`}>
          {highlighted}
        </span>
        <span>{after}</span>
      </span>
    );
  };

  // Render Benchmark Scaling SVG Chart (Linear vs Log Scale)
  const renderBenchmarkChart = () => {
    const beforePoints = repairResult?.before_benchmark?.points || analysisResult?.empirical_benchmark?.points || [];
    const afterPoints = repairResult?.after_benchmark?.points || [];

    if (beforePoints.length === 0) return null;

    const width = 580;
    const height = 230;
    const padding = { top: 25, right: 30, bottom: 45, left: 65 };

    const maxLen = Math.max(...beforePoints.map((p) => p.length), 30);
    const minLen = Math.min(...beforePoints.map((p) => p.length), 0);

    const rawMaxTime = Math.max(
      ...beforePoints.map((p) => p.duration_ms),
      ...afterPoints.map((p) => p.duration_ms),
      10
    );

    const scaleX = (len) =>
      padding.left + ((len - minLen) / Math.max(maxLen - minLen, 1)) * (width - padding.left - padding.right);

    const getYVal = (timeMs) => {
      if (useLogScale) {
        const val = Math.max(0, timeMs);
        return Math.log10(val + 1);
      }
      return timeMs;
    };

    const maxChartY = getYVal(rawMaxTime);

    const scaleY = (timeMs) => {
      const yVal = getYVal(timeMs);
      return height - padding.bottom - (yVal / Math.max(maxChartY, 1e-4)) * (height - padding.top - padding.bottom);
    };

    const makePath = (points) => {
      if (!points || points.length === 0) return '';
      return points
        .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${scaleX(p.length)} ${scaleY(p.duration_ms)}`)
        .join(' ');
    };

    // Y Grid ticks
    const yTicks = useLogScale
      ? [0, 1, 2, 3].filter((logVal) => logVal <= maxChartY + 0.5).map((logVal) => ({
          label: `${Math.round(Math.pow(10, logVal) - 1)}ms`,
          y: height - padding.bottom - (logVal / Math.max(maxChartY, 1)) * (height - padding.top - padding.bottom),
        }))
      : [0, 0.25, 0.5, 0.75, 1.0].map((pct) => ({
          label: `${Math.round(pct * rawMaxTime)}ms`,
          y: height - padding.bottom - pct * (height - padding.top - padding.bottom),
        }));

    return (
      <div style={{ marginTop: '1rem', border: 'var(--border-rule)', background: 'var(--paper-panel)', padding: '0.85rem', borderRadius: 'var(--radius-control)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--ink-slate)' }}>
            Execution Scaling: Time vs. Input Length
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* Log scale toggle */}
            <button
              type="button"
              className="btn-quiet"
              onClick={() => setUseLogScale(!useLogScale)}
              aria-pressed={useLogScale}
            >
              {useLogScale ? 'Scale: Logarithmic (log₁₀)' : 'Scale: Linear'}
            </button>

            {/* Legend */}
            <div style={{ display: 'flex', gap: '0.75rem', fontSize: '11px' }}>
              <span style={{ color: 'var(--red-risk)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: 8, height: 8, background: 'var(--red-risk)', display: 'inline-block' }} />
                Original
              </span>
              {afterPoints.length > 0 && (
                <span style={{ color: 'var(--green-accept)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: 8, height: 8, background: 'var(--green-accept)', display: 'inline-block' }} />
                  Repaired (Linear)
                </span>
              )}
            </div>
          </div>
        </div>

        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          {/* Grid lines */}
          {yTicks.map((tick, i) => (
            <g key={i}>
              <line
                x1={padding.left}
                y1={tick.y}
                x2={width - padding.right}
                y2={tick.y}
                stroke="var(--ink-border-light)"
                strokeDasharray="3 3"
              />
              <text
                x={padding.left - 8}
                y={tick.y + 4}
                fill="var(--ink-secondary)"
                fontSize="10"
                fontFamily="var(--font-mono)"
                textAnchor="end"
              >
                {tick.label}
              </text>
            </g>
          ))}

          {/* X axis line */}
          <line
            x1={padding.left}
            y1={height - padding.bottom}
            x2={width - padding.right}
            y2={height - padding.bottom}
            stroke="var(--ink-border)"
          />

          {/* Before repair path (Brick Red) */}
          <path d={makePath(beforePoints)} fill="none" stroke="var(--red-risk)" strokeWidth="2" />
          {beforePoints.map((p, idx) => (
            <circle
              key={`b-${idx}`}
              cx={scaleX(p.length)}
              cy={scaleY(p.duration_ms)}
              r={p.timed_out ? 4 : 3}
              fill={p.timed_out ? 'var(--red-risk)' : '#ffffff'}
              stroke="var(--red-risk)"
              strokeWidth="1.5"
            >
              <title>{`Length: ${p.length}, Duration: ${p.duration_ms.toFixed(2)}ms ${p.timed_out ? '(Timed out)' : ''}`}</title>
            </circle>
          ))}

          {/* After repair path (Muted Green) */}
          {afterPoints.length > 0 && (
            <>
              <path d={makePath(afterPoints)} fill="none" stroke="var(--green-accept)" strokeWidth="2" />
              {afterPoints.map((p, idx) => (
                <circle
                  key={`a-${idx}`}
                  cx={scaleX(p.length)}
                  cy={scaleY(p.duration_ms)}
                  r={3}
                  fill="#ffffff"
                  stroke="var(--green-accept)"
                  strokeWidth="1.5"
                >
                  <title>{`Length: ${p.length}, Duration: ${p.duration_ms.toFixed(2)}ms`}</title>
                </circle>
              ))}
            </>
          )}

          {/* X-axis ticks */}
          {beforePoints.map((p, idx) => (
            <text
              key={`x-${idx}`}
              x={scaleX(p.length)}
              y={height - padding.bottom + 14}
              fill="var(--ink-secondary)"
              fontSize="10"
              fontFamily="var(--font-mono)"
              textAnchor="middle"
            >
              {p.length}
            </text>
          ))}

          {/* Axes labels */}
          <text
            x={width / 2}
            y={height - 8}
            fill="var(--ink-secondary)"
            fontSize="10"
            textAnchor="middle"
          >
            Attack string length (characters)
          </text>
          <text
            x={14}
            y={height / 2}
            transform={`rotate(-90 14 ${height / 2})`}
            fill="var(--ink-secondary)"
            fontSize="10"
            textAnchor="middle"
          >
            Duration (ms)
          </text>
        </svg>
      </div>
    );
  };

  const riskClass = analysisResult?.risk_class;
  const isVulnerable = Boolean(analysisResult?.is_vulnerable);
  const slowdownConfirmed = Boolean(analysisResult?.slowdown_confirmed);

  return (
    <div className="redos-view" id="redos-view" role="region" aria-label="ReDoS Guard Screening & Repair">
      {/* Header controls & pattern selector */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            id="redos-target-input"
            type="text"
            className="input-code"
            style={{ flex: '1 1 280px' }}
            value={targetRegex}
            onChange={(e) => setTargetRegex(e.target.value)}
            placeholder="Enter regular expression to test for ReDoS..."
            spellCheck="false"
          />

          <button
            type="button"
            id="btn-analyze-redos"
            className="btn-run"
            onClick={() => handleAnalyze()}
            disabled={loading || !targetRegex.trim()}
          >
            {loading ? 'Screening...' : 'Screen regex'}
          </button>

          <select
            className="select-examples"
            onChange={handleSelectPreset}
            defaultValue=""
            aria-label="Load a standard ReDoS benchmark pattern"
          >
            {REDOS_PRESETS.map((p, idx) => (
              <option key={idx} value={p.regex} disabled={!p.regex}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error alert */}
      {errorMessage && (
        <div className="syntax-error-banner" role="alert">
          <div>
            <strong>Error: </strong>
            {errorMessage}
          </div>
        </div>
      )}

      {/* Analysis Results Display */}
      {analysisResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Verdict Banner distinguishing confirmed from structurally ambiguous */}
          <div
            className={`redos-risk-banner ${
              riskClass === 'exponential' || riskClass === 'polynomial'
                ? 'exponential'
                : 'linear'
            }`}
            id="redos-verdict-banner"
            role="status"
          >
            <div>
              <strong>Verdict: </strong>
              {!isVulnerable ? (
                <span>Linear / Safe (no catastrophic backtracking detected)</span>
              ) : slowdownConfirmed ? (
                <span>Confirmed by measurement ({riskClass.toUpperCase()} BACKTRACKING RISK)</span>
              ) : (
                <span>Structurally ambiguous only ({riskClass.toUpperCase()} AMBIGUOUS PATHS)</span>
              )}
            </div>

            <span style={{ fontSize: 'var(--text-xs)' }}>
              Confidence: {(analysisResult.confidence * 100).toFixed(0)}%
            </span>
          </div>

          {/* Offending Span Underlined with Engineering Callout */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div className="offending-regex-container">
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                Evaluated expression with offending span:
              </span>
              <div>{renderHighlightedRegex()}</div>
            </div>

            <div className="engineering-callout">
              <div className="engineering-callout-title">AST Diagnosis</div>
              <p style={{ margin: 0 }}>{analysisResult.explanation}</p>
            </div>
          </div>

          {/* Pumpable Attack String Section */}
          {analysisResult.attack_string ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <div style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--ink-slate)' }}>
                Pumpable attack string
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.5rem 0.75rem',
                  background: 'var(--paper-panel)',
                  border: 'var(--border-rule)',
                  borderRadius: 'var(--radius-control)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--red-risk)',
                  wordBreak: 'break-all',
                }}
              >
                <span>{analysisResult.attack_string.sample_attack}</span>
                <button
                  type="button"
                  className="btn-quiet"
                  style={{ marginLeft: '0.75rem', flexShrink: 0 }}
                  onClick={() => handleCopyAttack(analysisResult.attack_string.sample_attack)}
                >
                  {copiedAttack ? '✓ Copied' : 'Copy'}
                </button>
              </div>

              <div style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>
                Tokens: prefix='{analysisResult.attack_string.prefix}', pump='{analysisResult.attack_string.pump}', suffix='{analysisResult.attack_string.suffix}'
              </div>
            </div>
          ) : (
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--green-accept)' }}>
              ✓ No pumpable attack string exists. All cycle traversals evaluate in linear time.
            </div>
          )}

          {/* Empirical Scaling Benchmark Chart */}
          {renderBenchmarkChart()}

          {/* Suggested Safe Language-Equivalent Repair with Diff */}
          {repairResult && (
            <div
              style={{
                marginTop: '0.5rem',
                padding: '0.85rem',
                border: 'var(--border-rule)',
                borderRadius: 'var(--radius-control)',
                background: repairResult.success ? 'var(--green-tint)' : 'var(--paper-subtle)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ fontWeight: 700, fontSize: 'var(--text-sm)', color: repairResult.success ? 'var(--green-accept)' : 'var(--red-risk)' }}>
                  {repairResult.success ? 'Language-equivalent safe repair' : 'Repair unavailable'}
                </div>

                {repairResult.equivalence_verified && (
                  <span style={{ fontSize: '11px', color: 'var(--green-accept)', fontWeight: 600 }}>
                    ✓ Minimized DFA language equivalence verified
                  </span>
                )}
              </div>

              {repairResult.success ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div className="diff-container">
                    <div className="diff-line-del">- {repairResult.original_regex}</div>
                    <div className="diff-line-add">+ {repairResult.repaired_regex}</div>
                  </div>

                  <p style={{ margin: 0, fontSize: 'var(--text-xs)', color: 'var(--ink-slate)' }}>
                    {repairResult.explanation}
                  </p>

                  {onLoadIntoStudio && (
                    <div>
                      <button
                        type="button"
                        className="btn-quiet"
                        style={{ fontWeight: 600 }}
                        onClick={() => onLoadIntoStudio(repairResult.repaired_regex)}
                      >
                        Load repaired regex into pipeline
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <p style={{ margin: 0, fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)' }}>
                  {repairResult.explanation || 'No safe equivalent repair found.'}
                </p>
              )}
            </div>
          )}

          {/* Plain Statement of Tool Limits */}
          <div
            style={{
              padding: '0.6rem 0.75rem',
              background: 'var(--paper-panel)',
              border: 'var(--border-rule)',
              borderRadius: 'var(--radius-control)',
              fontSize: '11px',
              color: 'var(--ink-secondary)',
              lineHeight: 1.45,
            }}
          >
            <strong>Tool limits:</strong> ReDoS Guard analyzes regular languages recognized by finite state automata.
            It does not support backreferences (e.g., <code>\1</code>), lookaround assertions (<code>(?=...)</code>, <code>(?!...)</code>),
            or possessive quantifiers (<code>a++</code>), as those require non-regular match engines.
          </div>
        </div>
      )}
    </div>
  );
}

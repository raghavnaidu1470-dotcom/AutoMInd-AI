import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { REDOS_EXAMPLES, runIsolatedWorkerMatch } from '../utils/redosExamples.js';

export default function ReDoSGuardPanel({ onLoadIntoStudio, initialRegex = '(a|b)*abb' }) {
  // Tabs: 'user_analysis' | 'educational_presets'
  const [activeTab, setActiveTab] = useState('user_analysis');

  // User regex analysis state
  const [targetRegex, setTargetRegex] = useState(initialRegex);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [repairResult, setRepairResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [copiedAttack, setCopiedAttack] = useState(false);
  const [useLogScale, setUseLogScale] = useState(false);

  // Request sequencing to discard stale responses
  const analyzeSeqRef = useRef(0);

  // Educational presets state
  const [selectedExample, setSelectedExample] = useState(REDOS_EXAMPLES[0]);
  const [presetDemoResult, setPresetDemoResult] = useState(null);
  const [testingPreset, setTestingPreset] = useState(false);

  // When initialRegex from studio changes, sync user analysis target
  useEffect(() => {
    if (initialRegex) {
      setTargetRegex(initialRegex);
    }
  }, [initialRegex]);

  // Trigger ReDoS analysis on the user's expression
  const handleAnalyze = async (regexToAnalyze = targetRegex) => {
    if (!regexToAnalyze || !regexToAnalyze.trim()) return;
    const currentSeq = ++analyzeSeqRef.current;
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.analyzeReDoS(regexToAnalyze, true);
      if (currentSeq !== analyzeSeqRef.current) return; // Discard stale response
      setAnalysisResult(res);

      if (res.is_vulnerable) {
        try {
          const rep = await api.repairReDoS(regexToAnalyze, true);
          if (currentSeq !== analyzeSeqRef.current) return;
          setRepairResult(rep);
        } catch {
          if (currentSeq === analyzeSeqRef.current) setRepairResult(null);
        }
      } else {
        setRepairResult(null);
      }
    } catch (err) {
      if (currentSeq === analyzeSeqRef.current) {
        setErrorMessage(err.message || 'Analysis failed');
      }
    } finally {
      if (currentSeq === analyzeSeqRef.current) {
        setLoading(false);
      }
    }
  };

  const handleTestPresetBounded = async (regexStr, inputStr, typeLabel) => {
    setTestingPreset(true);
    setPresetDemoResult({
      typeLabel,
      inputTested: inputStr,
      running: true,
    });
    try {
      const res = await runIsolatedWorkerMatch(regexStr, inputStr, { timeoutMs: 100 });
      setPresetDemoResult({
        ...res,
        typeLabel,
        inputTested: inputStr,
        running: false,
      });
    } catch (err) {
      setPresetDemoResult({
        success: false,
        error: err.message,
        typeLabel,
        inputTested: inputStr,
        running: false,
      });
    } finally {
      setTestingPreset(false);
    }
  };

  const handleCopyAttack = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedAttack(true);
    setTimeout(() => setCopiedAttack(false), 2000);
  };

  // Offending span rendering
  const renderHighlightedRegex = (regexStr, spans) => {
    if (!spans || spans.length === 0) {
      return <span>{regexStr}</span>;
    }
    const span = spans[0];
    const before = regexStr.slice(0, span.start);
    const highlighted = regexStr.slice(span.start, span.end);
    const after = regexStr.slice(span.end);

    return (
      <span>
        <span>{before}</span>
        <span className="offending-span" title={`Risky token span [${span.start}..${span.end}]`}>
          {highlighted}
        </span>
        <span>{after}</span>
      </span>
    );
  };

  // Render Benchmark Scaling SVG Chart
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
        const minLog = Math.log10(0.1);
        const maxLog = Math.log10(Math.max(rawMaxTime, 1));
        const valLog = Math.log10(Math.max(timeMs, 0.1));
        return height - padding.bottom - ((valLog - minLog) / Math.max(maxLog - minLog, 0.001)) * (height - padding.top - padding.bottom);
      }
      return height - padding.bottom - (timeMs / Math.max(rawMaxTime, 1)) * (height - padding.top - padding.bottom);
    };

    const makePath = (points) => {
      if (!points || points.length === 0) return '';
      return points.map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${scaleX(p.length)} ${getYVal(p.duration_ms)}`).join(' ');
    };

    return (
      <div className="benchmark-chart-container" role="region" aria-label="Empirical Timing Growth Chart">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
          <div>
            <span style={{ fontSize: 'var(--text-xs)', fontWeight: 700 }}>
              Empirical Backtracking Benchmark (Backtracking Engine Timings)
            </span>
            <div style={{ fontSize: '10px', color: 'var(--ink-secondary)' }}>
              Measured via sandboxed Python/JS subprocess execution on near-matching adversarial strings
            </div>
          </div>
          <button
            type="button"
            className="btn-quiet"
            style={{ fontSize: '11px' }}
            onClick={() => setUseLogScale(!useLogScale)}
            aria-pressed={useLogScale}
          >
            Scale: {useLogScale ? 'Logarithmic' : 'Linear'}
          </button>
        </div>

        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', background: 'var(--paper-panel)', border: 'var(--border-rule)', borderRadius: 'var(--radius-control)' }}>
          {/* Grid lines */}
          <line x1={padding.left} y1={height - padding.bottom} x2={width - padding.right} y2={height - padding.bottom} stroke="var(--ink-border)" strokeWidth="1" />
          <line x1={padding.left} y1={padding.top} x2={padding.left} y2={height - padding.bottom} stroke="var(--ink-border)" strokeWidth="1" />

          {/* Original vulnerable curve (Red) */}
          <path d={makePath(beforePoints)} fill="none" stroke="var(--red-risk)" strokeWidth="2.5" strokeDasharray={repairResult ? '4 3' : undefined} />
          {beforePoints.map((p, idx) => (
            <circle key={`b-${idx}`} cx={scaleX(p.length)} cy={getYVal(p.duration_ms)} r="4" fill="var(--red-risk)">
              <title>{`Input Length: ${p.length} chars, Duration: ${p.duration_ms.toFixed(2)}ms (Backtracking engine)`}</title>
            </circle>
          ))}

          {/* Repaired curve (Green, if repair benchmarked) */}
          {afterPoints.length > 0 && (
            <>
              <path d={makePath(afterPoints)} fill="none" stroke="var(--green-accept)" strokeWidth="2.5" />
              {afterPoints.map((p, idx) => (
                <circle key={`a-${idx}`} cx={scaleX(p.length)} cy={getYVal(p.duration_ms)} r="4" fill="var(--green-accept)">
                  <title>{`Repaired: Length: ${p.length} chars, Duration: ${p.duration_ms.toFixed(2)}ms`}</title>
                </circle>
              ))}
            </>
          )}

          {/* X-axis ticks */}
          {beforePoints.map((p, idx) => (
            <text key={`x-${idx}`} x={scaleX(p.length)} y={height - padding.bottom + 14} fill="var(--ink-secondary)" fontSize="10" fontFamily="var(--font-mono)" textAnchor="middle">
              {p.length}
            </text>
          ))}

          <text x={width / 2} y={height - 8} fill="var(--ink-secondary)" fontSize="10" textAnchor="middle">
            Near-match string length (characters)
          </text>
          <text x={14} y={height / 2} transform={`rotate(-90 14 ${height / 2})`} fill="var(--ink-secondary)" fontSize="10" textAnchor="middle">
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
      {/* Educational Primer: Backtracking vs Automata Immunity */}
      <div className="redos-education-primer">
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-start' }}>
          <span style={{ fontSize: '20px' }}>🛡️</span>
          <div>
            <strong style={{ fontSize: 'var(--text-sm)', color: 'var(--ink-slate)' }}>
              How ReDoS Happens & Why Automata Are Immune
            </strong>
            <p style={{ margin: '0.25rem 0', fontSize: 'var(--text-xs)', color: 'var(--ink-slate)', lineHeight: 1.45 }}>
              Many programming languages (JavaScript RegExp, Python <code>re</code>, PCRE) evaluate regular expressions using
              <strong> backtracking engines</strong>. When an expression contains ambiguous nested quantifiers or overlapping choices,
              the engine may explore millions of futile paths on adversarial near-matches, locking up CPUs.
            </p>
            <div style={{ padding: '0.35rem 0.6rem', background: 'var(--green-tint)', border: '1px solid var(--green-accept)', borderRadius: '3px', fontSize: '11px', color: 'var(--green-accept)' }}>
              <strong>The Automata Immunity Guarantee:</strong> Pure Deterministic Finite Automata (DFAs, used by AutoMind and Google RE2)
              evaluate in strict <em>linear time O(n)</em>. Because they do not backtrack, they are completely immune to ReDoS!
            </div>
          </div>
        </div>
      </div>

      {/* Primary Navigation Tabs: User Analysis vs Educational Presets */}
      <div className="redos-tab-strip" role="tablist" aria-label="ReDoS modes">
        <button
          type="button"
          className={`redos-tab-btn ${activeTab === 'user_analysis' ? 'active' : ''}`}
          onClick={() => setActiveTab('user_analysis')}
          role="tab"
          aria-selected={activeTab === 'user_analysis'}
        >
          🔍 Analyze Studio Regex (<code>{targetRegex}</code>)
        </button>
        <button
          type="button"
          className={`redos-tab-btn ${activeTab === 'educational_presets' ? 'active' : ''}`}
          onClick={() => setActiveTab('educational_presets')}
          role="tab"
          aria-selected={activeTab === 'educational_presets'}
        >
          📚 Educational Presets Catalog ({REDOS_EXAMPLES.length} Archetypes)
        </button>
      </div>

      {/* TAB 1: User Regex Analysis */}
      {activeTab === 'user_analysis' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              id="redos-target-input"
              type="text"
              className="input-code"
              style={{ flex: '1 1 300px' }}
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
              {loading ? 'Screening...' : 'Screen this regex'}
            </button>
          </div>

          {errorMessage && (
            <div className="syntax-error-banner" role="alert">
              <strong>Analysis Error: </strong> {errorMessage}
            </div>
          )}

          {analysisResult ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {/* Separate Static vs Empirical Findings */}
              <div
                className={`redos-risk-banner ${
                  riskClass === 'exponential' || riskClass === 'polynomial'
                    ? 'exponential'
                    : 'linear'
                }`}
                role="status"
              >
                <div>
                  <strong>Static Analysis Finding: </strong>
                  {!isVulnerable ? (
                    <span>Linear / Safe — No ambiguous overlapping cycles detected.</span>
                  ) : (
                    <span>
                      {riskClass.toUpperCase()} AMBIGUOUS STRUCTURE ({analysisResult.degree ? `Degree ${analysisResult.degree}` : 'Exponential'})
                    </span>
                  )}
                </div>

                <div style={{ fontSize: 'var(--text-xs)', marginTop: '0.2rem' }}>
                  <strong>Runtime Backtracking Measurement: </strong>
                  {slowdownConfirmed ? (
                    <span>Adversarial slowdown confirmed on backtracking engine benchmark.</span>
                  ) : (
                    <span>No severe timing spike observed on tested sample lengths (or evaluates linearly).</span>
                  )}
                </div>
              </div>

              {/* Evaluated Expression Span */}
              <div className="offending-regex-container">
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)', display: 'block', marginBottom: '0.25rem' }}>
                  Analyzed Expression ({analysisResult.regex}):
                </span>
                <div>{renderHighlightedRegex(analysisResult.regex, analysisResult.highlighted_spans)}</div>
              </div>

              <div className="engineering-callout">
                <div className="engineering-callout-title">AST Structural Diagnosis</div>
                <p style={{ margin: 0, fontSize: 'var(--text-xs)' }}>{analysisResult.explanation}</p>
              </div>

              {/* Pumpable Attack String */}
              {analysisResult.attack_string ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <div style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--ink-slate)' }}>
                    Adversarial Near-Match String:
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.45rem 0.65rem',
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
                </div>
              ) : (
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--green-accept)' }}>
                  ✓ No pumpable attack string detected. Evaluates safely across all inputs.
                </div>
              )}

              {/* Empirical Chart */}
              {renderBenchmarkChart()}

              {/* Proposed Safe Repair */}
              {repairResult && (
                <div className="repair-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong style={{ fontSize: 'var(--text-sm)', color: 'var(--green-accept)' }}>
                      Suggested Safe Alternative: <code>{repairResult.repaired_regex}</code>
                    </strong>
                    {onLoadIntoStudio && (
                      <button
                        type="button"
                        className="btn-run"
                        onClick={() => onLoadIntoStudio(repairResult.repaired_regex)}
                        style={{ fontSize: '11px' }}
                      >
                        Load safe alternative into studio ▶
                      </button>
                    )}
                  </div>
                  <p style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-slate)', margin: '0.4rem 0 0 0' }}>
                    {repairResult.explanation}
                  </p>
                  <div style={{ fontSize: '11px', color: 'var(--ink-secondary)', marginTop: '0.2rem' }}>
                    Formal equivalence: {repairResult.equivalence_verified ? 'Verified identical language' : 'Refactored pattern (verify language requirements)'}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ padding: '1.25rem', textAlign: 'center', background: 'var(--paper-panel)', border: 'var(--border-rule)', borderRadius: 'var(--radius-control)', color: 'var(--ink-secondary)', fontSize: 'var(--text-xs)' }}>
              Click <strong>Screen this regex</strong> to inspect structural ambiguity and benchmark timing growth.
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Educational Presets Catalog */}
      {activeTab === 'educational_presets' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {/* Preset Selector Dropdown */}
          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <label htmlFor="select-archetype" style={{ fontSize: 'var(--text-xs)', fontWeight: 700 }}>
              Select Archetype:
            </label>
            <select
              id="select-archetype"
              className="select-examples"
              style={{ flex: '1 1 320px' }}
              value={selectedExample.id}
              onChange={(e) => {
                const found = REDOS_EXAMPLES.find((ex) => ex.id === e.target.value);
                if (found) {
                  setSelectedExample(found);
                  setPresetDemoResult(null);
                }
              }}
            >
              {REDOS_EXAMPLES.map((ex) => (
                <option key={ex.id} value={ex.id}>
                  {ex.name} ({ex.category})
                </option>
              ))}
            </select>

            {onLoadIntoStudio && (
              <button
                type="button"
                className="btn-quiet-pill"
                onClick={() => onLoadIntoStudio(selectedExample.regex)}
                title="Load this archetype into the main studio"
              >
                Load into Studio ▶
              </button>
            )}
          </div>

          {/* Archetype Breakdown Card */}
          <div className="redos-example-card" id="redos-archetype-card" role="region" aria-label="ReDoS Pattern Breakdown">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <strong style={{ fontSize: 'var(--text-sm)' }}>{selectedExample.name}</strong>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--ink-slate)', marginTop: '0.2rem' }}>
                  Pattern: <code>{selectedExample.regex}</code>
                </div>
              </div>
              <span className={`redos-archetype-badge ${selectedExample.risk}`}>
                {selectedExample.category}
              </span>
            </div>

            {/* Explanation of the failure mode */}
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-slate)', lineHeight: 1.45, background: 'var(--paper-subtle)', padding: '0.5rem', borderRadius: '4px' }}>
              <strong>Why this pattern backtracks: </strong>
              {selectedExample.explanation}
            </div>

            {/* Matching vs Adversarial Test Candidates */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.65rem' }}>
              {/* Matching Candidate */}
              <div style={{ padding: '0.5rem 0.65rem', background: 'var(--paper-subtle)', border: '1px solid var(--ink-border-light)', borderRadius: 'var(--radius-control)' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--green-accept)', marginBottom: '0.2rem' }}>
                  ✓ Benign matching input:
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', marginBottom: '0.4rem', wordBreak: 'break-all' }}>
                  "{selectedExample.matchingInput}"
                </div>
                <button
                  type="button"
                  className="btn-quiet"
                  style={{ fontSize: '11px' }}
                  onClick={() => handleTestPresetBounded(selectedExample.regex, selectedExample.matchingInput, 'Benign match')}
                >
                  Test matching input
                </button>
              </div>

              {/* Adversarial Near-Match Candidate */}
              <div style={{ padding: '0.5rem 0.65rem', background: 'var(--paper-subtle)', border: '1px solid var(--ink-border-light)', borderRadius: 'var(--radius-control)' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--red-risk)', marginBottom: '0.2rem' }}>
                  ⚠️ Adversarial near-match input:
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', marginBottom: '0.4rem', wordBreak: 'break-all' }}>
                  "{selectedExample.problematicInput}"
                </div>
                <button
                  type="button"
                  className="btn-quiet"
                  style={{ fontSize: '11px', borderColor: 'var(--red-risk)', color: 'var(--red-risk)' }}
                  onClick={() => handleTestPresetBounded(selectedExample.regex, selectedExample.problematicInput, 'Adversarial near-match')}
                >
                  Test near-match (bounded)
                </button>
              </div>
            </div>

            {/* Bounded Test Execution Outcome */}
            {presetDemoResult && (
              <div
                style={{
                  padding: '0.5rem 0.75rem',
                  background: presetDemoResult.interrupted
                    ? 'var(--amber-tint)'
                    : presetDemoResult.matched
                    ? 'var(--green-tint)'
                    : 'var(--paper-subtle)',
                  border: `1px solid ${
                    presetDemoResult.interrupted
                      ? 'var(--amber-signal)'
                      : presetDemoResult.matched
                      ? 'var(--green-accept)'
                      : 'var(--ink-border)'
                  }`,
                  borderRadius: 'var(--radius-control)',
                  fontSize: 'var(--text-xs)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.25rem',
                }}
                role="status"
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.4rem' }}>
                  <span>
                    <strong>{presetDemoResult.typeLabel}: </strong>
                    {presetDemoResult.running ? (
                      <em>Testing in isolated background worker...</em>
                    ) : presetDemoResult.interrupted ? (
                      <span style={{ color: 'var(--amber-signal)', fontWeight: 700 }}>
                        ⏱️ Interrupted after {presetDemoResult.durationMs}ms (Worker terminated)
                      </span>
                    ) : presetDemoResult.matched ? (
                      <span style={{ color: 'var(--green-accept)', fontWeight: 700 }}>
                        ✓ Matched successfully ({presetDemoResult.durationMs}ms)
                      </span>
                    ) : (
                      <span>
                        Rejected upon mismatch ({presetDemoResult.durationMs}ms)
                      </span>
                    )}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>
                    Isolation: {presetDemoResult.isolation || 'Web Worker'}
                  </span>
                </div>
                {presetDemoResult.interrupted && (
                  <div style={{ fontSize: '11px', color: 'var(--ink-slate)', lineHeight: 1.35 }}>
                    Adversarial backtracking exceeded the 100ms deadline. The background execution thread was terminated via <code>worker.terminate()</code>, ensuring the browser UI remained completely responsive.
                  </div>
                )}
              </div>
            )}

            {/* Safe Alternative Rewrite */}
            <div style={{ padding: '0.5rem 0.65rem', background: 'var(--green-tint)', border: '1px solid var(--green-accept)', borderRadius: 'var(--radius-control)', marginTop: '0.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--green-accept)' }}>
                  Safe alternative: <code style={{ fontFamily: 'var(--font-mono)' }}>{selectedExample.safeAlternative}</code>
                </span>
                {onLoadIntoStudio && (
                  <button
                    type="button"
                    className="btn-quiet"
                    style={{ fontSize: '11px', fontWeight: 700 }}
                    onClick={() => onLoadIntoStudio(selectedExample.safeAlternative)}
                  >
                    Load safe alternative into studio ▶
                  </button>
                )}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--ink-slate)', lineHeight: 1.4 }}>
                {selectedExample.safeExplanation}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import { parseSyntaxError } from '../utils/syntaxValidator.js';

const STANDARD_EXAMPLES = [
  { label: 'Select an example...', regex: '', string: '' },
  { label: 'Ends in abb: (a|b)*abb', regex: '(a|b)*abb', string: 'ababb' },
  { label: 'Repeated a then b: a*b+', regex: 'a*b+', string: 'aaabbb' },
  { label: 'Alternating binary: (01)*101', regex: '(01)*101', string: '0101101' },
  { label: 'Second to last is a: (a|b)*a(a|b)', regex: '(a|b)*a(a|b)', string: 'bab' },
  { label: 'Even number of zeros: (1*01*0)*1*', regex: '(1*01*0)*1*', string: '10101' },
  { label: 'ReDoS sample: (a+)+$', regex: '(a+)+$', string: 'aaaaaaaaaa!' },
];

export default function RegexInput({
  regex,
  setRegex,
  inputString,
  setInputString,
  onRun,
  loading,
  syntaxError,
  clearSyntaxError,
  recentRegexes = [],
  generatedExamples = null,
  onSelectGeneratedExample = null,
  isExamplesStale = false,
  onGenerateMore = null,
}) {
  const [filterTab, setFilterTab] = useState('all'); // 'all' | 'accepted' | 'rejected' | 'edge'
  const [showAllExamples, setShowAllExamples] = useState(false);
  const [inspectedCandidate, setInspectedCandidate] = useState(null);

  const parsedError = syntaxError ? parseSyntaxError(syntaxError, regex) : null;

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onRun();
    }
  };

  const handleRegexChange = (e) => {
    if (clearSyntaxError) clearSyntaxError();
    setRegex(e.target.value);
  };

  const handleStringChange = (e) => {
    setInputString(e.target.value);
  };

  const handleSelectExample = (e) => {
    const selected = STANDARD_EXAMPLES.find((ex) => ex.label === e.target.value);
    if (selected && selected.regex) {
      if (clearSyntaxError) clearSyntaxError();
      setRegex(selected.regex);
      setInputString(selected.string);
      setTimeout(() => onRun(selected.regex, selected.string), 50);
    }
  };

  const handleSelectRecent = (e) => {
    const val = e.target.value;
    if (val) {
      if (clearSyntaxError) clearSyntaxError();
      setRegex(val);
      setTimeout(() => onRun(val, inputString), 50);
    }
  };

  // Group candidate examples
  const allExamples = generatedExamples?.examples || [];
  const acceptedList = generatedExamples?.accepted || allExamples.filter((e) => e.matches);
  const rejectedList = generatedExamples?.rejected || allExamples.filter((e) => !e.matches);
  const edgeList = generatedExamples?.edgeCases || allExamples.filter((e) => e.group === 'edge');

  let filteredExamples = allExamples;
  if (filterTab === 'accepted') filteredExamples = acceptedList;
  else if (filterTab === 'rejected') filteredExamples = rejectedList;
  else if (filterTab === 'edge') filteredExamples = edgeList;

  const initialCount = 7;
  const displayedExamples = showAllExamples
    ? filteredExamples
    : filteredExamples.slice(0, initialCount);

  return (
    <div className="command-bar" id="command-bar" role="region" aria-label="Command bar">
      {/* Top Input Bar */}
      <div className="command-bar-inputs-row">
        {/* Regex Field */}
        <div className="command-group" style={{ flex: '1 1 280px' }}>
          <label htmlFor="command-regex-input" className="command-label">
            Regex:
          </label>
          <div className="command-input-wrapper" style={{ width: '100%' }}>
            <input
              id="command-regex-input"
              type="text"
              className={`input-code ${parsedError ? 'has-error' : ''}`}
              style={{ width: '100%' }}
              placeholder="e.g. (a|b)*abb"
              value={regex}
              onChange={handleRegexChange}
              onKeyDown={handleKeyDown}
              aria-invalid={Boolean(parsedError)}
              aria-describedby={parsedError ? 'syntax-error-detail' : undefined}
              autoComplete="off"
              spellCheck="false"
            />
          </div>
        </div>

        {/* String Field */}
        <div className="command-group" style={{ flex: '0 1 200px' }}>
          <label htmlFor="command-string-input" className="command-label">
            Test String:
          </label>
          <input
            id="command-string-input"
            type="text"
            className="input-code"
            style={{ width: '100%' }}
            placeholder="e.g. ababb (or empty)"
            value={inputString}
            onChange={handleStringChange}
            onKeyDown={handleKeyDown}
            autoComplete="off"
            spellCheck="false"
          />
        </div>

        {/* Run String Button */}
        <button
          type="button"
          id="btn-run-string"
          className="btn-run"
          onClick={() => onRun()}
          disabled={loading}
        >
          {loading ? 'Running...' : 'Run string ▶'}
        </button>

        {/* Quiet Examples Dropdown */}
        <div className="command-group">
          <label htmlFor="select-examples" className="command-label">
            Presets:
          </label>
          <select
            id="select-examples"
            className="select-examples"
            onChange={handleSelectExample}
            defaultValue=""
            aria-label="Load a standard regex example"
          >
            {STANDARD_EXAMPLES.map((ex, idx) => (
              <option key={idx} value={ex.label} disabled={!ex.regex}>
                {ex.label}
              </option>
            ))}
          </select>
        </div>

        {/* Recent Regexes Dropdown (if any) */}
        {recentRegexes.length > 0 && (
          <div className="command-group">
            <label htmlFor="select-recent" className="command-label">
              Recent:
            </label>
            <select
              id="select-recent"
              className="select-examples"
              onChange={handleSelectRecent}
              defaultValue=""
              aria-label="Load recently used regular expression"
            >
              <option value="" disabled>
                History ({recentRegexes.length})
              </option>
              {recentRegexes.map((r, idx) => (
                <option key={idx} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Live Syntax Error Underline & Plain Diagnostic Advice */}
      {parsedError && (
        <div className="syntax-error-banner" id="syntax-error-detail" role="alert">
          <div>
            <strong>Syntax error</strong> at position {parsedError.position}
            {regex && parsedError.position < regex.length ? (
              <span> (character <code>{regex[parsedError.position]}</code>)</span>
            ) : null}: {parsedError.message}.
            <div style={{ marginTop: '0.2rem', color: 'var(--ink-slate)' }}>
              <strong>How to fix:</strong> {parsedError.tip}
            </div>
            {regex && regex.length > 0 && (
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px',
                  marginTop: '0.3rem',
                  padding: '0.2rem 0.4rem',
                  background: '#ffffff',
                  border: '1px solid var(--ink-border)',
                  borderRadius: '2px',
                  display: 'inline-block',
                }}
              >
                <div>{regex}</div>
                <div style={{ color: 'var(--red-risk)' }}>
                  {' '.repeat(Math.max(0, Math.min(parsedError.position, regex.length - 1)))}^
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Automatically Generated Test Examples (Requirement 3) */}
      {!parsedError && (
        <div
          className="generated-candidates-panel"
          id="generated-candidates-panel"
          role="region"
          aria-label="Generated Test Inputs"
        >
          {/* Header Row: Filter Tabs & Status */}
          <div className="generated-candidates-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 700, fontSize: 'var(--text-xs)', color: 'var(--ink-slate)' }}>
                Auto-generated test inputs:
              </span>

              {/* Group Filter Tabs */}
              <div className="candidate-filter-tabs" role="tablist" aria-label="Example groups">
                <button
                  type="button"
                  className={`candidate-filter-tab ${filterTab === 'all' ? 'active' : ''}`}
                  onClick={() => setFilterTab('all')}
                  role="tab"
                  aria-selected={filterTab === 'all'}
                >
                  All ({allExamples.length})
                </button>
                <button
                  type="button"
                  className={`candidate-filter-tab match ${filterTab === 'accepted' ? 'active' : ''}`}
                  onClick={() => setFilterTab('accepted')}
                  role="tab"
                  aria-selected={filterTab === 'accepted'}
                >
                  ✓ Accepted ({acceptedList.length})
                </button>
                <button
                  type="button"
                  className={`candidate-filter-tab reject ${filterTab === 'rejected' ? 'active' : ''}`}
                  onClick={() => setFilterTab('rejected')}
                  role="tab"
                  aria-selected={filterTab === 'rejected'}
                >
                  ✕ Rejected ({rejectedList.length})
                </button>
                <button
                  type="button"
                  className={`candidate-filter-tab ${filterTab === 'edge' ? 'active' : ''}`}
                  onClick={() => setFilterTab('edge')}
                  role="tab"
                  aria-selected={filterTab === 'edge'}
                >
                  ⚡ Edge cases ({edgeList.length})
                </button>
              </div>
            </div>

            {/* Right Header Status / Refresh Notice */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '11px' }}>
              {isExamplesStale ? (
                <span style={{ fontStyle: 'italic', color: 'var(--amber-signal)' }}>
                  (Refreshing for updated regex...)
                </span>
              ) : (
                <span style={{ color: 'var(--ink-secondary)' }}>
                  Click candidate to test on tape
                </span>
              )}
            </div>
          </div>

          {/* Limited Language Honesty Notice (if applicable) */}
          {generatedExamples?.limitedLanguageNotice && (
            <div className="limited-language-notice" role="note">
              ℹ️ {generatedExamples.limitedLanguageNotice}
            </div>
          )}

          {/* Interactive Candidate Chips Strip */}
          <div
            className="generated-candidates-chips"
            role="group"
            aria-label="Candidate string options"
          >
            {displayedExamples && displayedExamples.length > 0 ? (
              displayedExamples.map((ex, idx) => {
                const isCurrentInput = inputString === ex.input;
                return (
                  <button
                    key={idx}
                    type="button"
                    className={`candidate-chip ${ex.matches ? 'match' : 'reject'} ${isCurrentInput ? 'selected' : ''}`}
                    onClick={() => {
                      if (onSelectGeneratedExample) onSelectGeneratedExample(ex.input);
                    }}
                    onMouseEnter={() => setInspectedCandidate(ex)}
                    onMouseLeave={() => setInspectedCandidate(null)}
                    disabled={isExamplesStale}
                    title={`${ex.label}: ${ex.reason || ex.description}`}
                    aria-label={`Test string "${ex.displayInput}", ${ex.matches ? 'accepted' : 'rejected'}`}
                  >
                    <span
                      style={{
                        fontWeight: 700,
                        color: ex.matches ? 'var(--green-accept)' : 'var(--red-risk)',
                      }}
                    >
                      {ex.matches ? '✓' : '✕'}
                    </span>
                    <span className="candidate-text">
                      {ex.input === '' ? <em style={{ color: 'var(--amber-signal)' }}>ε (empty)</em> : ex.input}
                    </span>
                    <span className={`candidate-tag ${ex.matches ? 'match' : 'reject'}`}>
                      {ex.matches ? 'Accept' : 'Reject'}
                    </span>
                  </button>
                );
              })
            ) : (
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)' }}>
                {isExamplesStale
                  ? 'Re-evaluating candidates for pattern change...'
                  : 'No examples available in this group.'}
              </span>
            )}

            {/* Show More / Show Fewer & Generate More Actions */}
            {filteredExamples.length > initialCount && (
              <button
                type="button"
                className="btn-quiet-pill"
                onClick={() => setShowAllExamples(!showAllExamples)}
                style={{ fontSize: '11px' }}
              >
                {showAllExamples
                  ? 'Show fewer'
                  : `Show more (${filteredExamples.length - initialCount})`}
              </button>
            )}

            {onGenerateMore && (
              <button
                type="button"
                className="btn-quiet-pill"
                onClick={onGenerateMore}
                title="Synthesize additional edge cases and longer paths"
                style={{ fontSize: '11px' }}
              >
                + Generate more
              </button>
            )}
          </div>

          {/* Interactive Candidate Inspection Tooltip / Reason Callout */}
          {inspectedCandidate && (
            <div className="candidate-reason-callout" role="status">
              <strong>"{inspectedCandidate.displayInput}":</strong> {inspectedCandidate.reason || inspectedCandidate.description}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

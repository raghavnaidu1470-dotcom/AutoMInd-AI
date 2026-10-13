import React from 'react';
import { parseSyntaxError } from '../utils/syntaxValidator.js';

const STANDARD_EXAMPLES = [
  { label: 'Select an example...', regex: '', string: '' },
  { label: 'Ends in abb: (a|b)*abb', regex: '(a|b)*abb', string: 'ababb' },
  { label: 'Alternating binary: (01)*101', regex: '(01)*101', string: '0101101' },
  { label: 'Repeated a then b: a*b+', regex: 'a*b+', string: 'aaabbb' },
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
}) {
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
      // Small timeout to run with newly set values
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

  return (
    <div className="command-bar" id="command-bar" role="region" aria-label="Command bar">
      {/* Regex Field */}
      <div className="command-group" style={{ flex: '1 1 240px' }}>
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
      <div className="command-group" style={{ flex: '0 1 180px' }}>
        <label htmlFor="command-string-input" className="command-label">
          String:
        </label>
        <input
          id="command-string-input"
          type="text"
          className="input-code"
          style={{ width: '100%' }}
          placeholder="e.g. ababb"
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
        {loading ? 'Running...' : 'Run string'}
      </button>

      {/* Quiet Examples Dropdown */}
      <div className="command-group">
        <label htmlFor="select-examples" className="command-label">
          Examples:
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
            {/* Visual character position display with indicator arrow */}
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
    </div>
  );
}

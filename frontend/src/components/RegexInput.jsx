import React from 'react';

const PRESETS = [
  { label: '(a|b)*abb', string: 'ababb', desc: 'Ends in abb' },
  { label: 'a*b+', string: 'aaabbb', desc: 'Zero or more a, one or more b' },
  { label: '(01)*101', string: '0101101', desc: 'Binary pattern' },
  { label: '(a|b)*a(a|b)', string: 'bab', desc: 'Second-to-last is a' },
];

export default function RegexInput({
  regex,
  setRegex,
  inputString,
  setInputString,
  onProcess,
  loading,
  syntaxError,
  clearSyntaxError,
}) {
  const handleSelectPreset = (preset) => {
    if (clearSyntaxError) clearSyntaxError();
    setRegex(preset.label);
    setInputString(preset.string);
  };

  const handleRegexChange = (e) => {
    if (clearSyntaxError) clearSyntaxError();
    setRegex(e.target.value);
  };

  return (
    <div className="glass-panel control-bar" id="regex-control-panel">
      <div className="input-row">
        {/* Regex Input Field */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div className="input-group">
            <span className="input-icon">/</span>
            <input
              id="regex-input-field"
              type="text"
              className={`input-field ${syntaxError ? 'input-error' : ''}`}
              style={syntaxError ? { borderColor: 'rgba(239, 68, 68, 0.6)' } : {}}
              placeholder="Enter Regular Expression (e.g. (a|b)*abb)..."
              value={regex}
              onChange={handleRegexChange}
            />
          </div>

          {/* Inline Syntax Error Alert */}
          {syntaxError && (
            <div
              id="regex-inline-syntax-error"
              style={{
                marginTop: '0.4rem',
                padding: '0.4rem 0.75rem',
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid rgba(239, 68, 68, 0.35)',
                borderRadius: 'var(--radius-sm)',
                color: '#fca5a5',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <span>⚠️</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>{syntaxError}</span>
            </div>
          )}
        </div>

        {/* Candidate String Input */}
        <div className="input-group" style={{ maxWidth: '300px' }}>
          <span className="input-icon">"</span>
          <input
            id="string-input-field"
            type="text"
            className="input-field"
            placeholder="Candidate string (e.g. ababb)..."
            value={inputString}
            onChange={(e) => setInputString(e.target.value)}
          />
        </div>

        {/* Generate / Run Button */}
        <button
          id="btn-generate-automata"
          className="btn-primary"
          onClick={onProcess}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Generate & Explain'}
        </button>
      </div>

      {/* Preset Buttons */}
      <div className="presets-group">
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Quick Presets:</span>
        {PRESETS.map((p) => (
          <button
            key={p.label}
            className="preset-chip"
            onClick={() => handleSelectPreset(p)}
          >
            {p.label} <span style={{ opacity: 0.6 }}>({p.desc})</span>
          </button>
        ))}
      </div>
    </div>
  );
}

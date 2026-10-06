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
}) {
  const handleSelectPreset = (preset) => {
    setRegex(preset.label);
    setInputString(preset.string);
  };

  return (
    <div className="glass-panel control-bar" id="regex-control-panel">
      <div className="input-row">
        {/* Regex Input Field */}
        <div className="input-group">
          <span className="input-icon">/</span>
          <input
            id="regex-input-field"
            type="text"
            className="input-field"
            placeholder="Enter Regular Expression (e.g. (a|b)*abb)..."
            value={regex}
            onChange={(e) => setRegex(e.target.value)}
          />
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

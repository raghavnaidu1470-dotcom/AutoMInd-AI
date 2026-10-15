import React, { useState, useEffect, useRef } from 'react';
import {
  tokenizeRegex,
  explainRegexPlainEnglish,
  checkUnsupportedConstructs,
  SUPPORTED_SYNTAX,
} from '../utils/regexExplainer.js';

export default function RegexExplainer({ regex, onHoverToken }) {
  const [selectedTokenIndex, setSelectedTokenIndex] = useState(null);
  const [showSyntaxModal, setShowSyntaxModal] = useState(false);
  const previouslyFocusedRef = useRef(null);
  const modalCardRef = useRef(null);
  const syntaxCloseBtnRef = useRef(null);

  // Focus management for syntax modal: capture previous element, trap tab focus, and restore on unmount
  useEffect(() => {
    if (showSyntaxModal) {
      previouslyFocusedRef.current = document.activeElement;
      setTimeout(() => {
        syntaxCloseBtnRef.current?.focus();
      }, 50);

      const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          setShowSyntaxModal(false);
          return;
        }

        if (e.key === 'Tab') {
          const modalEl = modalCardRef.current;
          if (!modalEl) return;
          const focusables = Array.from(
            modalEl.querySelectorAll(
              'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
            )
          );
          if (focusables.length === 0) return;
          const first = focusables[0];
          const last = focusables[focusables.length - 1];
          if (e.shiftKey) {
            if (document.activeElement === first || !modalEl.contains(document.activeElement)) {
              e.preventDefault();
              last.focus();
            }
          } else {
            if (document.activeElement === last || !modalEl.contains(document.activeElement)) {
              e.preventDefault();
              first.focus();
            }
          }
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => {
        window.removeEventListener('keydown', handleKeyDown);
        if (previouslyFocusedRef.current && previouslyFocusedRef.current.focus) {
          previouslyFocusedRef.current.focus();
        }
      };
    }
  }, [showSyntaxModal]);

  const unsupportedConstruct = checkUnsupportedConstructs(regex);
  const plainEnglish = explainRegexPlainEnglish(regex);
  const tokens = tokenizeRegex(regex);

  const activeToken =
    selectedTokenIndex !== null ? tokens.find((t) => t.index === selectedTokenIndex) : null;

  return (
    <div className="regex-explainer-panel" id="regex-explainer-panel" role="region" aria-label="Interactive Regex Explanation">
      {/* Unsupported syntax alert if non-regular programming features used */}
      {unsupportedConstruct && (
        <div className="unsupported-feature-banner" role="alert">
          <div>
            <strong>Programming Regex Feature Detected ({unsupportedConstruct.name}):</strong>
            <p style={{ margin: '0.25rem 0', fontSize: 'var(--text-xs)' }}>
              {unsupportedConstruct.explanation}
            </p>
            <span style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>
              AutoMind AI models formal regular languages (Chomsky Type-3) using finite automata.
            </span>
          </div>
        </div>
      )}

      {/* Top Header: Plain English Narrative & Syntax Button */}
      <div className="regex-explainer-header">
        <div style={{ flex: 1 }}>
          <div className="explainer-heading-row">
            <span className="explainer-pill">Plain-English Meaning</span>
            <button
              type="button"
              className="btn-quiet-pill"
              onClick={() => setShowSyntaxModal(true)}
              aria-label="View supported formal syntax guide"
            >
              📖 Formal Syntax Guide
            </button>
          </div>
          <div className="explainer-narrative" id="regex-plain-english-text">
            {plainEnglish}
          </div>
        </div>
      </div>

      {/* Interactive Token Strip */}
      {tokens.length > 0 && (
        <div className="explainer-token-section">
          <div className="explainer-section-label">
            <span>Parsed Tokens (hover or click to inspect):</span>
            {activeToken && (
              <span className="token-active-type">
                Type: <strong>{activeToken.type}</strong>
              </span>
            )}
          </div>

          <div className="explainer-tokens-strip" role="group" aria-label="Regex tokens">
            {tokens.map((tok) => {
              const isSelected = selectedTokenIndex === tok.index;
              return (
                <button
                  key={tok.index}
                  type="button"
                  className={`token-chip ${tok.type} ${isSelected ? 'selected' : ''}`}
                  onMouseEnter={() => {
                    setSelectedTokenIndex(tok.index);
                    if (onHoverToken) onHoverToken(tok);
                  }}
                  onMouseLeave={() => {
                    if (onHoverToken) onHoverToken(null);
                  }}
                  onClick={() => setSelectedTokenIndex(tok.index)}
                  aria-label={`${tok.label}: ${tok.meaning}`}
                  title={`${tok.label}: ${tok.meaning}`}
                >
                  <span className="token-char">{tok.char}</span>
                  <span className="token-sublabel">{tok.type}</span>
                </button>
              );
            })}
          </div>

          {/* Active Token Detail Callout */}
          {activeToken ? (
            <div className="token-meaning-callout" role="status">
              <strong>{activeToken.label}:</strong> {activeToken.meaning}
            </div>
          ) : (
            <div className="token-meaning-callout-hint">
              Hover over or click any token above to see its formal definition and meaning.
              <span style={{ display: 'block', fontSize: '11px', color: 'var(--ink-secondary)', marginTop: '0.2rem' }}>
                Note: 1-to-1 token-to-graph node mapping is unavailable because finite automata states are synthesized via global transformations (Thompson NFA composition, powerset determinization, and Hopcroft partitioning). Use the State Inspector to view precise state origins.
              </span>
            </div>
          )}
        </div>
      )}

      {/* Supported Formal Syntax Modal */}
      {showSyntaxModal && (
        <div
          className="modal-backdrop"
          role="dialog"
          aria-modal="true"
          aria-label="Supported Formal Regex Syntax"
          onClick={(e) => {
            if (e.target.classList.contains('modal-backdrop')) setShowSyntaxModal(false);
          }}
        >
          <div className="modal-card" ref={modalCardRef}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontSize: 'var(--text-md)' }}>
                Supported Formal Regex Syntax (Chomsky Type-3)
              </h3>
              <button
                ref={syntaxCloseBtnRef}
                type="button"
                className="btn-quiet"
                onClick={() => setShowSyntaxModal(false)}
                aria-label="Close syntax guide"
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)', marginBottom: '0.85rem' }}>
                AutoMind AI recognizes pure regular languages convertible into Finite Automata (NFAs and DFAs) under
                <strong> full-string acceptance semantics</strong> (<em>w ∈ L(r)</em>). For a fixed compiled DFA,
                string recognition evaluates in strictly linear time <em>O(|w|)</em> without risk of catastrophic backtracking.
                (Note: compiling or determinizing a large NFA via subset construction has worst-case exponential state complexity <em>O(2<sup>|Q|</sup>)</em>).
              </p>

              <table className="syntax-table">
                <thead>
                  <tr>
                    <th>Syntax</th>
                    <th>Formal Operation</th>
                    <th>Formal Definition</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {SUPPORTED_SYNTAX.map((syn, idx) => (
                    <tr key={idx}>
                      <td><code>{syn.construct}</code></td>
                      <td><strong>{syn.name}</strong></td>
                      <td><code style={{ color: 'var(--amber-signal)' }}>{syn.formal}</code></td>
                      <td>{syn.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'var(--amber-tint)', border: '1px solid var(--amber-signal)', borderRadius: 'var(--radius-control)', fontSize: 'var(--text-xs)' }}>
                <strong style={{ display: 'block', marginBottom: '0.35rem' }}>Theory of Computation Precision Notes:</strong>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <li>
                    <strong>Lookaround Assertions:</strong> Lookarounds over regular subpatterns can still describe regular languages (due to closure under intersection and complement), but this application does not currently support them.
                  </li>
                  <li>
                    <strong>Backreferences:</strong> Backreferences can describe non-regular languages in general (for example, {'{'}ww | w ∈ Σ*{'}'} is non-regular for alphabets containing at least two symbols, while checking whether a given string consists of two identical halves is straightforward). Finite automata cannot support general backreferences due to bounded memory. (This is separate from general regex matching with backreferences, which is NP-complete.)
                  </li>
                  <li>
                    <strong>Greedy vs Lazy Quantifiers:</strong> Greedy and lazy quantifiers affect match selection priority during substring search in backtracking engines, but recognize the exact same formal language for full-string membership in the supported regular subset.
                  </li>
                  <li>
                    <strong>DFA Complexity:</strong> String recognition on a fixed compiled DFA is linear <em>O(|w|)</em>; however, compiling/determinizing an NFA via subset construction has worst-case exponential state complexity <em>O(2<sup>|Q|</sup>)</em>.
                  </li>
                </ul>
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn-run"
                onClick={() => setShowSyntaxModal(false)}
              >
                Close Guide
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

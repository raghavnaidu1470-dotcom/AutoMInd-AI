import React, { useState, useEffect, useRef } from 'react';
import { computeMinimizationDiff } from '../utils/minimizationDiff.js';

export default function MinimizationModal({ isOpen, onClose, dfa, minDfa }) {
  const [showAlgorithmDetails, setShowAlgorithmDetails] = useState(false);
  const previouslyFocusedRef = useRef(null);
  const modalCardRef = useRef(null);
  const closeBtnRef = useRef(null);

  // Focus management: capture previous element, trap tab focus, and restore on unmount
  useEffect(() => {
    if (isOpen) {
      previouslyFocusedRef.current = document.activeElement;
      setTimeout(() => {
        closeBtnRef.current?.focus();
      }, 50);

      const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          onClose();
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
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const diff = computeMinimizationDiff(dfa, minDfa);
  if (!diff) return null;

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Hopcroft Minimization Comparison"
      onClick={(e) => {
        if (e.target.classList.contains('modal-backdrop')) onClose();
      }}
    >
      <div className="modal-card" ref={modalCardRef} style={{ maxWidth: '680px' }}>
        <div className="modal-header">
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--amber-signal)', fontWeight: 700 }}>
              DFA Optimization · Hopcroft's Algorithm
            </div>
            <h3 style={{ margin: '0.2rem 0 0 0', fontSize: 'var(--text-md)' }}>
              Minimization Before & After Comparison
            </h3>
          </div>
          <button
            ref={closeBtnRef}
            type="button"
            className="btn-quiet"
            onClick={onClose}
            aria-label="Close minimization comparison"
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          {/* Top Statistics Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.6rem', marginBottom: '1rem' }}>
            <div className="stat-card">
              <span className="stat-label">Original DFA States</span>
              <span className="stat-number">{diff.originalCount}</span>
              <span className="stat-sub">From subset construction</span>
            </div>
            <div className="stat-card highlight">
              <span className="stat-label">Minimized DFA States</span>
              <span className="stat-number">{diff.minimizedCount}</span>
              <span className="stat-sub">Minimal equivalent DFA</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">States Eliminated</span>
              <span className="stat-number">{diff.statesEliminated}</span>
              <span className="stat-sub">{diff.reductionPercent}% reduction</span>
            </div>
          </div>

          {/* Plain Language Summary */}
          <div className="engineering-callout" style={{ marginBottom: '1rem' }}>
            <div className="engineering-callout-title">Equivalence verdict</div>
            <p style={{ margin: 0, fontSize: 'var(--text-xs)', lineHeight: 1.5 }}>
              {diff.summary}
            </p>
          </div>

          {/* Merged States Table */}
          <div style={{ marginBottom: '1rem' }}>
            <h4 style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', color: 'var(--ink-secondary)', marginBottom: '0.4rem' }}>
              State Partition & Merging Breakdown
            </h4>
            <div style={{ maxHeight: '220px', overflowY: 'auto', border: 'var(--border-rule)', borderRadius: 'var(--radius-control)' }}>
              <table className="syntax-table" style={{ margin: 0 }}>
                <thead>
                  <tr>
                    <th>Minimized State</th>
                    <th>Merged Original DFA States</th>
                    <th>Accepting?</th>
                    <th>Why Merged / Maintained</th>
                  </tr>
                </thead>
                <tbody>
                  {diff.mergeGroups.map((g) => (
                    <tr key={g.minimizedId}>
                      <td>
                        <strong style={{ fontFamily: 'var(--font-mono)' }}>{g.minimizedId}</strong>
                        {g.isStart && <span className="state-badge-start">start</span>}
                      </td>
                      <td>
                        <code style={{ fontFamily: 'var(--font-mono)' }}>
                          {'{' + g.mergedDfaStates.join(', ') + '}'}
                        </code>
                      </td>
                      <td>
                        {g.isAccepting ? (
                          <span style={{ color: 'var(--green-accept)', fontWeight: 700 }}>✓ Accepting</span>
                        ) : (
                          <span style={{ color: 'var(--ink-secondary)' }}>Non-accepting</span>
                        )}
                      </td>
                      <td style={{ fontSize: '11px', color: 'var(--ink-slate)' }}>
                        {g.explanation}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Progressive Disclosure: Optional Algorithm Details */}
          <div>
            <button
              type="button"
              className="btn-quiet"
              style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)' }}
              onClick={() => setShowAlgorithmDetails(!showAlgorithmDetails)}
            >
              {showAlgorithmDetails ? '▼ Hide Hopcroft Algorithm Internals' : '▶ How does Hopcroft\'s Algorithm work? (Optional)'}
            </button>

            {showAlgorithmDetails && (
              <div style={{ marginTop: '0.5rem', padding: '0.65rem', background: 'var(--paper-subtle)', borderRadius: 'var(--radius-control)', fontSize: 'var(--text-xs)', lineHeight: 1.45 }}>
                <p style={{ margin: '0 0 0.4rem 0' }}>
                  <strong>Hopcroft's Partition Refinement Algorithm</strong> starts with two initial sets: accepting states <em>F</em> and non-accepting states <em>Q \ F</em>.
                </p>
                <p style={{ margin: '0 0 0.4rem 0' }}>
                  At each iteration, it selects a partition and an alphabet symbol <em>c</em>. If states in the partition transition to different target partitions on <em>c</em>, the partition is split. This refinement repeats until all remaining states in each block are provably indistinguishable on any future string suffix.
                </p>
                <span style={{ color: 'var(--ink-secondary)', fontStyle: 'italic' }}>
                  Time complexity: O(|Σ| · |Q| log |Q|), making it the most efficient DFA minimization algorithm known.
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button
            type="button"
            className="btn-run"
            onClick={onClose}
          >
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
}

import React from 'react';

/**
 * TraceTable Component
 * ====================
 * Continuous-form green-bar printer paper execution trace log.
 * Striped alternating rows with interactive linkage: clicking a row jumps
 * directly to that step on the diagram and input tape.
 */

export default function TraceTable({ simulationResult, currentStepIndex, onSelectStep }) {
  const steps = simulationResult?.steps || [];

  if (steps.length === 0) {
    return (
      <div style={{ padding: '0.8rem', fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)' }}>
        No simulation trace available. Run a candidate string to inspect execution steps.
      </div>
    );
  }

  return (
    <div className="greenbar-table-container" role="region" aria-label="Execution Trace Log">
      <table className="greenbar-table">
        <thead>
          <tr>
            <th scope="col">Step</th>
            <th scope="col">Char</th>
            <th scope="col">Source</th>
            <th scope="col">Sym</th>
            <th scope="col">Target</th>
          </tr>
        </thead>
        <tbody>
          {steps.map((st, idx) => {
            const isActive = idx === currentStepIndex;
            const fromStr = st.current_states?.join(', ') || 'q0';
            const toStr = st.next_states?.join(', ') || 'q0';
            const sym = st.symbol_read || 'ε';

            return (
              <tr
                key={idx}
                className={`greenbar-row ${isActive ? 'active' : ''}`}
                onClick={() => onSelectStep(idx)}
                tabIndex={0}
                role="button"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectStep(idx);
                  }
                }}
                aria-label={`Jump to step ${idx}, read character ${sym} from ${fromStr} to ${toStr}`}
              >
                <td>#{idx}</td>
                <td>{sym}</td>
                <td>{fromStr}</td>
                <td>{st.transition_taken?.symbol || sym}</td>
                <td>{toStr}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

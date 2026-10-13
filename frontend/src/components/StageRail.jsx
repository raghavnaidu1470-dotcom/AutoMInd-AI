import React from 'react';

/**
 * StageRail Component
 * ===================
 * A slim sequential rail displaying the pipeline phases:
 * 1. Regex
 * 2. NFA
 * 3. DFA
 * 4. Minimized DFA
 * 5. Run
 * 6. ReDoS check
 * Each item displays its relevant state count or verdict.
 */

export default function StageRail({
  activeStage,
  setActiveStage,
  nfaStateCount,
  dfaStateCount,
  minDfaStateCount,
  simulationResult,
  redosRisk,
  syntaxError,
}) {
  const stages = [
    {
      id: 'regex',
      num: '1',
      label: 'Regex',
      detail: syntaxError ? 'Syntax error' : 'Valid pattern',
      badgeClass: syntaxError ? 'error' : '',
    },
    {
      id: 'nfa',
      num: '2',
      label: 'NFA',
      detail: nfaStateCount !== undefined ? `${nfaStateCount} states` : 'Thompson',
    },
    {
      id: 'dfa',
      num: '3',
      label: 'DFA',
      detail: dfaStateCount !== undefined ? `${dfaStateCount} states` : 'Subset',
    },
    {
      id: 'minimized_dfa',
      num: '4',
      label: 'Minimized DFA',
      detail: minDfaStateCount !== undefined ? `${minDfaStateCount} states` : 'Hopcroft',
    },
    {
      id: 'run',
      num: '5',
      label: 'Run',
      detail: simulationResult
        ? simulationResult.accepted
          ? 'Accepted'
          : 'Rejected'
        : 'Ready',
    },
    {
      id: 'redos',
      num: '6',
      label: 'ReDoS check',
      detail: redosRisk ? `${redosRisk} risk` : 'Screening',
    },
  ];

  return (
    <nav className="stage-rail" id="stage-rail" aria-label="Pipeline Stages">
      <div className="stage-rail-title">Pipeline</div>
      {stages.map((st) => {
        const isActive = activeStage === st.id;
        return (
          <button
            key={st.id}
            type="button"
            className={`stage-item ${isActive ? 'active' : ''}`}
            onClick={() => setActiveStage(st.id)}
            aria-current={isActive ? 'step' : undefined}
          >
            <div className="stage-item-header">
              <span className="stage-item-num">{st.num}.</span>
              <span>{st.label}</span>
            </div>
            <div className={`stage-item-badge ${st.badgeClass || ''}`}>
              {st.detail}
            </div>
          </button>
        );
      })}
    </nav>
  );
}

import React from 'react';

/**
 * StageRail Component
 * ===================
 * Navigation sidebar organized around the 4 core learning phases:
 * 1. Understand Regex
 * 2. Explore Automata (NFA, DFA, Minimized DFA)
 * 3. Test a String
 * 4. Investigate ReDoS
 *
 * Includes view mode toggle (Beginner vs Advanced), prominent "Walk me through this" action,
 * and persistent sidebar visibility controls.
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
  isAdvancedMode = false,
  setIsAdvancedMode,
  onOpenWalkthrough,
  onCloseRail,
}) {
  const phases = [
    {
      id: 'understand',
      stageTarget: 'minimized_dfa',
      num: '1',
      title: 'Understand Regex',
      subtitle: syntaxError ? 'Syntax error' : 'Plain English & tokens',
      badgeClass: syntaxError ? 'error' : 'ready',
      isActive: activeStage === 'regex' || activeStage === 'understand',
      onClick: () => setActiveStage('minimized_dfa'),
    },
    {
      id: 'automata',
      num: '2',
      title: 'Explore Automata',
      subtitle: `${minDfaStateCount ?? 0} min / ${dfaStateCount ?? 0} dfa states`,
      isActive: ['nfa', 'dfa', 'minimized_dfa'].includes(activeStage),
      substages: [
        { id: 'nfa', label: 'NFA', count: nfaStateCount, sub: "Thompson's" },
        { id: 'dfa', label: 'DFA', count: dfaStateCount, sub: 'Subset' },
        { id: 'minimized_dfa', label: 'Minimized', count: minDfaStateCount, sub: "Hopcroft's" },
      ],
    },
    {
      id: 'test',
      stageTarget: activeStage === 'nfa' ? 'nfa' : activeStage === 'dfa' ? 'dfa' : 'minimized_dfa',
      num: '3',
      title: 'Test a String',
      subtitle: simulationResult
        ? simulationResult.accepted
          ? '✓ String accepted'
          : '✕ String rejected'
        : 'Tape simulator ready',
      badgeClass: simulationResult
        ? simulationResult.accepted
          ? 'accepted'
          : 'rejected'
        : '',
      isActive: false, // In Studio view, tape is always pinned at bottom
      onClick: () => {
        // Focus the input tape or string field
        const inputEl = document.getElementById('command-string-input');
        if (inputEl) inputEl.focus();
      },
    },
    {
      id: 'redos',
      num: '4',
      title: 'Investigate ReDoS',
      subtitle: redosRisk ? `${redosRisk} risk` : 'Backtracking analysis',
      badgeClass: redosRisk === 'exponential' || redosRisk === 'polynomial' ? 'error' : '',
      isActive: activeStage === 'redos',
      onClick: () => setActiveStage('redos'),
    },
  ];

  return (
    <nav className="stage-rail" id="stage-rail" aria-label="Learning Flow Steps">
      {/* Header with Title and Close Button */}
      <div className="stage-rail-header">
        <span className="stage-rail-title">Learning Flow</span>
        {onCloseRail && (
          <button
            type="button"
            id="btn-close-rail"
            className="btn-quiet"
            onClick={onCloseRail}
            title="Collapse navigation sidebar"
            aria-label="Collapse navigation sidebar"
            style={{ padding: '0.1rem 0.35rem', fontSize: '11px' }}
          >
            ✕
          </button>
        )}
      </div>

      {/* Prominent Walk Me Through This Action */}
      {onOpenWalkthrough && (
        <button
          type="button"
          id="btn-walk-me-through"
          className="btn-walkthrough"
          onClick={onOpenWalkthrough}
          aria-label="Start interactive beginner walkthrough"
        >
          <span style={{ fontSize: '14px' }}>🎓</span>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontWeight: 700, fontSize: '12px' }}>Walk me through this</div>
            <div style={{ fontSize: '10px', color: 'var(--ink-secondary)' }}>Interactive beginner guide</div>
          </div>
        </button>
      )}

      {/* 4 Phases List */}
      <div className="stage-phases-list">
        {/* Phase 1: Understand Regex */}
        <button
          type="button"
          className={`stage-item ${phases[0].isActive ? 'active' : ''}`}
          onClick={phases[0].onClick}
        >
          <div className="stage-item-header">
            <span className="stage-item-num">1.</span>
            <span>Understand Regex</span>
          </div>
          <div className={`stage-item-badge ${phases[0].badgeClass}`}>
            {phases[0].subtitle}
          </div>
        </button>

        {/* Phase 2: Explore Automata */}
        <div className={`stage-item-group ${phases[1].isActive ? 'active' : ''}`}>
          <div className="stage-item-header" style={{ padding: '0.4rem 0.65rem 0.2rem' }}>
            <span className="stage-item-num">2.</span>
            <span>Explore Automata</span>
          </div>
          <div className="automata-subtabs-list">
            {phases[1].substages.map((sub) => {
              const isSelected = activeStage === sub.id;
              return (
                <button
                  key={sub.id}
                  type="button"
                  className={`substage-pill ${isSelected ? 'selected' : ''}`}
                  onClick={() => setActiveStage(sub.id)}
                  aria-pressed={isSelected}
                  title={`${sub.label} (${sub.sub}): ${sub.count ?? 0} states`}
                >
                  <span style={{ fontWeight: 600 }}>{sub.label}</span>
                  <span className="substage-count">{sub.count ?? 0}q</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Phase 3: Test a String */}
        <button
          type="button"
          className="stage-item"
          onClick={phases[2].onClick}
          title="Scroll or focus candidate string testing"
        >
          <div className="stage-item-header">
            <span className="stage-item-num">3.</span>
            <span>Test a String</span>
          </div>
          <div className={`stage-item-badge ${phases[2].badgeClass}`}>
            {phases[2].subtitle}
          </div>
        </button>

        {/* Phase 4: Investigate ReDoS */}
        <button
          type="button"
          className={`stage-item ${phases[3].isActive ? 'active' : ''}`}
          onClick={phases[3].onClick}
        >
          <div className="stage-item-header">
            <span className="stage-item-num">4.</span>
            <span>Investigate ReDoS</span>
          </div>
          <div className={`stage-item-badge ${phases[3].badgeClass}`}>
            {phases[3].subtitle}
          </div>
        </button>
      </div>

      {/* View Mode Toggle: Beginner (Guided) vs Advanced (Diagnostics) */}
      <div className="stage-rail-footer">
        <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--ink-secondary)', marginBottom: '0.3rem', fontWeight: 600 }}>
          View Mode
        </div>
        <div className="view-mode-toggle" role="group" aria-label="Interface mode">
          <button
            type="button"
            className={`btn-mode ${!isAdvancedMode ? 'active' : ''}`}
            onClick={() => setIsAdvancedMode(false)}
            aria-pressed={!isAdvancedMode}
          >
            Beginner
          </button>
          <button
            type="button"
            className={`btn-mode ${isAdvancedMode ? 'active' : ''}`}
            onClick={() => setIsAdvancedMode(true)}
            aria-pressed={isAdvancedMode}
          >
            Advanced
          </button>
        </div>
      </div>
    </nav>
  );
}

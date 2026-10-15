import React, { useEffect, useState, useCallback, useRef } from 'react';

/**
 * ExecutionStepper Component (Pinned Tape Transport Bar & Guided Simulation)
 * =========================================================================
 * Mechanical-feeling tape transport pinned to the viewport bottom.
 * Renders individual rectangular cells with an advancing signal-amber read head,
 * full keyboard controls (Space, ArrowLeft, ArrowRight), scrubber, speed selector,
 * educational step-by-step reasoning callout, and plain-language termination verdicts.
 */

export default function ExecutionStepper({
  simulationResult,
  inputString = '',
  currentStepIndex = 0,
  setCurrentStepIndex,
  isNfa = false,
  automatonType = 'DFA',
}) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1); // 0.5x, 1x, 2x, 4x

  const steps = simulationResult?.steps || [];
  const maxStep = Math.max(0, steps.length - 1);
  const currentStep = steps[currentStepIndex] || null;
  const isFinished = currentStepIndex >= maxStep && steps.length > 0;
  const isAccepted = Boolean(simulationResult?.accepted);

  const tapeContainerRef = useRef(null);

  // Playback loop
  useEffect(() => {
    let timer = null;
    if (isPlaying && maxStep > 0) {
      const delay = Math.round(650 / speed);
      timer = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= maxStep) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, delay);
    }
    return () => clearInterval(timer);
  }, [isPlaying, maxStep, speed, setCurrentStepIndex]);

  // Keep active tape cell in view via horizontal scroll
  useEffect(() => {
    if (!tapeContainerRef.current) return;
    const activeCell = tapeContainerRef.current.querySelector('.tape-cell.active');
    if (activeCell) {
      activeCell.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  }, [currentStepIndex]);

  // Keyboard navigation: Space = Play/Pause, ArrowLeft = Prev, ArrowRight = Next
  const handleKeyDown = useCallback(
    (e) => {
      // Do not interfere if a modal is open or if user is focused inside an input / editable field
      if (document.querySelector('.modal-backdrop')) return;
      const tag = document.activeElement?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select' || document.activeElement?.isContentEditable) return;

      if (e.code === 'Space') {
        e.preventDefault();
        if (currentStepIndex >= maxStep) {
          setCurrentStepIndex(0);
          setIsPlaying(true);
        } else {
          setIsPlaying((p) => !p);
        }
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        setIsPlaying(false);
        setCurrentStepIndex((p) => Math.max(0, p - 1));
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        setIsPlaying(false);
        setCurrentStepIndex((p) => Math.min(maxStep, p + 1));
      }
    },
    [currentStepIndex, maxStep, setCurrentStepIndex]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Formatting active states
  const activeStates = currentStep?.current_states || [];
  const nextStates = currentStep?.next_states || [];
  const activeStatesText =
    activeStates.length > 0
      ? `{${activeStates.join(', ')}}`
      : simulationResult?.final_states?.length
      ? `{${simulationResult.final_states.join(', ')}}`
      : '{start}';

  // Consumed vs remaining characters
  const chars = inputString.length > 0 ? inputString.split('') : [];
  const consumedCount = Math.min(currentStepIndex, chars.length);
  const remainingCount = Math.max(0, chars.length - consumedCount);

  // Step explanation derivation
  let stepExplanation = '';
  if (currentStepIndex === 0) {
    stepExplanation = isNfa
      ? `Step 0: Initial configuration. Active state set is ${activeStatesText} (including start state and any states reachable via ε-closure).`
      : `Step 0: Initial configuration. Machine begins at start state ${activeStatesText}. No symbols read yet.`;
  } else if (currentStep) {
    const sym = currentStep.symbol_read;
    const trans = currentStep.transition_taken;
    if (trans) {
      if (isNfa) {
        stepExplanation = `Step ${currentStepIndex}: Read symbol '${sym}'. Machine transitioned from states ${activeStatesText} to next active set {${nextStates.join(', ')}} via ε-closure over all matching transitions.`;
      } else {
        stepExplanation = `Step ${currentStepIndex}: Read symbol '${sym}'. Traversed deterministic transition ${trans.from_state} --${trans.symbol}--> ${trans.to_state}. Machine is now in state ${trans.to_state}.`;
      }
    } else {
      stepExplanation = `Step ${currentStepIndex}: Attempted to read symbol '${sym}', but no valid transition exists from ${activeStatesText}. Machine halted.`;
    }
  }

  // Plain language verdict
  let verdictMessage = '';
  if (isFinished) {
    if (isAccepted) {
      verdictMessage = `✓ Accepted: Reached accepting state ${activeStatesText} after consuming entire input (${maxStep} steps).`;
    } else {
      if (currentStep?.symbol_read && !currentStep?.transition_taken) {
        verdictMessage = `✕ Rejected: Stuck at character '${currentStep.symbol_read}' with no outgoing transition from ${activeStatesText}.`;
      } else {
        verdictMessage = `✕ Rejected: Input fully consumed, but final active state ${activeStatesText} is not an accepting state.`;
      }
    }
  }

  // Screen reader live description
  const liveAnnouncement = isFinished
    ? verdictMessage
    : `Step ${currentStepIndex} of ${maxStep}. Reading character '${chars[currentStepIndex - 1] || 'start'}'. Active states: ${activeStatesText}.`;

  return (
    <footer className="tape-transport-bar" id="tape-transport-bar" role="region" aria-label="Tape Transport Controls">
      {/* Invisible Screen Reader Announcement */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {liveAnnouncement}
      </div>

      {/* Guided Step Explanation Bar */}
      <div className="guided-step-banner" role="status">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1 }}>
          <span className="guided-step-badge">
            {isFinished ? 'Simulation Complete' : `Step ${currentStepIndex} / ${maxStep}`}
          </span>
          <span className="guided-step-text">
            {isFinished ? verdictMessage : stepExplanation}
          </span>
        </div>

        {isNfa && activeStates.length > 1 && (
          <span className="nfa-branching-tag" title="In NFAs, multiple active states represent all valid branches explored simultaneously">
            Nondeterministic branch: {activeStates.length} active states
          </span>
        )}
      </div>

      <div className="tape-transport-controls">
        {/* Step Buttons Group */}
        <div className="tape-btn-group" role="group" aria-label="Playback controls">
          <button
            type="button"
            className="btn-transport"
            onClick={() => {
              setIsPlaying(false);
              setCurrentStepIndex(0);
            }}
            disabled={currentStepIndex === 0}
            title="Reset to step 0 (First)"
            aria-label="Reset to step 0"
          >
            |◀ Reset
          </button>

          <button
            type="button"
            className="btn-transport"
            onClick={() => {
              setIsPlaying(false);
              setCurrentStepIndex((p) => Math.max(0, p - 1));
            }}
            disabled={currentStepIndex === 0}
            title="Step backward (Left arrow)"
            aria-label="Step backward"
          >
            ◀ Back
          </button>

          <button
            type="button"
            className="btn-transport primary"
            onClick={() => {
              if (currentStepIndex >= maxStep) setCurrentStepIndex(0);
              setIsPlaying(!isPlaying);
            }}
            disabled={maxStep === 0}
            title="Play or pause (Spacebar)"
            aria-label={isPlaying ? 'Pause simulation' : 'Play simulation'}
          >
            {isPlaying ? '❚❚ Pause' : '▶ Play'}
          </button>

          <button
            type="button"
            className="btn-transport"
            onClick={() => {
              setIsPlaying(false);
              setCurrentStepIndex((p) => Math.min(maxStep, p + 1));
            }}
            disabled={currentStepIndex >= maxStep}
            title="Step forward (Right arrow)"
            aria-label="Step forward"
          >
            Next ▶
          </button>

          <button
            type="button"
            className="btn-transport"
            onClick={() => {
              setIsPlaying(false);
              setCurrentStepIndex(maxStep);
            }}
            disabled={currentStepIndex >= maxStep}
            title="Jump to completion"
            aria-label="Jump to completion"
          >
            Last ▶|
          </button>
        </div>

        {/* Scrubber Range Input */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: '1 1 200px', maxWidth: '300px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)' }}>Scrub:</span>
          <input
            type="range"
            min="0"
            max={maxStep}
            value={currentStepIndex}
            onChange={(e) => {
              setIsPlaying(false);
              setCurrentStepIndex(parseInt(e.target.value, 10));
            }}
            aria-label="Simulation step scrubber"
            style={{ width: '100%', cursor: 'pointer' }}
          />
        </div>

        {/* Speed Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)' }}>Speed:</span>
          <select
            className="select-examples"
            style={{ padding: '0.2rem 0.4rem', fontSize: 'var(--text-xs)' }}
            value={speed}
            onChange={(e) => setSpeed(parseFloat(e.target.value))}
            aria-label="Simulation playback speed"
          >
            <option value="0.5">0.5×</option>
            <option value="1">1×</option>
            <option value="2">2×</option>
            <option value="4">4×</option>
          </select>
        </div>
      </div>

      {/* Physical-feeling Tape Character Cells */}
      <div className="tape-cells-wrapper" ref={tapeContainerRef} role="list" aria-label="Input Tape">
        {chars.length === 0 ? (
          <div className="tape-cell active" role="listitem">
            <span className="tape-read-head" aria-hidden="true" />
            <span style={{ fontStyle: 'italic', color: 'var(--amber-signal)' }}>ε (empty string)</span>
          </div>
        ) : (
          chars.map((char, idx) => {
            const isConsumed = idx < currentStepIndex;
            const isCurrent = idx === currentStepIndex - 1 || (currentStepIndex === 0 && idx === 0);
            const isExactActive = idx === currentStepIndex - 1;

            return (
              <div
                key={idx}
                className={`tape-cell ${isConsumed ? 'consumed' : ''} ${isExactActive ? 'active' : ''}`}
                role="listitem"
                aria-label={`Character ${char} at position ${idx}, ${isConsumed ? 'consumed' : 'pending'}`}
              >
                {isExactActive && <span className="tape-read-head" aria-hidden="true" />}
                {char}
              </div>
            );
          })
        )}
      </div>

      {/* Tape Status Line & Plain-Language Verdict */}
      <div className="tape-status-line">
        <div>
          <span>
            Step <strong>{currentStepIndex}</strong> / {maxStep}
          </span>
          <span style={{ margin: '0 0.5rem', color: 'var(--ink-border)' }}>|</span>
          <span>
            Active: <strong>{activeStatesText}</strong>
            {isNfa && activeStates.length > 1 ? ` (${activeStates.length} states)` : ''}
          </span>
          <span style={{ margin: '0 0.5rem', color: 'var(--ink-border)' }}>|</span>
          <span>
            Tape: {consumedCount} consumed, {remainingCount} remaining
          </span>
        </div>

        {verdictMessage && (
          <div
            className={`verdict-text ${isAccepted ? 'accepted' : 'rejected'}`}
            id="simulation-verdict"
            role="status"
          >
            {verdictMessage}
          </div>
        )}
      </div>
    </footer>
  );
}

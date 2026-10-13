import React, { useEffect, useState, useCallback, useRef } from 'react';

/**
 * ExecutionStepper Component (Pinned Tape Transport Bar)
 * ========================================================
 * Mechanical-feeling tape transport pinned to the viewport bottom.
 * Renders individual rectangular cells with an advancing signal-amber read head,
 * full keyboard controls (Space, ArrowLeft, ArrowRight), scrubber, speed selector,
 * aria-live speech announcements, and plain-language termination verdicts.
 */

export default function ExecutionStepper({
  simulationResult,
  inputString = '',
  currentStepIndex = 0,
  setCurrentStepIndex,
  isNfa = false,
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
      // Don't capture keyboard shortcuts if user is typing in a form input
      const tag = document.activeElement?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

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
  const activeStatesText =
    activeStates.length > 0
      ? `{${activeStates.join(', ')}}`
      : simulationResult?.final_states?.length
      ? `{${simulationResult.final_states.join(', ')}}`
      : '{q0}';

  // Consumed vs remaining characters
  const chars = inputString.length > 0 ? inputString.split('') : [];
  const consumedCount = Math.min(currentStepIndex, chars.length);
  const remainingCount = Math.max(0, chars.length - consumedCount);

  // Plain language verdict
  let verdictMessage = '';
  if (isFinished) {
    if (isAccepted) {
      verdictMessage = `Accepted: reached accepting state ${activeStatesText} after ${maxStep} steps.`;
    } else {
      if (currentStep?.symbol_read && !currentStep?.transition_taken) {
        verdictMessage = `Rejected: no transition for '${currentStep.symbol_read}' from ${activeStatesText}.`;
      } else {
        verdictMessage = `Rejected: terminated in non-accepting state ${activeStatesText}.`;
      }
    }
  }

  // Aria live text description
  const liveAnnouncement = isFinished
    ? verdictMessage
    : `Step ${currentStepIndex} of ${maxStep}. Reading character '${chars[currentStepIndex - 1] || 'start'}'. Active states: ${activeStatesText}.`;

  return (
    <footer className="tape-transport-bar" id="tape-transport-bar" role="region" aria-label="Tape Transport Controls">
      {/* Invisible Screen Reader Announcement */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {liveAnnouncement}
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
            title="Jump to start (First)"
            aria-label="Jump to start"
          >
            |◀ First
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
            Step ▶
          </button>

          <button
            type="button"
            className="btn-transport"
            onClick={() => {
              setIsPlaying(false);
              setCurrentStepIndex(maxStep);
            }}
            disabled={currentStepIndex >= maxStep}
            title="Jump to end (Last)"
            aria-label="Jump to end"
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
            ε
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
            {isNfa && activeStates.length > 1 ? ` (${activeStates.length} active states)` : ''}
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

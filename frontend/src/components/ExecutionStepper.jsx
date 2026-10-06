import React, { useEffect, useState } from 'react';

export default function ExecutionStepper({
  simulationResult,
  inputString,
  currentStepIndex,
  setCurrentStepIndex,
}) {
  const [isPlaying, setIsPlaying] = useState(false);
  const steps = simulationResult?.steps || [];
  const maxStep = Math.max(steps.length - 1, 0);

  // Playback timer loop
  useEffect(() => {
    let timer = null;
    if (isPlaying) {
      timer = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= maxStep) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 700);
    }
    return () => clearInterval(timer);
  }, [isPlaying, maxStep, setCurrentStepIndex]);

  const currentStep = steps[currentStepIndex] || null;
  const isFinished = currentStepIndex >= maxStep && steps.length > 0;
  const isAccepted = simulationResult?.accepted;

  return (
    <div className="glass-panel stepper-bar" id="execution-stepper-panel">
      {/* Control buttons */}
      <div className="stepper-btn-group">
        <button
          id="btn-step-reset"
          className="btn-secondary"
          onClick={() => {
            setIsPlaying(false);
            setCurrentStepIndex(0);
          }}
          title="Reset to step 0"
        >
          ⏮ Reset
        </button>

        <button
          id="btn-step-prev"
          className="btn-secondary"
          onClick={() => setCurrentStepIndex((p) => Math.max(p - 1, 0))}
          disabled={currentStepIndex === 0}
        >
          ◀ Step
        </button>

        <button
          id="btn-step-play"
          className="btn-primary"
          style={{ padding: '0.6rem 1rem' }}
          onClick={() => {
            if (currentStepIndex >= maxStep) setCurrentStepIndex(0);
            setIsPlaying(!isPlaying);
          }}
        >
          {isPlaying ? '⏸ Pause' : '▶ Play'}
        </button>

        <button
          id="btn-step-next"
          className="btn-secondary"
          onClick={() => setCurrentStepIndex((p) => Math.min(p + 1, maxStep))}
          disabled={currentStepIndex >= maxStep}
        >
          Step ▶
        </button>
      </div>

      {/* String Tape Display */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Input Tape:</span>
        <div className="stepper-tape" id="string-tape-display">
          {inputString.split('').map((char, idx) => {
            const isConsumed = idx < currentStepIndex;
            const isCurrent = idx === currentStepIndex - 1;
            return (
              <div
                key={idx}
                className={`tape-char ${isConsumed ? 'consumed' : ''} ${isCurrent ? 'current' : ''}`}
              >
                {char}
              </div>
            );
          })}
          {inputString.length === 0 && <span style={{ color: 'var(--text-muted)' }}>[ε - Empty String]</span>}
        </div>
      </div>

      {/* Current Step Description & Acceptance Verdict */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
          <div>
            Step <span style={{ color: 'var(--accent-cyan)', fontWeight: 'bold' }}>{currentStepIndex}</span> / {maxStep}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
            State: <span style={{ color: '#fff' }}>{currentStep?.current_states?.join(', ') || 'q0'}</span>
          </div>
        </div>

        {/* Finished Verdict Banner */}
        {isFinished && (
          <div
            id="simulation-verdict-badge"
            style={{
              padding: '0.35rem 0.85rem',
              borderRadius: '9999px',
              fontWeight: '700',
              fontSize: '0.8rem',
              letterSpacing: '0.04em',
              background: isAccepted ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.2)',
              color: isAccepted ? '#34d399' : '#fda4af',
              border: `1px solid ${isAccepted ? '#10b981' : '#f43f5e'}`,
              boxShadow: isAccepted ? '0 0 12px rgba(16, 185, 129, 0.4)' : '0 0 12px rgba(244, 63, 94, 0.4)',
            }}
          >
            {isAccepted ? '✓ ACCEPTED' : '✗ REJECTED'}
          </div>
        )}
      </div>
    </div>
  );
}

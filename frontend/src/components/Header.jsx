import React from 'react';

/**
 * Header Component
 * ================
 * Clean, disciplined product header displaying the product name only
 * and an honest engine status readout with a retry action when unreachable.
 */
export default function Header({ backendStatus, onRetryHealth }) {
  const isConnected = backendStatus?.isLive || backendStatus?.status === 'healthy';

  return (
    <header className="app-header" id="app-header" role="banner">
      <div className="brand-wrapper">
        <h1 className="brand-title">AutoMind AI</h1>
      </div>

      <div className="engine-status" id="engine-status-wrapper">
        <span
          className={`status-dot ${isConnected ? 'online' : 'offline'}`}
          aria-hidden="true"
        />
        {isConnected ? (
          <span id="engine-status-text">Engine: connected</span>
        ) : (
          <span id="engine-status-text" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
            <span>Backend not reachable</span>
            {onRetryHealth && (
              <button
                type="button"
                className="btn-retry"
                id="btn-retry-backend"
                onClick={onRetryHealth}
                aria-label="Retry connecting to backend"
              >
                Retry
              </button>
            )}
          </span>
        )}
      </div>
    </header>
  );
}

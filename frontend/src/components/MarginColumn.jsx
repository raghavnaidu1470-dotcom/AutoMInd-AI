import React, { useState } from 'react';
import TraceTable from './TraceTable.jsx';
import XAIExplanationPanel from './XAIExplanationPanel.jsx';

/**
 * MarginColumn Component
 * =====================
 * Technical margin column styled like callouts on an engineering drawing.
 * Appears on the right side only when there is something meaningful to report:
 * either the green-bar execution trace log or the statistical GNN explanation.
 */

export default function MarginColumn({
  simulationResult,
  currentStepIndex,
  onSelectStep,
  xaiExplanation,
  loadingExplanation,
  showEdgeImportance,
  setShowEdgeImportance,
  onClose,
}) {
  const [activeTab, setActiveTab] = useState('trace'); // 'trace' | 'xai'

  return (
    <aside className="margin-column" id="margin-column" role="complementary" aria-label="Inspector & Trace">
      {/* Margin Header */}
      <div className="margin-header">
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <button
            type="button"
            className="btn-quiet"
            style={activeTab === 'trace' ? { background: 'var(--paper-panel)', fontWeight: 'bold' } : {}}
            onClick={() => setActiveTab('trace')}
            aria-pressed={activeTab === 'trace'}
          >
            Trace log
          </button>
          <button
            type="button"
            className="btn-quiet"
            style={activeTab === 'xai' ? { background: 'var(--paper-panel)', fontWeight: 'bold' } : {}}
            onClick={() => setActiveTab('xai')}
            aria-pressed={activeTab === 'xai'}
          >
            Explanation
          </button>
        </div>

        {onClose && (
          <button
            type="button"
            id="btn-close-margin-column"
            className="btn-quiet"
            onClick={onClose}
            title="Collapse margin column"
            aria-label="Collapse margin column"
          >
            ✕
          </button>
        )}
      </div>

      {/* Margin Body */}
      <div className="margin-body">
        {activeTab === 'trace' ? (
          <div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)', marginBottom: '0.4rem' }}>
              Click any row to jump to that step:
            </div>
            <TraceTable
              simulationResult={simulationResult}
              currentStepIndex={currentStepIndex}
              onSelectStep={onSelectStep}
            />
          </div>
        ) : (
          <XAIExplanationPanel
            xaiExplanation={xaiExplanation}
            loading={loadingExplanation}
            showEdgeImportance={showEdgeImportance}
            setShowEdgeImportance={setShowEdgeImportance}
          />
        )}
      </div>
    </aside>
  );
}

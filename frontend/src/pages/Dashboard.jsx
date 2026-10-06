import React, { useState, useEffect, useCallback } from 'react';
import Header from '../components/Header';
import RegexInput from '../components/RegexInput';
import AutomataViewer from '../components/AutomataViewer';
import ExecutionStepper from '../components/ExecutionStepper';
import XAIExplanationPanel from '../components/XAIExplanationPanel';
import { api } from '../services/api';
import {
  MOCK_AUTOMATA_BUNDLE,
  MOCK_SIMULATION_RESULT,
  MOCK_XAI_EXPLANATION,
} from '../mock/mockData';

export default function Dashboard() {
  const [backendStatus, setBackendStatus] = useState(null);
  const [regex, setRegex] = useState('(a|b)*abb');
  const [inputString, setInputString] = useState('ababb');
  const [activeTab, setActiveTab] = useState('minimized_dfa');
  const [automataBundle, setAutomataBundle] = useState(MOCK_AUTOMATA_BUNDLE);
  const [simulationResult, setSimulationResult] = useState(MOCK_SIMULATION_RESULT);
  const [xaiExplanation, setXaiExplanation] = useState(MOCK_XAI_EXPLANATION);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isLiveMode, setIsLiveMode] = useState(false);

  // Core processing pipeline: parse -> simulate -> explain
  const handleProcess = useCallback(
    async (overrideRegex, overrideString, overrideTab) => {
      const targetRegex = overrideRegex !== undefined ? overrideRegex : regex;
      const targetString = overrideString !== undefined ? overrideString : inputString;
      const tabToUse = overrideTab !== undefined ? overrideTab : activeTab;

      setLoading(true);
      setErrorMessage(null);

      try {
        // 1. Parse regex to fetch NFA, DFA, Minimized DFA
        const bundle = await api.parseRegex(targetRegex);
        setAutomataBundle(bundle);

        // Select active automaton to simulate
        const targetAutomaton = bundle[tabToUse] || bundle.minimized_dfa || bundle.dfa || bundle.nfa;

        if (!targetAutomaton) {
          throw new Error('No valid automaton structure returned for current view tab.');
        }

        // 2. Run string simulation
        const sim = await api.runSimulation(targetAutomaton, targetString);
        setSimulationResult(sim);
        setCurrentStepIndex(0);

        // 3. Compute live GNN & SHAP XAI explanations
        const xai = await api.getExplanation(targetAutomaton, sim, targetString);
        setXaiExplanation(xai);

        // Determine if pipeline ran live on backend
        const allLive = Boolean(bundle.isLive && sim.isLive && xai.isLive);
        setIsLiveMode(allLive);
      } catch (err) {
        console.error('Pipeline execution error:', err);
        setErrorMessage(
          `Pipeline error: ${err.message}. Showing safe fallback preview.`
        );
        setIsLiveMode(false);
      } finally {
        setLoading(false);
      }
    },
    [regex, inputString, activeTab]
  );

  // On initial mount: test backend health and run initial live pipeline
  useEffect(() => {
    let isMounted = true;

    async function init() {
      try {
        const health = await api.checkHealth();
        if (isMounted) {
          setBackendStatus(health);
          if (health.isLive) {
            setIsLiveMode(true);
          }
        }
      } catch (e) {
        if (isMounted) {
          setBackendStatus({ status: 'offline', isLive: false });
          setIsLiveMode(false);
        }
      }
      // Trigger initial pipeline to fetch live trained GNN results
      if (isMounted) {
        handleProcess();
      }
    }

    init();
    return () => {
      isMounted = false;
    };
  }, []);

  // When tab changes, re-simulate and re-explain for the active automaton
  const handleTabChange = useCallback(
    (newTab) => {
      setActiveTab(newTab);
      const targetAuto = automataBundle?.[newTab] || automataBundle?.minimized_dfa || automataBundle?.dfa;
      if (targetAuto) {
        // Re-run simulation and explanation for selected diagram
        api.runSimulation(targetAuto, inputString).then((sim) => {
          setSimulationResult(sim);
          setCurrentStepIndex(0);
          api.getExplanation(targetAuto, sim, inputString).then((xai) => {
            setXaiExplanation(xai);
          });
        });
      }
    },
    [automataBundle, inputString]
  );

  // Active automaton depending on tab
  const currentAutomaton =
    automataBundle?.[activeTab] || automataBundle?.minimized_dfa || automataBundle?.dfa || automataBundle?.nfa;

  // Derive currently active state and transition for highlighting in AutomataViewer
  const currentStep = simulationResult?.steps?.[currentStepIndex];
  const activeStateId = currentStep?.current_states?.[0] || currentAutomaton?.start_state;
  const activeTransition = currentStep?.transition_taken;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header backendStatus={backendStatus} />

      <main className="dashboard-container">
        {/* Status / Alert Banner */}
        {errorMessage && (
          <div
            id="status-alert-banner"
            style={{
              padding: '0.75rem 1.25rem',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(244, 63, 94, 0.12)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              color: '#fda4af',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>⚠️ {errorMessage}</span>
            <button
              onClick={() => setErrorMessage(null)}
              style={{
                background: 'none',
                border: 'none',
                color: '#fda4af',
                cursor: 'pointer',
                fontWeight: 'bold',
              }}
            >
              ✕
            </button>
          </div>
        )}

        {/* Live Engine Status Indicator */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.8rem',
            color: 'var(--text-muted)',
            padding: '0 0.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                display: 'inline-block',
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                background: isLiveMode ? '#10b981' : '#f59e0b',
                boxShadow: isLiveMode ? '0 0 6px #10b981' : '0 0 6px #f59e0b',
              }}
            />
            <span>
              {isLiveMode
                ? 'Connected to live FastAPI backend + Trained AutomataGNN'
                : 'Using standalone mock fallback (FastAPI backend unavailable or starting up)'}
            </span>
          </div>
          {loading && (
            <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
              ⚡ Processing pipeline...
            </span>
          )}
        </div>

        {/* Top Control Bar */}
        <RegexInput
          regex={regex}
          setRegex={setRegex}
          inputString={inputString}
          setInputString={setInputString}
          onProcess={() => handleProcess()}
          loading={loading}
        />

        {/* Step-by-Step String Execution Stepper */}
        <ExecutionStepper
          simulationResult={simulationResult}
          inputString={inputString}
          currentStepIndex={currentStepIndex}
          setCurrentStepIndex={setCurrentStepIndex}
        />

        {/* Two-Column Visualization & XAI Grid */}
        <div className="workspace-grid">
          <AutomataViewer
            automaton={currentAutomaton}
            activeTab={activeTab}
            setActiveTab={handleTabChange}
            activeStateId={activeStateId}
            activeTransition={activeTransition}
            xaiExplanation={xaiExplanation}
            showHeatmap={showHeatmap}
            setShowHeatmap={setShowHeatmap}
          />

          <XAIExplanationPanel
            xaiExplanation={xaiExplanation}
            loading={loading}
            isLiveMode={isLiveMode}
          />
        </div>
      </main>
    </div>
  );
}

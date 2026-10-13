import React, { useState, useEffect, useCallback, useRef } from 'react';
import Header from '../components/Header.jsx';
import RegexInput from '../components/RegexInput.jsx';
import StageRail from '../components/StageRail.jsx';
import AutomataViewer from '../components/AutomataViewer.jsx';
import ExecutionStepper from '../components/ExecutionStepper.jsx';
import MarginColumn from '../components/MarginColumn.jsx';
import ReDoSGuardPanel from '../components/ReDoSGuardPanel.jsx';
import { api } from '../services/api.js';
import {
  decodeStateFromQuery,
  syncStateToUrl,
  getRecentRegexes,
  saveRecentRegex,
} from '../utils/urlState.js';
import {
  MOCK_AUTOMATA_BUNDLE,
  MOCK_SIMULATION_RESULT,
  MOCK_XAI_EXPLANATION,
} from '../mock/mockData.js';

export default function Dashboard() {
  // Read initial state from URL query parameters (or sensible defaults)
  const initialUrlState = typeof window !== 'undefined'
    ? decodeStateFromQuery(window.location.search)
    : { regex: '(a|b)*abb', inputString: 'ababb', stage: 'minimized_dfa', step: 0 };

  const [regex, setRegex] = useState(initialUrlState.regex);
  const [inputString, setInputString] = useState(initialUrlState.inputString);
  const [activeStage, setActiveStage] = useState(initialUrlState.stage);
  const [currentStepIndex, setCurrentStepIndex] = useState(initialUrlState.step);

  const [backendStatus, setBackendStatus] = useState(null);
  const [automataBundle, setAutomataBundle] = useState(MOCK_AUTOMATA_BUNDLE);
  const [simulationResult, setSimulationResult] = useState(MOCK_SIMULATION_RESULT);
  const [xaiExplanation, setXaiExplanation] = useState(MOCK_XAI_EXPLANATION);
  const [redosAnalysis, setRedosAnalysis] = useState(null);

  const [loading, setLoading] = useState(false);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [syntaxError, setSyntaxError] = useState(null);
  const [showEdgeImportance, setShowEdgeImportance] = useState(false);
  const [recentRegexes, setRecentRegexes] = useState([]);
  const [marginVisible, setMarginVisible] = useState(true);

  const abortControllerRef = useRef(null);

  // Sync state to URL and recent history
  useEffect(() => {
    syncStateToUrl({
      regex,
      inputString,
      stage: activeStage,
      step: currentStepIndex,
    });
  }, [regex, inputString, activeStage, currentStepIndex]);

  // Load recent history on mount
  useEffect(() => {
    setRecentRegexes(getRecentRegexes());
  }, []);

  // Check backend health
  const checkHealth = useCallback(async () => {
    try {
      const res = await api.checkHealth();
      setBackendStatus(res);
      return res.isLive;
    } catch (err) {
      setBackendStatus({ status: 'offline', isLive: false });
      return false;
    }
  }, []);

  // Main pipeline execution
  const runPipeline = useCallback(
    async (targetRegex = regex, targetString = inputString) => {
      if (!targetRegex || !targetRegex.trim()) {
        setErrorMessage('Regex cannot be empty. Please enter a regular expression pattern.');
        return;
      }

      // Save to recent history
      saveRecentRegex(targetRegex);
      setRecentRegexes(getRecentRegexes());

      // Cancel previous in-flight request if any
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      setLoading(true);
      setErrorMessage(null);
      setSyntaxError(null);

      try {
        // 1. Parse regex to fetch NFA, DFA, and Minimized DFA
        const bundle = await api.parseRegex(targetRegex);
        setAutomataBundle(bundle);

        // Select automaton to simulate based on current stage
        const targetAutoKey =
          activeStage === 'nfa' ? 'nfa' : activeStage === 'dfa' ? 'dfa' : 'minimized_dfa';
        const targetAutomaton = bundle[targetAutoKey] || bundle.minimized_dfa || bundle.dfa || bundle.nfa;

        if (!targetAutomaton) {
          throw new Error('No valid automaton structure returned by the backend.');
        }

        // 2. Run candidate string simulation
        const sim = await api.runSimulation(targetAutomaton, targetString);
        setSimulationResult(sim);
        setCurrentStepIndex(0);

        // 3. ReDoS screening
        api.analyzeReDoS(targetRegex, false)
          .then((rd) => setRedosAnalysis(rd))
          .catch(() => {});

        // 4. Fetch XAI explanation
        setLoadingExplanation(true);
        api.getExplanation(targetAutomaton, sim, targetString)
          .then((xai) => setXaiExplanation(xai))
          .catch((xaiErr) => console.warn('XAI explanation error:', xaiErr))
          .finally(() => setLoadingExplanation(false));
      } catch (err) {
        if (err.name === 'AbortError') return;

        if (err.isSyntaxError) {
          setSyntaxError(err.message);
        } else {
          setErrorMessage(err.message);
        }
      } finally {
        setLoading(false);
      }
    },
    [regex, inputString, activeStage]
  );

  // Initial load
  useEffect(() => {
    checkHealth().then((isLive) => {
      runPipeline();
    });
  }, []);

  // Cancel in-flight operation
  const handleCancelOperation = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setLoading(false);
  };

  // Stage change handler
  const handleSelectStage = (newStage) => {
    setActiveStage(newStage);

    // If switching between NFA, DFA, or Minimized DFA, re-simulate for that automaton
    if (newStage === 'nfa' || newStage === 'dfa' || newStage === 'minimized_dfa') {
      const targetAuto = automataBundle?.[newStage];
      if (targetAuto && inputString) {
        api.runSimulation(targetAuto, inputString)
          .then((sim) => {
            setSimulationResult(sim);
            setCurrentStepIndex(0);
          })
          .catch((err) => console.warn('Simulation error on stage change:', err));
      }
    }
  };

  // Select active automaton depending on stage
  const currentAutomaton =
    activeStage === 'nfa'
      ? automataBundle?.nfa
      : activeStage === 'dfa'
      ? automataBundle?.dfa
      : automataBundle?.minimized_dfa || automataBundle?.dfa || automataBundle?.nfa;

  const currentStep = simulationResult?.steps?.[currentStepIndex];
  const activeStateId = currentStep?.current_states?.[0] || currentAutomaton?.start_state;
  const activeTransition = currentStep?.transition_taken;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Header backendStatus={backendStatus} onRetryHealth={checkHealth} />

      {/* Top Command Bar */}
      <RegexInput
        regex={regex}
        setRegex={setRegex}
        inputString={inputString}
        setInputString={setInputString}
        onRun={(r, s) => runPipeline(r, s)}
        loading={loading}
        syntaxError={syntaxError}
        clearSyntaxError={() => setSyntaxError(null)}
        recentRegexes={recentRegexes}
      />

      {/* Long operation & Cancel bar */}
      {loading && (
        <div
          style={{
            padding: '0.35rem 1.25rem',
            background: 'var(--amber-tint)',
            borderBottom: '1px solid var(--amber-signal)',
            fontSize: 'var(--text-xs)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
          role="status"
        >
          <span>Processing automata construction and string execution...</span>
          <button type="button" className="btn-quiet" onClick={handleCancelOperation}>
            Cancel operation
          </button>
        </div>
      )}

      {/* Backend Error Banner */}
      {errorMessage && (
        <div
          className="syntax-error-banner"
          style={{ margin: '0.5rem 1.25rem', borderRadius: 'var(--radius-control)' }}
          role="alert"
        >
          <div style={{ flex: 1 }}>
            <strong>Backend Error: </strong>
            <span>{errorMessage}</span>
            <div style={{ marginTop: '0.2rem', color: 'var(--ink-slate)' }}>
              <strong>What to try: </strong>
              Verify that the FastAPI backend is running at http://localhost:8000, check network connectivity, or click Retry in the header.
            </div>
          </div>
          <button
            type="button"
            className="btn-quiet"
            onClick={() => setErrorMessage(null)}
            aria-label="Dismiss error"
          >
            ✕
          </button>
        </div>
      )}

      {/* Workspace: Stage Rail (Left), Drawing Area / ReDoS (Center), Margin (Right) */}
      <div className="workspace-layout">
        {/* Stage Rail */}
        <StageRail
          activeStage={activeStage}
          setActiveStage={handleSelectStage}
          nfaStateCount={automataBundle?.nfa?.states?.length}
          dfaStateCount={automataBundle?.dfa?.states?.length}
          minDfaStateCount={automataBundle?.minimized_dfa?.states?.length}
          simulationResult={simulationResult}
          redosRisk={redosAnalysis?.risk_class}
          syntaxError={syntaxError}
        />

        {/* Center Canvas / ReDoS View */}
        {activeStage === 'redos' ? (
          <div style={{ flex: 1, overflowY: 'auto' }}>
            <ReDoSGuardPanel
              initialRegex={regex}
              onLoadIntoStudio={(newRegex) => {
                setRegex(newRegex);
                setActiveStage('minimized_dfa');
                runPipeline(newRegex, inputString);
              }}
            />
          </div>
        ) : (
          <AutomataViewer
            automaton={currentAutomaton}
            activeStage={activeStage}
            activeStateId={activeStateId}
            activeTransition={activeTransition}
            xaiExplanation={xaiExplanation}
            showEdgeImportance={showEdgeImportance}
            setShowEdgeImportance={setShowEdgeImportance}
          />
        )}

        {/* Right Margin Column (Appears conditionally for explanation / trace) */}
        {activeStage !== 'redos' && marginVisible && (
          <MarginColumn
            simulationResult={simulationResult}
            currentStepIndex={currentStepIndex}
            onSelectStep={(idx) => setCurrentStepIndex(idx)}
            xaiExplanation={xaiExplanation}
            loadingExplanation={loadingExplanation}
            showEdgeImportance={showEdgeImportance}
            setShowEdgeImportance={setShowEdgeImportance}
            onClose={() => setMarginVisible(false)}
          />
        )}
      </div>

      {/* Pinned Bottom Tape Transport Bar */}
      {activeStage !== 'redos' && (
        <ExecutionStepper
          simulationResult={simulationResult}
          inputString={inputString}
          currentStepIndex={currentStepIndex}
          setCurrentStepIndex={setCurrentStepIndex}
          isNfa={activeStage === 'nfa'}
        />
      )}
    </div>
  );
}

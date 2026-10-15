import React, { useState, useEffect, useCallback, useRef } from 'react';
import Header from '../components/Header.jsx';
import RegexInput from '../components/RegexInput.jsx';
import RegexExplainer from '../components/RegexExplainer.jsx';
import StageRail from '../components/StageRail.jsx';
import AutomataViewer from '../components/AutomataViewer.jsx';
import ExecutionStepper from '../components/ExecutionStepper.jsx';
import MarginColumn from '../components/MarginColumn.jsx';
import ReDoSGuardPanel from '../components/ReDoSGuardPanel.jsx';
import WalkMeThroughModal from '../components/WalkMeThroughModal.jsx';
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
import { generateAutomataExamples } from '../utils/exampleGenerator.js';

export default function Dashboard() {
  // Read initial state from URL query parameters (or sensible defaults)
  const initialUrlState = typeof window !== 'undefined'
    ? decodeStateFromQuery(window.location.search)
    : { regex: '(a|b)*abb', inputString: 'ababb', stage: 'minimized_dfa', step: 0 };

  const [regex, setRegex] = useState(initialUrlState.regex);
  const [inputString, setInputString] = useState(initialUrlState.inputString);
  const [activeStage, setActiveStage] = useState(initialUrlState.stage || 'minimized_dfa');
  const [currentStepIndex, setCurrentStepIndex] = useState(initialUrlState.step || 0);

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
  const [railVisible, setRailVisible] = useState(true);
  const [isAdvancedMode, setIsAdvancedMode] = useState(false);
  const [walkthroughOpen, setWalkthroughOpen] = useState(false);

  const [generatedExamples, setGeneratedExamples] = useState(() => {
    try {
      return generateAutomataExamples(
        MOCK_AUTOMATA_BUNDLE.minimized_dfa || MOCK_AUTOMATA_BUNDLE.dfa,
        initialUrlState.regex || '(a|b)*abb'
      );
    } catch {
      return null;
    }
  });

  const abortControllerRef = useRef(null);
  const pipelineSeqRef = useRef(0);

  // Keyboard shortcut to toggle right sidebar (Alt+S)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.altKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) return;
        e.preventDefault();
        setMarginVisible((v) => !v);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

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
    } catch {
      setBackendStatus({ status: 'offline', isLive: false });
      return false;
    }
  }, []);

  // Current active automaton model
  const currentAutomaton =
    activeStage === 'nfa'
      ? automataBundle?.nfa
      : activeStage === 'dfa'
      ? automataBundle?.dfa
      : automataBundle?.minimized_dfa || automataBundle?.dfa || automataBundle?.nfa;

  // Strict Synchronization: Re-simulate whenever currentAutomaton or inputString changes
  useEffect(() => {
    if (
      currentAutomaton &&
      inputString !== undefined &&
      inputString !== null &&
      activeStage !== 'redos'
    ) {
      if (simulationResult?.automaton_id !== currentAutomaton.id || simulationResult?.input_string !== inputString) {
        api.runSimulation(currentAutomaton, inputString)
          .then((sim) => {
            setSimulationResult(sim);
            setCurrentStepIndex(0);
            api.getExplanation(currentAutomaton, sim, inputString)
              .then((xai) => setXaiExplanation(xai))
              .catch(() => {});
          })
          .catch((err) => {
            if (err.name !== 'AbortError') {
              console.warn('Sync simulation update error:', err);
            }
          });
      }
    }
  }, [currentAutomaton?.id, inputString, activeStage]);

  // Main pipeline execution
  const runPipeline = useCallback(
    async (targetRegex = regex, targetString = inputString) => {
      if (!targetRegex || !targetRegex.trim()) {
        setErrorMessage('Regex cannot be empty. Please enter a regular expression pattern.');
        return;
      }

      saveRecentRegex(targetRegex);
      setRecentRegexes(getRecentRegexes());

      const currentSeq = ++pipelineSeqRef.current;

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();
      const signal = abortControllerRef.current.signal;

      setLoading(true);
      setErrorMessage(null);
      setSyntaxError(null);

      try {
        // 1. Parse regex to fetch NFA, DFA, and Minimized DFA
        const bundle = await api.parseRegex(targetRegex, { signal });
        if (currentSeq !== pipelineSeqRef.current) return;
        setAutomataBundle(bundle);

        // Generate verified candidate test inputs
        try {
          const gen = generateAutomataExamples(
            bundle.minimized_dfa || bundle.dfa || bundle.nfa,
            targetRegex
          );
          if (currentSeq === pipelineSeqRef.current) {
            setGeneratedExamples(gen);
          }
        } catch (genErr) {
          console.warn('Failed to generate automata examples:', genErr);
        }

        // Select automaton to simulate based on current stage
        const targetAutoKey =
          activeStage === 'nfa' ? 'nfa' : activeStage === 'dfa' ? 'dfa' : 'minimized_dfa';
        const targetAutomaton = bundle[targetAutoKey] || bundle.minimized_dfa || bundle.dfa || bundle.nfa;

        if (!targetAutomaton) {
          throw new Error('No valid automaton structure returned by the backend.');
        }

        // 2. Run candidate string simulation
        const sim = await api.runSimulation(targetAutomaton, targetString, { signal });
        if (currentSeq !== pipelineSeqRef.current) return;
        setSimulationResult(sim);
        setCurrentStepIndex(0);

        // 3. ReDoS screening
        api.analyzeReDoS(targetRegex, false, { signal })
          .then((rd) => {
            if (currentSeq === pipelineSeqRef.current) setRedosAnalysis(rd);
          })
          .catch(() => {});

        // 4. Fetch XAI explanation
        setLoadingExplanation(true);
        api.getExplanation(targetAutomaton, sim, targetString, { signal })
          .then((xai) => {
            if (currentSeq === pipelineSeqRef.current) setXaiExplanation(xai);
          })
          .catch((xaiErr) => {
            if (xaiErr.name !== 'AbortError') console.warn('XAI explanation error:', xaiErr);
          })
          .finally(() => {
            if (currentSeq === pipelineSeqRef.current) setLoadingExplanation(false);
          });
      } catch (err) {
        if (err.name === 'AbortError' || currentSeq !== pipelineSeqRef.current) return;

        if (err.isSyntaxError) {
          setSyntaxError(err.message);
          setGeneratedExamples(null);
        } else {
          setErrorMessage(err.message);
        }
      } finally {
        if (currentSeq === pipelineSeqRef.current) {
          setLoading(false);
        }
      }
    },
    [regex, inputString, activeStage]
  );

  // Initial load
  useEffect(() => {
    checkHealth().then(() => {
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

    if (newStage === 'nfa' || newStage === 'dfa' || newStage === 'minimized_dfa') {
      const targetAuto = automataBundle?.[newStage];
      if (targetAuto && inputString !== undefined && inputString !== null) {
        api.runSimulation(targetAuto, inputString)
          .then((sim) => {
            setSimulationResult(sim);
            setCurrentStepIndex(0);
            api.getExplanation(targetAuto, sim, inputString)
              .then((xai) => setXaiExplanation(xai))
              .catch(() => {});
          })
          .catch((err) => console.warn('Simulation error on stage change:', err));
      }
    }
  };

  // Active step and active state set calculations
  const currentStep = simulationResult?.steps?.[currentStepIndex];
  const activeStates = currentStep?.current_states || (currentAutomaton?.start_state ? [currentAutomaton.start_state] : []);
  const activeStateId = activeStates[0] || currentAutomaton?.start_state;
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
        generatedExamples={generatedExamples}
        onSelectGeneratedExample={(str) => {
          setInputString(str);
          runPipeline(regex, str);
        }}
        isExamplesStale={loading || (generatedExamples && generatedExamples.sourceRegex !== regex)}
        onGenerateMore={() => {
          if (currentAutomaton) {
            const more = generateAutomataExamples(currentAutomaton, regex, 15);
            setGeneratedExamples(more);
          }
        }}
      />

      {/* Interactive Plain-English & Token Explainer (Requirement 2) */}
      {!syntaxError && activeStage !== 'redos' && (
        <RegexExplainer regex={regex} />
      )}

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
        {/* Persistent Reopen Navigation Rail Button */}
        {!railVisible && (
          <button
            type="button"
            id="btn-persistent-open-rail"
            className="persistent-open-rail-btn"
            onClick={() => setRailVisible(true)}
            aria-label="Open learning flow navigation"
            title="Open learning flow navigation sidebar"
          >
            ▶ Navigation
          </button>
        )}

        {/* Stage Rail Navigation */}
        {railVisible && (
          <StageRail
            activeStage={activeStage}
            setActiveStage={handleSelectStage}
            nfaStateCount={automataBundle?.nfa?.states?.length}
            dfaStateCount={automataBundle?.dfa?.states?.length}
            minDfaStateCount={automataBundle?.minimized_dfa?.states?.length}
            simulationResult={simulationResult}
            redosRisk={redosAnalysis?.risk_class}
            syntaxError={syntaxError}
            isAdvancedMode={isAdvancedMode}
            setIsAdvancedMode={setIsAdvancedMode}
            onOpenWalkthrough={() => setWalkthroughOpen(true)}
            onCloseRail={() => setRailVisible(false)}
          />
        )}

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
            setActiveStage={handleSelectStage}
            automataBundle={automataBundle}
            activeStateId={activeStateId}
            activeStates={activeStates}
            activeTransition={activeTransition}
            xaiExplanation={xaiExplanation}
            showEdgeImportance={showEdgeImportance}
            setShowEdgeImportance={setShowEdgeImportance}
            sidebarVisible={marginVisible}
            onToggleSidebar={() => setMarginVisible((prev) => !prev)}
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
            isAdvancedMode={isAdvancedMode}
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
          automatonType={currentAutomaton?.type || 'DFA'}
        />
      )}

      {/* Beginner Walkthrough Modal */}
      <WalkMeThroughModal
        isOpen={walkthroughOpen}
        onClose={() => setWalkthroughOpen(false)}
      />
    </div>
  );
}

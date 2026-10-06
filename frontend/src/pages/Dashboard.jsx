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

  // Check backend health on initial mount
  useEffect(() => {
    async function initCheck() {
      const status = await api.checkHealth();
      setBackendStatus(status);
    }
    initCheck();
  }, []);

  // Handle pipeline generation
  const handleProcess = useCallback(async () => {
    setLoading(true);
    try {
      // 1. Parse regex to fetch NFA, DFA, Minimized DFA
      const bundle = await api.parseRegex(regex);
      setAutomataBundle(bundle);

      // Select active automaton to simulate
      const targetAutomaton = bundle[activeTab] || bundle.minimized_dfa || bundle.dfa;

      // 2. Run string simulation
      const sim = await api.runSimulation(targetAutomaton, inputString);
      setSimulationResult(sim);
      setCurrentStepIndex(0);

      // 3. Compute XAI explanations
      const xai = await api.getExplanation(targetAutomaton, sim, inputString);
      setXaiExplanation(xai);
    } catch (err) {
      console.error('Processing error:', err);
    } finally {
      setLoading(false);
    }
  }, [regex, inputString, activeTab]);

  // Active automaton depending on tab
  const currentAutomaton =
    automataBundle?.[activeTab] || automataBundle?.minimized_dfa || automataBundle?.dfa;

  // Derive currently active state and transition for highlighting in AutomataViewer
  const currentStep = simulationResult?.steps?.[currentStepIndex];
  const activeStateId = currentStep?.current_states?.[0] || currentAutomaton?.start_state;
  const activeTransition = currentStep?.transition_taken;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header backendStatus={backendStatus} />

      <main className="dashboard-container">
        {/* Top Control Bar */}
        <RegexInput
          regex={regex}
          setRegex={setRegex}
          inputString={inputString}
          setInputString={setInputString}
          onProcess={handleProcess}
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
            setActiveTab={setActiveTab}
            activeStateId={activeStateId}
            activeTransition={activeTransition}
            xaiExplanation={xaiExplanation}
            showHeatmap={showHeatmap}
            setShowHeatmap={setShowHeatmap}
          />

          <XAIExplanationPanel
            xaiExplanation={xaiExplanation}
            loading={loading}
          />
        </div>
      </main>
    </div>
  );
}

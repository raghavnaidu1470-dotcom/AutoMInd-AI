/**
 * Frontend API Service
 * ====================
 * Handles HTTP communication with the FastAPI backend orchestrator,
 * with graceful fallback to built-in mock fixtures if the backend is unreachable.
 */

import {
  MOCK_AUTOMATA_BUNDLE,
  MOCK_SIMULATION_RESULT,
  MOCK_XAI_EXPLANATION,
} from '../mock/mockData';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const api = {
  /**
   * Health check endpoint to verify backend connectivity
   */
  async checkHealth() {
    try {
      const res = await fetch(`${BASE_URL}/health`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return { ...data, isLive: true };
    } catch (err) {
      return {
        status: 'offline',
        service: 'AutoMind Standalone (Mock Mode)',
        isLive: false,
        error: err.message,
      };
    }
  },

  /**
   * Submits regular expression to retrieve NFA, DFA, and Minimized DFA
   */
  async parseRegex(regex) {
    try {
      const res = await fetch(`${BASE_URL}/automata/parse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ regex }),
      });
      if (!res.ok) {
        const errorDetail = await res.text().catch(() => '');
        throw new Error(`Server returned ${res.status}: ${errorDetail}`);
      }
      const data = await res.json();
      return { ...data, isLive: true };
    } catch (err) {
      console.warn('Backend /api/automata/parse unavailable, using mock automata fallback:', err.message);
      return {
        ...MOCK_AUTOMATA_BUNDLE,
        regex,
        isLive: false,
        fallbackReason: err.message,
      };
    }
  },

  /**
   * Runs candidate string simulation on the selected automaton
   */
  async runSimulation(automaton, inputString) {
    try {
      const res = await fetch(`${BASE_URL}/simulation/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          automaton,
          input_string: inputString,
        }),
      });
      if (!res.ok) {
        const errorDetail = await res.text().catch(() => '');
        throw new Error(`Server returned ${res.status}: ${errorDetail}`);
      }
      const data = await res.json();
      return { ...data, isLive: true };
    } catch (err) {
      console.warn('Backend /api/simulation/run unavailable, using mock simulation fallback:', err.message);
      return {
        ...MOCK_SIMULATION_RESULT,
        input_string: inputString,
        isLive: false,
        fallbackReason: err.message,
      };
    }
  },

  /**
   * Requests real GNN prediction, GNNExplainer critical subgraphs, and SHAP attributions
   */
  async getExplanation(automaton, simulationTrace, inputString) {
    try {
      const res = await fetch(`${BASE_URL}/xai/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          automaton,
          simulation_trace: simulationTrace,
          input_string: inputString,
        }),
      });
      if (!res.ok) {
        const errorDetail = await res.text().catch(() => '');
        throw new Error(`Server returned ${res.status}: ${errorDetail}`);
      }
      const data = await res.json();
      return { ...data, isLive: true };
    } catch (err) {
      console.warn('Backend /api/xai/explain unavailable, using mock explanation fallback:', err.message);
      return {
        ...MOCK_XAI_EXPLANATION,
        input_string: inputString,
        isLive: false,
        fallbackReason: err.message,
      };
    }
  },
};

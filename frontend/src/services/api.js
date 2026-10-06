/**
 * Frontend API Service
 * Handles HTTP communication with the FastAPI backend orchestrator,
 * with graceful fallback to built-in mock data for standalone preview.
 */

import {
  MOCK_AUTOMATA_BUNDLE,
  MOCK_SIMULATION_RESULT,
  MOCK_XAI_EXPLANATION,
} from '../mock/mockData';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const api = {
  /**
   * Health check endpoint
   */
  async checkHealth() {
    try {
      const res = await fetch(`${BASE_URL}/health`);
      if (!res.ok) throw new Error('API offline');
      return await res.json();
    } catch {
      return { status: 'mock_mode', service: 'Standalone Frontend' };
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
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('Backend unavailable, using mock automata bundle:', err);
      return { ...MOCK_AUTOMATA_BUNDLE, regex };
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
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('Backend unavailable, using mock simulation result:', err);
      return {
        ...MOCK_SIMULATION_RESULT,
        input_string: inputString,
      };
    }
  },

  /**
   * Requests GNN prediction, GNNExplainer critical subgraphs, and SHAP attributions
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
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('Backend unavailable, using mock XAI explanation:', err);
      return {
        ...MOCK_XAI_EXPLANATION,
        input_string: inputString,
      };
    }
  },
};

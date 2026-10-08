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
    let res;
    try {
      res = await fetch(`${BASE_URL}/automata/parse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ regex }),
      });
    } catch (networkErr) {
      console.warn('Backend /api/automata/parse unreachable, using mock automata fallback:', networkErr.message);
      return {
        ...MOCK_AUTOMATA_BUNDLE,
        regex,
        isLive: false,
        fallbackReason: networkErr.message,
      };
    }

    if (!res.ok) {
      let detailMsg = `Server returned ${res.status}`;
      try {
        const errJson = await res.json();
        detailMsg = errJson.detail || detailMsg;
      } catch (e) {
        const text = await res.text().catch(() => '');
        if (text) detailMsg = text;
      }

      const error = new Error(detailMsg);
      error.status = res.status;
      error.isSyntaxError = (res.status === 400 || res.status === 422);
      throw error;
    }

    const data = await res.json();
    return { ...data, isLive: true };
  },

  /**
   * Runs candidate string simulation on the selected automaton
   */
  async runSimulation(automaton, inputString) {
    let res;
    try {
      res = await fetch(`${BASE_URL}/simulation/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          automaton,
          input_string: inputString,
        }),
      });
    } catch (networkErr) {
      console.warn('Backend /api/simulation/run unreachable, using mock simulation fallback:', networkErr.message);
      return {
        ...MOCK_SIMULATION_RESULT,
        input_string: inputString,
        isLive: false,
        fallbackReason: networkErr.message,
      };
    }

    if (!res.ok) {
      let detailMsg = `Server returned ${res.status}`;
      try {
        const errJson = await res.json();
        detailMsg = errJson.detail || detailMsg;
      } catch (e) {
        const text = await res.text().catch(() => '');
        if (text) detailMsg = text;
      }
      const error = new Error(detailMsg);
      error.status = res.status;
      throw error;
    }

    const data = await res.json();
    return { ...data, isLive: true };
  },

  /**
   * Requests real GNN prediction, GNNExplainer critical subgraphs, and SHAP attributions
   */
  async getExplanation(automaton, simulationTrace, inputString) {
    let res;
    try {
      res = await fetch(`${BASE_URL}/xai/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          automaton,
          simulation_trace: simulationTrace,
          input_string: inputString,
        }),
      });
    } catch (networkErr) {
      console.warn('Backend /api/xai/explain unreachable, using mock explanation fallback:', networkErr.message);
      return {
        ...MOCK_XAI_EXPLANATION,
        input_string: inputString,
        isLive: false,
        fallbackReason: networkErr.message,
      };
    }

    if (!res.ok) {
      let detailMsg = `Server returned ${res.status}`;
      try {
        const errJson = await res.json();
        detailMsg = errJson.detail || detailMsg;
      } catch (e) {
        const text = await res.text().catch(() => '');
        if (text) detailMsg = text;
      }
      const error = new Error(detailMsg);
      error.status = res.status;
      throw error;
    }

    const data = await res.json();
    return { ...data, isLive: true };
  },
};

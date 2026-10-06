/**
 * Standalone mock dataset for frontend development and offline preview.
 */

export const MOCK_AUTOMATA_BUNDLE = {
  regex: '(a|b)*abb',
  nfa: {
    id: 'nfa_ends_with_abb',
    name: 'NFA for (a|b)*abb',
    type: 'NFA',
    alphabet: ['a', 'b'],
    start_state: 's0',
    states: [
      { id: 's0', label: 's0', is_start: true, is_accepting: false },
      { id: 's1', label: 's1', is_start: false, is_accepting: false },
      { id: 's2', label: 's2', is_start: false, is_accepting: false },
      { id: 's3', label: 's3', is_start: false, is_accepting: true },
    ],
    transitions: [
      { id: 'nt1', from_state: 's0', to_state: 's0', symbol: 'a' },
      { id: 'nt2', from_state: 's0', to_state: 's0', symbol: 'b' },
      { id: 'nt3', from_state: 's0', to_state: 's1', symbol: 'a' },
      { id: 'nt4', from_state: 's1', to_state: 's2', symbol: 'b' },
      { id: 'nt5', from_state: 's2', to_state: 's3', symbol: 'b' },
    ],
    metadata: { regex: '(a|b)*abb', state_count: 4, transition_count: 5 },
  },
  dfa: {
    id: 'dfa_ends_with_abb',
    name: 'DFA for (a|b)*abb',
    type: 'DFA',
    alphabet: ['a', 'b'],
    start_state: 'q0',
    states: [
      { id: 'q0', label: 'q0 (Start)', is_start: true, is_accepting: false },
      { id: 'q1', label: 'q1 (Saw a)', is_start: false, is_accepting: false },
      { id: 'q2', label: 'q2 (Saw ab)', is_start: false, is_accepting: false },
      { id: 'q3', label: 'q3 (Saw abb)', is_start: false, is_accepting: true },
    ],
    transitions: [
      { id: 'dt1', from_state: 'q0', to_state: 'q1', symbol: 'a' },
      { id: 'dt2', from_state: 'q0', to_state: 'q0', symbol: 'b' },
      { id: 'dt3', from_state: 'q1', to_state: 'q1', symbol: 'a' },
      { id: 'dt4', from_state: 'q1', to_state: 'q2', symbol: 'b' },
      { id: 'dt5', from_state: 'q2', to_state: 'q1', symbol: 'a' },
      { id: 'dt6', from_state: 'q2', to_state: 'q3', symbol: 'b' },
      { id: 'dt7', from_state: 'q3', to_state: 'q1', symbol: 'a' },
      { id: 'dt8', from_state: 'q3', to_state: 'q0', symbol: 'b' },
    ],
    metadata: { regex: '(a|b)*abb', state_count: 4, transition_count: 8, is_minimized: true },
  },
  minimized_dfa: {
    id: 'min_dfa_ends_with_abb',
    name: 'Minimized DFA for (a|b)*abb',
    type: 'MINIMIZED_DFA',
    alphabet: ['a', 'b'],
    start_state: 'q0',
    states: [
      { id: 'q0', label: 'q0', is_start: true, is_accepting: false },
      { id: 'q1', label: 'q1', is_start: false, is_accepting: false },
      { id: 'q2', label: 'q2', is_start: false, is_accepting: false },
      { id: 'q3', label: 'q3', is_start: false, is_accepting: true },
    ],
    transitions: [
      { id: 'dt1', from_state: 'q0', to_state: 'q1', symbol: 'a' },
      { id: 'dt2', from_state: 'q0', to_state: 'q0', symbol: 'b' },
      { id: 'dt3', from_state: 'q1', to_state: 'q1', symbol: 'a' },
      { id: 'dt4', from_state: 'q1', to_state: 'q2', symbol: 'b' },
      { id: 'dt5', from_state: 'q2', to_state: 'q1', symbol: 'a' },
      { id: 'dt6', from_state: 'q2', to_state: 'q3', symbol: 'b' },
      { id: 'dt7', from_state: 'q3', to_state: 'q1', symbol: 'a' },
      { id: 'dt8', from_state: 'q3', to_state: 'q0', symbol: 'b' },
    ],
    metadata: { regex: '(a|b)*abb', state_count: 4, transition_count: 8, is_minimized: true },
  },
};

export const MOCK_SIMULATION_RESULT = {
  automaton_id: 'dfa_ends_with_abb',
  input_string: 'ababb',
  accepted: true,
  final_states: ['q3'],
  execution_time_ms: 1.25,
  steps: [
    {
      step: 0,
      current_states: ['q0'],
      symbol_read: null,
      transition_taken: null,
      next_states: ['q0'],
    },
    {
      step: 1,
      current_states: ['q0'],
      symbol_read: 'a',
      transition_taken: { from_state: 'q0', to_state: 'q1', symbol: 'a' },
      next_states: ['q1'],
    },
    {
      step: 2,
      current_states: ['q1'],
      symbol_read: 'b',
      transition_taken: { from_state: 'q1', to_state: 'q2', symbol: 'b' },
      next_states: ['q2'],
    },
    {
      step: 3,
      current_states: ['q2'],
      symbol_read: 'a',
      transition_taken: { from_state: 'q2', to_state: 'q1', symbol: 'a' },
      next_states: ['q1'],
    },
    {
      step: 4,
      current_states: ['q1'],
      symbol_read: 'b',
      transition_taken: { from_state: 'q1', to_state: 'q2', symbol: 'b' },
      next_states: ['q2'],
    },
    {
      step: 5,
      current_states: ['q2'],
      symbol_read: 'b',
      transition_taken: { from_state: 'q2', to_state: 'q3', symbol: 'b' },
      next_states: ['q3'],
    },
  ],
};

export const MOCK_XAI_EXPLANATION = {
  automaton_id: 'dfa_ends_with_abb',
  input_string: 'ababb',
  predicted_accepted: true,
  confidence: 0.985,
  node_importance: {
    q0: 0.32,
    q1: 0.68,
    q2: 0.89,
    q3: 0.98,
  },
  edge_importance: [
    { from_state: 'q2', to_state: 'q3', symbol: 'b', importance: 0.97 },
    { from_state: 'q1', to_state: 'q2', symbol: 'b', importance: 0.86 },
    { from_state: 'q2', to_state: 'q1', symbol: 'a', importance: 0.44 },
    { from_state: 'q0', to_state: 'q1', symbol: 'a', importance: 0.36 },
    { from_state: 'q0', to_state: 'q0', symbol: 'b', importance: 0.12 },
    { from_state: 'q1', to_state: 'q1', symbol: 'a', importance: 0.08 },
    { from_state: 'q3', to_state: 'q1', symbol: 'a', importance: 0.05 },
    { from_state: 'q3', to_state: 'q0', symbol: 'b', importance: 0.05 },
  ],
  critical_subgraph: {
    nodes: ['q1', 'q2', 'q3'],
    edges: [
      { from_state: 'q1', to_state: 'q2', symbol: 'b' },
      { from_state: 'q2', to_state: 'q3', symbol: 'b' },
    ],
  },
  feature_attributions: {
    is_accepting: 0.45,
    final_state_match: 0.26,
    visit_frequency: 0.15,
    in_degree: 0.09,
    is_start: 0.05,
  },
  explanation_summary:
    "Critical suffix traversal q1 --b--> q2 and q2 --b--> q3 reached the accepting state q3, serving as the dominant factor (importance: 0.97) for string acceptance.",
};

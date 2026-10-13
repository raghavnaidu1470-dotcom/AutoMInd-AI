import test from 'node:test';
import assert from 'node:assert/strict';

import { mergeParallelEdges } from '../src/utils/edgeMerging.js';
import { encodeStateToQuery, decodeStateFromQuery } from '../src/utils/urlState.js';
import { buildAutomatonLayout, LARGE_INPUT_THRESHOLD } from '../src/utils/dagreLayout.js';
import { parseSyntaxError } from '../src/utils/syntaxValidator.js';

test('mergeParallelEdges: combines multiple transitions between same states into single sorted label', () => {
  const rawTransitions = [
    { from_state: 'q0', to_state: 'q1', symbol: 'b' },
    { from_state: 'q0', to_state: 'q1', symbol: 'a' },
    { from_state: 'q1', to_state: 'q1', symbol: 'a' },
    { from_state: 'q1', to_state: 'q2', symbol: 'ε' },
    { from_state: 'q1', to_state: 'q2', symbol: 'c' },
  ];

  const merged = mergeParallelEdges(rawTransitions);
  assert.equal(merged.length, 3, 'Should produce 3 distinct edges');

  const q0_q1 = merged.find((e) => e.from_state === 'q0' && e.to_state === 'q1');
  assert.ok(q0_q1);
  assert.equal(q0_q1.label, 'a, b', 'Symbols should be sorted alphabetically');
  assert.equal(q0_q1.isSelfLoop, false);

  const q1_q1 = merged.find((e) => e.from_state === 'q1' && e.to_state === 'q1');
  assert.ok(q1_q1);
  assert.equal(q1_q1.isSelfLoop, true);
  assert.equal(q1_q1.label, 'a');

  const q1_q2 = merged.find((e) => e.from_state === 'q1' && e.to_state === 'q2');
  assert.ok(q1_q2);
  assert.equal(q1_q2.label, 'c, ε', 'Epsilon should be placed last');
});

test('mergeParallelEdges: handles empty or invalid input gracefully', () => {
  assert.deepEqual(mergeParallelEdges([]), []);
  assert.deepEqual(mergeParallelEdges(null), []);
  assert.deepEqual(mergeParallelEdges([null, undefined]), []);
});

test('urlState: correctly encodes and decodes application state', () => {
  const initial = {
    regex: '(a|b)*abb',
    inputString: 'ababb',
    stage: 'dfa',
    step: 3,
  };

  const query = encodeStateToQuery(initial);
  assert.ok(query.includes('string=ababb'));
  assert.ok(query.includes('stage=dfa'));
  assert.ok(query.includes('step=3'));

  const parsed = decodeStateFromQuery(query);
  assert.equal(parsed.regex, '(a|b)*abb');
  assert.equal(parsed.inputString, 'ababb');
  assert.equal(parsed.stage, 'dfa');
  assert.equal(parsed.step, 3);
});

test('urlState: falls back to sensible defaults on empty query string', () => {
  const parsed = decodeStateFromQuery('');
  assert.equal(parsed.regex, '(a|b)*abb');
  assert.equal(parsed.inputString, 'ababb');
  assert.equal(parsed.stage, 'minimized_dfa');
  assert.equal(parsed.step, 0);
});

test('buildAutomatonLayout: generates valid coordinates and paths via Dagre', () => {
  const sampleAutomaton = {
    states: [
      { id: 'q0', is_start: true, is_accepting: false },
      { id: 'q1', is_start: false, is_accepting: false },
      { id: 'q2', is_start: false, is_accepting: true },
    ],
    transitions: [
      { from_state: 'q0', to_state: 'q1', symbol: 'a' },
      { from_state: 'q1', to_state: 'q2', symbol: 'b' },
      { from_state: 'q2', to_state: 'q2', symbol: 'b' },
    ],
  };

  const layout = buildAutomatonLayout(sampleAutomaton);
  assert.ok(layout.coords['q0'], 'Should compute coords for q0');
  assert.ok(layout.coords['q1'], 'Should compute coords for q1');
  assert.ok(layout.coords['q2'], 'Should compute coords for q2');
  assert.ok(layout.coords['q0'].x < layout.coords['q1'].x, 'Left-to-right ordering');
  assert.ok(layout.coords['q1'].x < layout.coords['q2'].x, 'Left-to-right ordering');
  assert.equal(layout.isLarge, false);
});

test('buildAutomatonLayout: flags large graphs (>= 60 states) and simplifies layout without freezing', () => {
  const largeStates = [];
  for (let i = 0; i < LARGE_INPUT_THRESHOLD + 5; i++) {
    largeStates.push({ id: `q${i}`, is_start: i === 0, is_accepting: i === LARGE_INPUT_THRESHOLD + 4 });
  }

  const largeAutomaton = {
    states: largeStates,
    transitions: [
      { from_state: 'q0', to_state: 'q1', symbol: 'a' },
    ],
  };

  const layout = buildAutomatonLayout(largeAutomaton);
  assert.equal(layout.isLarge, true);
  assert.equal(layout.stateCount, LARGE_INPUT_THRESHOLD + 5);
  assert.ok(layout.coords['q0']);
  assert.ok(layout.coords[`q${LARGE_INPUT_THRESHOLD + 4}`]);
});

test('parseSyntaxError: extracts position and actionable tip from backend error detail', () => {
  const errText = "Regex syntax error: Unexpected closing parenthesis ')' at position 4";
  const parsed = parseSyntaxError(errText, "ab)c");

  assert.equal(parsed.position, 4);
  assert.equal(parsed.message, "Unexpected closing parenthesis ')'");
  assert.ok(parsed.tip.includes("Remove this closing parenthesis"));

  const unclosedErr = "Regex syntax error: Unbalanced parenthesis: missing ')' at position 1";
  const parsed2 = parseSyntaxError(unclosedErr, "(abc");
  assert.equal(parsed2.position, 1);
  assert.ok(parsed2.tip.includes("Add a closing parenthesis"));
});

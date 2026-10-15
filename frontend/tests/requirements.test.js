import test from 'node:test';
import assert from 'node:assert/strict';

import { buildStandaloneSvgString, EXPORT_COLORS } from '../src/utils/diagramExport.js';
import { REDOS_EXAMPLES, runBoundedClientMatch } from '../src/utils/redosExamples.js';
import { generateAutomataExamples, verifyAutomatonMatch } from '../src/utils/exampleGenerator.js';
import {
  tokenizeRegex,
  explainRegexPlainEnglish,
  checkUnsupportedConstructs,
} from '../src/utils/regexExplainer.js';
import { computeMinimizationDiff } from '../src/utils/minimizationDiff.js';

// Sample DFA for testing: (a|b)*abb
const sampleDfa = {
  id: 'dfa_sample',
  name: 'Sample DFA (a|b)*abb',
  type: 'DFA',
  alphabet: ['a', 'b'],
  start_state: 'q0',
  states: [
    { id: 'q0', label: 'q0', is_start: true, is_accepting: false, metadata: { nfa_subset: ['s0'] } },
    { id: 'q1', label: 'q1', is_start: false, is_accepting: false, metadata: { nfa_subset: ['s0', 's1'] } },
    { id: 'q2', label: 'q2', is_start: false, is_accepting: false, metadata: { nfa_subset: ['s0', 's2'] } },
    { id: 'q3', label: 'q3', is_start: false, is_accepting: true, metadata: { nfa_subset: ['s0', 's3'] } },
  ],
  transitions: [
    { from_state: 'q0', to_state: 'q1', symbol: 'a' },
    { from_state: 'q0', to_state: 'q0', symbol: 'b' },
    { from_state: 'q1', to_state: 'q1', symbol: 'a' },
    { from_state: 'q1', to_state: 'q2', symbol: 'b' },
    { from_state: 'q2', to_state: 'q1', symbol: 'a' },
    { from_state: 'q2', to_state: 'q3', symbol: 'b' },
    { from_state: 'q3', to_state: 'q1', symbol: 'a' },
    { from_state: 'q3', to_state: 'q0', symbol: 'b' },
  ],
};

// Sample Minimized DFA
const sampleMinDfa = {
  id: 'min_dfa_sample',
  name: 'Minimized DFA (a|b)*abb',
  type: 'MINIMIZED_DFA',
  alphabet: ['a', 'b'],
  start_state: 'q0',
  states: [
    { id: 'q0', label: 'q0', is_start: true, is_accepting: false, metadata: { merged_states: ['q0'] } },
    { id: 'q1', label: 'q1', is_start: false, is_accepting: false, metadata: { merged_states: ['q1'] } },
    { id: 'q2', label: 'q2', is_start: false, is_accepting: false, metadata: { merged_states: ['q2'] } },
    { id: 'q3', label: 'q3', is_start: false, is_accepting: true, metadata: { merged_states: ['q3'] } },
  ],
  transitions: sampleDfa.transitions,
};

test('Requirement 1: buildStandaloneSvgString produces self-contained, high-quality SVG', () => {
  const mockSvg = {
    cloneNode: () => ({
      removeAttribute: () => {},
      setAttribute: () => {},
      outerHTML: '<svg xmlns="http://www.w3.org/2000/svg"><defs></defs><g><path class="svg-edge-path" stroke="var(--ink-slate)" d="M 0 0" /></g></svg>',
    }),
  };

  const layout = { width: 800, height: 450 };
  const svgOutput = buildStandaloneSvgString(mockSvg, layout, sampleDfa);

  assert.ok(svgOutput.includes('<style type="text/css">'), 'Should embed standalone stylesheet');
  assert.ok(svgOutput.includes('fill="#f8f9fa"'), 'Should contain solid paper background');
  assert.ok(svgOutput.includes('JetBrains Mono'), 'Should declare explicit high-legibility fonts');
  assert.ok(svgOutput.includes('viewBox='), 'Should specify explicit viewBox');
  assert.ok(!svgOutput.includes('var(--ink-slate)'), 'Should replace CSS variable references with concrete hex');
});

test('Requirement 2: REDOS_EXAMPLES covers diverse archetypes with required attributes', () => {
  assert.ok(REDOS_EXAMPLES.length >= 8, 'Should provide at least 8 rich ReDoS examples');

  const categories = new Set(REDOS_EXAMPLES.map((e) => e.category));
  assert.ok(categories.size >= 3, 'Should cover exponential, polynomial, and linear categories');

  REDOS_EXAMPLES.forEach((ex) => {
    assert.ok(ex.regex, `Example ${ex.id} must define regex`);
    assert.ok(ex.explanation, `Example ${ex.id} must define explanation`);
    assert.ok(ex.matchingInput, `Example ${ex.id} must define matchingInput`);
    assert.ok(ex.problematicInput, `Example ${ex.id} must define problematicInput`);
    assert.ok(ex.safeAlternative, `Example ${ex.id} must define safeAlternative`);
    assert.ok(ex.safeExplanation, `Example ${ex.id} must define safeExplanation`);
  });

  // Bounded runner check
  const boundedResult = runBoundedClientMatch('(a+)+$', 'aaaaaaaaaa!');
  assert.ok(boundedResult.success);
  assert.equal(boundedResult.matched, false);
  assert.ok(boundedResult.durationMs < 200, 'Bounded runner must execute quickly without freezing');
});

test('Requirement 3: generateAutomataExamples groups into Accepted, Rejected, and Edge cases', () => {
  const result = generateAutomataExamples(sampleDfa, '(a|b)*abb');

  assert.equal(result.unsupported, false);
  assert.ok(result.examples.length >= 5, 'Must provide at least 5 distinct test strings');
  assert.ok(Array.isArray(result.accepted), 'Must provide accepted list');
  assert.ok(Array.isArray(result.rejected), 'Must provide rejected list');
  assert.ok(Array.isArray(result.edgeCases), 'Must provide edge cases list');

  // Verify uniqueness of candidate inputs
  const inputs = result.examples.map((e) => e.input);
  const uniqueInputs = new Set(inputs);
  assert.equal(uniqueInputs.size, inputs.length, 'All generated examples must be distinct');

  // Verify match results against simulator
  result.examples.forEach((ex) => {
    const verified = verifyAutomatonMatch(sampleDfa, ex.input);
    assert.equal(ex.matches, verified, `Ground-truth label mismatch for input "${ex.input}"`);
    assert.ok(ex.reason, 'Must supply explanatory reason for each example');
  });
});

test('Requirement 3: generateAutomataExamples handles finite/small languages by completing with non-matches', () => {
  const finiteDfa = {
    id: 'single_a',
    alphabet: ['a'],
    start_state: 's0',
    states: [
      { id: 's0', is_start: true, is_accepting: false },
      { id: 's1', is_start: false, is_accepting: true },
    ],
    transitions: [{ from_state: 's0', to_state: 's1', symbol: 'a' }],
  };

  const result = generateAutomataExamples(finiteDfa, 'a');
  assert.ok(result.examples.length >= 5, 'Must guarantee at least 5 examples even for finite language');

  const matches = result.examples.filter((e) => e.matches);
  assert.equal(matches.length, 1, 'Only "a" can match');
  assert.equal(matches[0].input, 'a');

  const nonMatches = result.examples.filter((e) => !e.matches);
  assert.ok(nonMatches.length >= 4, 'Must complete set with verified non-matching strings');
});

test('Requirement 2: regexExplainer generates accurate plain-English and interactive tokens', () => {
  const narrative = explainRegexPlainEnglish('(a|b)*abb');
  assert.ok(narrative.includes('abb'), 'Plain English should mention ending in abb');

  const tokens = tokenizeRegex('(a|b)*abb');
  assert.ok(tokens.length >= 7, 'Should parse all tokens');
  assert.equal(tokens[0].type, 'group');
  assert.equal(tokens[2].type, 'alt');
  assert.equal(tokens[5].type, 'star');

  // Unsupported check
  const lookaheadUnsupported = checkUnsupportedConstructs('(?=abc)def');
  assert.ok(lookaheadUnsupported, 'Must detect lookahead assertion');
  assert.ok(lookaheadUnsupported.explanation.includes('closed under intersection'), 'Must explain regular assertions can describe regular languages');

  const backrefUnsupported = checkUnsupportedConstructs('(a)\\1');
  assert.ok(backrefUnsupported, 'Must detect backreference');
  assert.ok(backrefUnsupported.explanation.includes('in general'), 'Must explain backreferences can describe non-regular languages in general');
  assert.ok(backrefUnsupported.explanation.includes('non-regular for alphabets with at least two symbols'), 'Must state {ww} is non-regular for alphabets with at least two symbols');
  assert.ok(backrefUnsupported.explanation.includes('two identical halves is straightforward'), 'Must state string check of two identical halves is straightforward');
  assert.ok(!backrefUnsupported.explanation.includes('{ww | w ∈ Σ*} is NP-complete'), 'Must not claim {ww} is NP-complete');
  assert.ok(backrefUnsupported.explanation.includes('general regex matching with backreferences, which is NP-complete'), 'Must separate string check from NP-complete general matching');

  const lazyUnsupported = checkUnsupportedConstructs('a*?b');
  assert.ok(lazyUnsupported, 'Must detect lazy quantifier');
  assert.ok(lazyUnsupported.explanation.includes('full-string formal language membership'), 'Must explain greedy vs lazy affects search selection, not full-string language membership');

  // Tokenization of escapes, classes, and epsilon
  const escTokens = tokenizeRegex('\\d+[a-z]*ε');
  assert.equal(escTokens[0].char, '\\d');
  assert.equal(escTokens[0].type, 'char_class');
  assert.equal(escTokens[1].type, 'plus');
  assert.equal(escTokens[2].char, '[a-z]');
  assert.equal(escTokens[2].type, 'char_class');
  assert.equal(escTokens[3].type, 'star');
  assert.equal(escTokens[4].char, 'ε');
  assert.equal(escTokens[4].type, 'epsilon');

  const formalRegex = checkUnsupportedConstructs('(a|b)*abb');
  assert.equal(formalRegex, null, 'Formal regex should not be flagged as unsupported');
});

test('Requirement 4: computeMinimizationDiff accurately compares DFA and Minimized DFA', () => {
  // DFA with 3 states where 2 states merge
  const unminimizedDfa = {
    states: [
      { id: 'q0', is_start: true, is_accepting: false },
      { id: 'q1', is_start: false, is_accepting: true },
      { id: 'q2', is_start: false, is_accepting: true },
    ],
    alphabet: ['a'],
  };

  const minDfa = {
    states: [
      { id: 'm0', is_start: true, is_accepting: false, metadata: { merged_states: ['q0'] } },
      { id: 'm1', is_start: false, is_accepting: true, metadata: { merged_states: ['q1', 'q2'] } },
    ],
    alphabet: ['a'],
  };

  const diff = computeMinimizationDiff(unminimizedDfa, minDfa);
  assert.equal(diff.originalCount, 3);
  assert.equal(diff.minimizedCount, 2);
  assert.equal(diff.statesEliminated, 1);
  assert.equal(diff.reductionPercent, 33);
  assert.equal(diff.mergeGroups.length, 2);
  assert.ok(diff.mergeGroups[1].isMerged, 'State m1 should be flagged as merged');
  assert.deepEqual(diff.mergeGroups[1].mergedDfaStates, ['q1', 'q2']);
  assert.ok(diff.mergeGroups[1].explanation.includes('Myhill-Nerode'), 'Must reference Myhill-Nerode theorem');
  assert.ok(diff.mergeGroups[1].explanation.includes('right-languages'), 'Must explain identical right-languages');
});

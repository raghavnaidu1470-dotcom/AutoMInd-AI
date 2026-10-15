/**
 * Verified Test Matrix for AutoMind-AI
 * =====================================
 * Independently defined expected outcomes across all supported regular expressions,
 * boundary behaviors, syntax errors, and rejection modes.
 */

export const TEST_MATRIX = [
  {
    id: 'lit-concat',
    category: 'Literals & Concatenation',
    regex: 'ab',
    description: 'Exact concatenation of literal characters a then b',
    acceptedStrings: ['ab'],
    rejectedStrings: [
      { input: 'a', reason: 'non-accepting-state', note: 'Input consumed but ends in state q1 (non-accepting)' },
      { input: 'b', reason: 'missing-transition', note: 'No transition on symbol b from start state' },
      { input: 'aba', reason: 'missing-transition', note: 'No transition after second character' },
      { input: '', reason: 'empty-rejected', note: 'Empty string does not satisfy required sequence ab' },
    ],
    expectedAlphabet: ['a', 'b'],
    nfaExpectedStatesMin: 4,
    dfaExpectedStatesMin: 3,
  },
  {
    id: 'alt-group',
    category: 'Alternation & Grouping',
    regex: '(a|b)c',
    description: 'Binary choice between a or b followed by c',
    acceptedStrings: ['ac', 'bc'],
    rejectedStrings: [
      { input: 'c', reason: 'missing-transition', note: 'Missing choice symbol prefix' },
      { input: 'abc', reason: 'missing-transition', note: 'Cannot take both branches sequentially' },
      { input: '', reason: 'empty-rejected', note: 'Empty string rejected' },
      { input: 'a', reason: 'non-accepting-state', note: 'Ends in intermediate state before suffix c' },
    ],
    expectedAlphabet: ['a', 'b', 'c'],
  },
  {
    id: 'repetition-star-plus-opt',
    category: 'Star, Plus & Optional Repetition',
    regex: 'a*b+c?',
    description: 'Zero or more a, one or more b, zero or one c',
    acceptedStrings: ['b', 'bc', 'ab', 'abc', 'aaabbc', 'aaaaab'],
    rejectedStrings: [
      { input: 'a', reason: 'non-accepting-state', note: 'Missing required plus repetition of b' },
      { input: 'c', reason: 'missing-transition', note: 'No path to c without preceding b' },
      { input: '', reason: 'empty-rejected', note: 'Requires at least one b' },
      { input: 'bca', reason: 'missing-transition', note: 'Cannot loop a after trailing c' },
    ],
    expectedAlphabet: ['a', 'b', 'c'],
  },
  {
    id: 'char-class-ranges-escapes',
    category: 'Character Classes, Ranges & Escapes',
    regex: '[a-z]\\d',
    description: 'Single lowercase letter followed by any single digit 0-9',
    acceptedStrings: ['a0', 'z9', 'm5'],
    rejectedStrings: [
      { input: '0a', reason: 'missing-transition', note: 'Order inverted: digit before letter' },
      { input: 'A1', reason: 'missing-transition', note: 'Uppercase outside range [a-z]' },
      { input: 'a', reason: 'non-accepting-state', note: 'Digit suffix missing' },
      { input: '', reason: 'empty-rejected', note: 'Empty string rejected' },
    ],
  },
  {
    id: 'empty-accepted',
    category: 'Empty-String Acceptance',
    regex: '(a|b)*',
    description: 'Arbitrary sequence of a and b, including empty string',
    acceptedStrings: ['', 'a', 'b', 'ab', 'ba', 'aaaa'],
    rejectedStrings: [
      { input: 'c', reason: 'missing-transition', note: 'Symbol outside alphabet {a, b}' },
      { input: '1', reason: 'missing-transition', note: 'Symbol outside alphabet {a, b}' },
    ],
    acceptsEmpty: true,
  },
  {
    id: 'empty-rejected',
    category: 'Empty-String Rejection',
    regex: '(a|b)+',
    description: 'Non-empty sequence of a and b',
    acceptedStrings: ['a', 'b', 'ab', 'ba', 'aba'],
    rejectedStrings: [
      { input: '', reason: 'empty-rejected', note: 'Positive closure requires >= 1 symbol' },
      { input: 'c', reason: 'missing-transition', note: 'Symbol outside alphabet {a, b}' },
    ],
    acceptsEmpty: false,
  },
  {
    id: 'nested-larger-automaton',
    category: 'Nested Expressions & Larger Automaton',
    regex: '(a|b)*abb',
    description: 'Strings ending with abb over alphabet {a, b}',
    acceptedStrings: ['abb', 'ababb', 'babb', 'aababb'],
    rejectedStrings: [
      { input: 'abab', reason: 'non-accepting-state', note: 'Ends in non-accepting state q2 (seen ab)' },
      { input: 'bba', reason: 'non-accepting-state', note: 'Ends in non-accepting state q1 (seen a)' },
      { input: 'x', reason: 'missing-transition', note: 'Symbol x not in language alphabet' },
    ],
    expectedStates: {
      nfa: 11,
      dfa: 4,
      minimizedDfa: 4,
    },
  },
  {
    id: 'binary-larger-automaton',
    category: 'Larger Binary Automaton',
    regex: '(01)*101',
    description: 'Repeated 01 pairs followed by suffix 101',
    acceptedStrings: ['101', '01101', '0101101'],
    rejectedStrings: [
      { input: '0101', reason: 'non-accepting-state', note: 'Trailing 101 missing' },
      { input: '111', reason: 'missing-transition', note: 'No 11 transition from state' },
      { input: '', reason: 'empty-rejected', note: 'Empty string rejected' },
    ],
    expectedStates: {
      nfa: 12,
      dfa: 5,
      minimizedDfa: 5,
    },
  },
];

export const SYNTAX_ERROR_MATRIX = [
  {
    pattern: '(a|b',
    expectedMessageSubstring: 'Unbalanced parenthesis',
    expectedPosition: 0,
    expectedTip: "Add a closing parenthesis ')'",
  },
  {
    pattern: 'a**',
    expectedMessageSubstring: "Multiple repeat operators '*' and '*'",
    expectedPosition: 2,
    expectedTip: 'Remove the redundant repeat quantifier',
  },
  {
    pattern: 'a|',
    expectedMessageSubstring: "Empty alternation branch after '|'",
    expectedPosition: 1,
    expectedTip: "Provide an alternative pattern after '|'",
  },
  {
    pattern: '\\1',
    expectedMessageSubstring: "Backreferences '\\1' are not supported in regular automata",
    expectedTip: 'Remove backreferences',
  },
  {
    pattern: '(?=abc)',
    expectedMessageSubstring: 'Lookaround assertions and non-capturing groups',
    expectedTip: 'Rewrite without lookaround assertions',
  },
];

export const REDOS_DEMO_CASES = [
  {
    id: 'redos-safe-linear',
    regex: '(a|b)*abb',
    expectedRisk: 'linear',
    isVulnerable: false,
    hasAttackString: false,
    label: 'Linear Reference Baseline',
  },
  {
    id: 'redos-nested-plus',
    regex: '(a+)+$',
    expectedRisk: 'exponential',
    isVulnerable: true,
    hasAttackString: true,
    offendingSpan: '0-6: (a+)+$',
    safeAlternative: 'a+$',
    label: 'Nested Positive Closure',
  },
  {
    id: 'redos-overlapping-alt',
    regex: '(a|aa)+$',
    expectedRisk: 'exponential',
    isVulnerable: true,
    hasAttackString: true,
    safeAlternative: 'a+$',
    label: 'Overlapping Alternation in Repetition',
  },
  {
    id: 'redos-polynomial-adjacent',
    regex: 'a*a*b',
    expectedRisk: 'polynomial',
    isVulnerable: true,
    hasAttackString: true,
    safeAlternative: 'a*b',
    label: 'Adjacent Identical Quantifiers',
  },
];

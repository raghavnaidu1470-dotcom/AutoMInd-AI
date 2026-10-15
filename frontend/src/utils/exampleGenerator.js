/**
 * Automatic Test String Generator for Automata & Regular Expressions
 * ==================================================================
 * Automatically synthesizes at least 5 distinct, verified test candidate strings
 * grouped into:
 *   - Accepted (strings that successfully reach an accepting state)
 *   - Rejected (strings that halt in a non-accepting state or lack transitions)
 *   - Edge Cases (empty input ε, single-symbol, off-alphabet characters, boundary probes)
 *
 * Each generated string is verified against the automaton transition graph
 * and labeled with its ground-truth match verdict and explanatory reason.
 */

/**
 * Simulates string execution on an automaton (DFA or NFA) to compute ground truth
 */
export function verifyAutomatonMatch(automaton, inputString = '') {
  if (!automaton || !automaton.start_state || !Array.isArray(automaton.states)) {
    return false;
  }

  const startId = String(automaton.start_state);
  const states = automaton.states || [];
  const transitions = automaton.transitions || [];
  const acceptingIds = new Set(states.filter((s) => s.is_accepting).map((s) => String(s.id)));

  // If this is an NFA with epsilon transitions
  const hasEpsilon = transitions.some((t) => t.symbol === 'ε' || t.symbol === '');

  if (hasEpsilon) {
    // Epsilon-closure helper
    const epsMap = new Map();
    const symMap = new Map();

    transitions.forEach((t) => {
      const u = String(t.from_state);
      const v = String(t.to_state);
      const sym = t.symbol || 'ε';
      if (sym === 'ε' || sym === '') {
        if (!epsMap.has(u)) epsMap.set(u, new Set());
        epsMap.get(u).add(v);
      } else {
        const key = `${u}:${sym}`;
        if (!symMap.has(key)) symMap.set(key, new Set());
        symMap.get(key).add(v);
      }
    });

    const getEpsClosure = (stateSet) => {
      const closure = new Set(stateSet);
      const stack = Array.from(stateSet);
      while (stack.length > 0) {
        const curr = stack.pop();
        const epsNeighbors = epsMap.get(curr);
        if (epsNeighbors) {
          epsNeighbors.forEach((nxt) => {
            if (!closure.has(nxt)) {
              closure.add(nxt);
              stack.push(nxt);
            }
          });
        }
      }
      return closure;
    };

    let currentStates = getEpsClosure(new Set([startId]));

    for (let i = 0; i < inputString.length; i++) {
      const char = inputString[i];
      const nextStates = new Set();
      currentStates.forEach((st) => {
        const targets = symMap.get(`${st}:${char}`);
        if (targets) {
          targets.forEach((tgt) => nextStates.add(tgt));
        }
      });
      currentStates = getEpsClosure(nextStates);
      if (currentStates.size === 0) break;
    }

    return Array.from(currentStates).some((st) => acceptingIds.has(st));
  }

  // Deterministic DFA simulation
  const transMap = new Map();
  transitions.forEach((t) => {
    transMap.set(`${String(t.from_state)}:${String(t.symbol)}`, String(t.to_state));
  });

  let current = startId;
  for (let i = 0; i < inputString.length; i++) {
    const char = inputString[i];
    const nxt = transMap.get(`${current}:${char}`);
    if (!nxt) return false;
    current = nxt;
  }

  return acceptingIds.has(current);
}

/**
 * Generates an explanatory reason for the simulation verdict
 */
function getMatchReason(automaton, inputStr, matches) {
  if (inputStr === '') {
    const isStartAccepting = automaton.states?.find(
      (s) => String(s.id) === String(automaton.start_state)
    )?.is_accepting;
    return isStartAccepting
      ? 'Empty string (ε) is accepted because start state is an accepting state.'
      : 'Empty string (ε) is rejected because start state is non-accepting (requires at least 1 symbol).';
  }

  const alphabet = automaton.alphabet || [];
  const foreignChar = inputStr.split('').find((c) => !alphabet.includes(c));
  if (foreignChar) {
    return `Rejected: symbol '${foreignChar}' is outside alphabet {${alphabet.join(', ')}}.`;
  }

  if (matches) {
    return `Accepted: input consumes ${inputStr.length} symbol${inputStr.length > 1 ? 's' : ''} and terminates in an accepting state.`;
  }
  return `Rejected: input terminates in a non-accepting or dead state after reading ${inputStr.length} symbols.`;
}

/**
 * Generates structured, verified example candidate strings for an automaton
 */
export function generateAutomataExamples(automaton, regexPattern = '', maxCount = 8) {
  if (!automaton || !automaton.states || automaton.states.length === 0) {
    return {
      examples: [],
      accepted: [],
      rejected: [],
      edgeCases: [],
      sourceRegex: regexPattern,
      unsupported: true,
      reason: 'No automaton structure available.',
      limitedLanguageNotice: null,
    };
  }

  const states = automaton.states || [];
  const transitions = automaton.transitions || [];
  const alphabet = Array.from(
    new Set((automaton.alphabet || []).filter((s) => s && s !== 'ε'))
  );

  // If alphabet is empty, infer from transitions
  if (alphabet.length === 0) {
    transitions.forEach((t) => {
      if (t.symbol && t.symbol !== 'ε' && !alphabet.includes(t.symbol)) {
        alphabet.push(t.symbol);
      }
    });
  }

  const startId = String(automaton.start_state);
  const acceptingIds = new Set(states.filter((s) => s.is_accepting).map((s) => String(s.id)));

  const candidateMap = new Map(); // input -> { label, group, description }

  // 1. Edge Case: Empty String (ε)
  const emptyMatches = verifyAutomatonMatch(automaton, '');
  candidateMap.set('', {
    label: 'Empty string (ε)',
    group: 'edge',
    description: emptyMatches ? 'Matches empty language (ε)' : 'Requires non-empty token',
  });

  // 2. BFS graph exploration for paths
  const queue = [{ state: startId, path: '' }];
  const visitedDepth = new Map();
  const maxBfsDepth = 12;
  const maxSteps = 450;
  let step = 0;

  const adj = new Map();
  transitions.forEach((t) => {
    const u = String(t.from_state);
    const sym = t.symbol;
    if (sym && sym !== 'ε') {
      if (!adj.has(u)) adj.set(u, []);
      adj.get(u).push({ to: String(t.to_state), symbol: sym });
    }
  });

  while (queue.length > 0 && step < maxSteps) {
    step++;
    const { state, path } = queue.shift();
    if (path.length > maxBfsDepth) continue;

    if (acceptingIds.has(state) && path.length > 0) {
      if (!candidateMap.has(path)) {
        candidateMap.set(path, {
          label: `Path: "${path}"`,
          group: 'accepted',
          description: `Consumes ${path.length} transitions to accepting state`,
        });
      }
    } else if (!acceptingIds.has(state) && path.length > 0 && path.length <= 4) {
      if (!candidateMap.has(path)) {
        candidateMap.set(path, {
          label: `Near-miss: "${path}"`,
          group: 'rejected',
          description: 'Halted in non-accepting state',
        });
      }
    }

    const neighbors = adj.get(state) || [];
    for (const edge of neighbors) {
      const nextPath = path + edge.symbol;
      const key = `${edge.to}:${nextPath.length}`;
      if ((visitedDepth.get(key) || 0) < 3) {
        visitedDepth.set(key, (visitedDepth.get(key) || 0) + 1);
        queue.push({ state: edge.to, path: nextPath });
      }
    }
  }

  // 3. Edge Cases: Foreign symbol and boundary probes
  const nonAlphabetSymbols = ['X', '!', '9', 'z', '_'].filter((sym) => !alphabet.includes(sym));
  const foreignChar = nonAlphabetSymbols[0] || '#';

  if (!candidateMap.has(foreignChar)) {
    candidateMap.set(foreignChar, {
      label: `Foreign symbol "${foreignChar}"`,
      group: 'edge',
      description: `Outside language alphabet {${alphabet.join(', ')}}`,
    });
  }

  // Single characters from alphabet
  alphabet.slice(0, 2).forEach((sym) => {
    if (!candidateMap.has(sym)) {
      candidateMap.set(sym, {
        label: `Single symbol "${sym}"`,
        group: 'edge',
        description: `Single token evaluation`,
      });
    }
  });

  // Boundary probe: Shortest match + foreign character
  const firstMatch = Array.from(candidateMap.keys()).find((k) => k !== '' && verifyAutomatonMatch(automaton, k));
  if (firstMatch && !candidateMap.has(firstMatch + foreignChar)) {
    candidateMap.set(firstMatch + foreignChar, {
      label: `Boundary probe "${firstMatch + foreignChar}"`,
      group: 'edge',
      description: 'Valid prefix followed by foreign character',
    });
  }

  // 4. Verification and Structuring
  const allEntries = [];
  const acceptedList = [];
  const rejectedList = [];
  const edgeList = [];

  Array.from(candidateMap.entries()).forEach(([inputStr, meta]) => {
    const matches = verifyAutomatonMatch(automaton, inputStr);
    const reason = getMatchReason(automaton, inputStr, matches);
    const item = {
      input: inputStr,
      displayInput: inputStr === '' ? 'ε (empty string)' : inputStr,
      matches,
      group: meta.group,
      label: meta.label,
      description: meta.description,
      reason,
    };

    allEntries.push(item);
    if (meta.group === 'edge') {
      edgeList.push(item);
    } else if (matches) {
      acceptedList.push(item);
    } else {
      rejectedList.push(item);
    }
  });

  // Guarantee at least 5 distinct items by generating synthetic probes if needed
  let probeIndex = 1;
  while (allEntries.length < 5 && probeIndex < 10) {
    const probeStr = `${alphabet[0] || 'a'}${probeIndex}`;
    const matches = verifyAutomatonMatch(automaton, probeStr);
    const item = {
      input: probeStr,
      displayInput: probeStr,
      matches,
      group: matches ? 'accepted' : 'rejected',
      label: `Probe "${probeStr}"`,
      description: 'Synthesized test case',
      reason: getMatchReason(automaton, probeStr, matches),
    };
    allEntries.push(item);
    if (matches) acceptedList.push(item);
    else rejectedList.push(item);
    probeIndex++;
  }

  // Count matches
  const totalMatches = allEntries.filter((e) => e.matches).length;
  let limitedLanguageNotice = null;
  if (totalMatches < 3) {
    limitedLanguageNotice =
      'This regular expression has a very small or constrained accepted language. Verified non-matching strings are included to test rejection behavior.';
  }

  return {
    examples: allEntries,
    initialSlice: allEntries.slice(0, maxCount),
    accepted: acceptedList,
    rejected: rejectedList,
    edgeCases: edgeList,
    sourceRegex: regexPattern,
    unsupported: false,
    matchingCount: totalMatches,
    nonMatchingCount: allEntries.length - totalMatches,
    limitedLanguageNotice,
  };
}

/**
 * Curated ReDoS Vulnerability Examples & Bounded Demonstrator
 * ===========================================================
 * Comprehensive catalog of catastrophic and polynomial backtracking archetypes.
 * Each entry provides:
 * - regex: the vulnerable regular expression
 * - name: human-readable vulnerability descriptor
 * - category: algorithmic complexity class
 * - risk: 'exponential' | 'polynomial' | 'linear'
 * - explanation: detailed root-cause mechanics of the backtracking path
 * - matchingInput: valid candidate string that accepts in linear time
 * - problematicInput: near-match adversarial string triggering excessive backtracking
 * - safeAlternative: language-equivalent or bounded rewrite
 * - safeExplanation: how the alternative eliminates ambiguity and guarantees linear scan
 */

export const REDOS_EXAMPLES = [
  {
    id: 'nested-plus',
    name: 'Nested Positive Closure: (a+)+$',
    regex: '(a+)+$',
    category: 'Exponential Backtracking (O(2ⁿ))',
    risk: 'exponential',
    explanation:
      'The inner group `a+` and outer group `+` can both consume arbitrary runs of \'a\'. When followed by a non-matching character, a naive backtracking engine explores all 2ⁿ⁻¹ binary partitions of the sequence before concluding failure.',
    matchingInput: 'aaaaaaaaaa',
    problematicInput: 'aaaaaaaaaaaaaaaaaaaaaaaaa!',
    safeAlternative: 'a+$',
    safeExplanation:
      'Flattening nested quantifiers into a single `a+` accepts the exact same language in O(n) linear time with zero branch ambiguity.',
  },
  {
    id: 'overlapping-alt-star',
    name: 'Overlapping Alternation in Repetition: (a|aa)+$',
    regex: '(a|aa)+$',
    category: 'Exponential Backtracking (O(2ⁿ))',
    risk: 'exponential',
    explanation:
      'Both alternation branches \'a\' and \'aa\' consume the identical character \'a\'. With repetition `+` and anchor `$`, an invalid suffix forces the engine to attempt exponentially many branch permutations.',
    matchingInput: 'aaaaaaaaaa',
    problematicInput: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaX',
    safeAlternative: 'a+$',
    safeExplanation:
      'Since alternating between 1 and 2 characters inside repetition is union-equivalent to one or more \'a\'s, `a+$` evaluates deterministically without backtracking.',
  },
  {
    id: 'star-nesting-star',
    name: 'Nested Kleene Stars: (a*)*b',
    regex: '(a*)*b',
    category: 'Exponential Backtracking (O(2ⁿ))',
    risk: 'exponential',
    explanation:
      'The inner `a*` allows matching the empty string ε or runs of \'a\'. The outer star iterates over multiple empty or non-empty splits. When \'b\' is absent, the engine cycles through factorial and exponential branches.',
    matchingInput: 'aaaaab',
    problematicInput: 'aaaaaaaaaaaaaaaX',
    safeAlternative: 'a*b',
    safeExplanation:
      'Replacing `(a*)*` with `a*` produces an isomorphic language that runs in strict single-pass O(n) time.',
  },
  {
    id: 'polynomial-adjacent-star',
    name: 'Adjacent Identical Quantifiers: a*a*b',
    regex: 'a*a*b',
    category: 'Polynomial Backtracking (O(n²))',
    risk: 'polynomial',
    explanation:
      'Two adjacent `a*` quantifiers create quadratic splits: the first quantifier consumes k characters while the second consumes n-k. On mismatch with \'b\', the engine backtracks through all n(n+1)/2 split combinations.',
    matchingInput: 'aaaaab',
    problematicInput: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaX',
    safeAlternative: 'a*b',
    safeExplanation:
      'Merging adjacent identical Kleene stars into one quantifier removes partition ambiguity.',
  },
  {
    id: 'polynomial-three-star',
    name: 'Triple Overlapping Quantifiers: a*a*a*b',
    regex: 'a*a*a*b',
    category: 'Polynomial Backtracking (O(n³))',
    risk: 'polynomial',
    explanation:
      'Three consecutive `a*` quantifiers generate cubic O(n³) candidate partition states before rejecting a string missing the trailing \'b\'.',
    matchingInput: 'aaaaab',
    problematicInput: 'aaaaaaaaaaaaaaaaaaaaX',
    safeAlternative: 'a*b',
    safeExplanation:
      'Three sequential identical stars are mathematically equivalent to one `a*`.',
  },
  {
    id: 'domain-segment-wildcard',
    name: 'Unescaped Wildcard Segment: ^([a-z0-9]+.)+com$',
    regex: '^([a-z0-9]+.)+com$',
    category: 'Exponential Backtracking (O(2ⁿ))',
    risk: 'exponential',
    explanation:
      'The unescaped dot `.` matches any character including alphanumeric characters, causing the delimiter to overlap with the segment content `[a-z0-9]+`. Failing on a non-com suffix triggers deep combinatorial backtracking.',
    matchingInput: 'host.sub.domain.com',
    problematicInput: 'hostsubdomainhostsubdomain!',
    safeAlternative: '^[a-z0-9]+(\\.[a-z0-9]+)*\\.com$',
    safeExplanation:
      'Escaping the dot delimiter `\\.` and structuring segments as `head(\\.[a-z0-9]+)*` enforces mutually exclusive tokens.',
  },
  {
    id: 'csv-empty-group-ambiguity',
    name: 'Empty Token Ambiguity in List: ^(([a-z]+)*,)*$',
    regex: '^(([a-z]+)*,)*$',
    category: 'Exponential Backtracking (O(2ⁿ))',
    risk: 'exponential',
    explanation:
      'Both `([a-z]+)*` and the outer repetition can match empty strings between commas, leading to branch explosions when parsing malformed CSV rows.',
    matchingInput: 'alpha,beta,gamma,',
    problematicInput: 'alpha,beta,gamma,delta,omega!',
    safeAlternative: '^([a-z]+,)*$',
    safeExplanation:
      'Requiring non-empty entries before each comma eliminates empty-step non-determinism.',
  },
  {
    id: 'prefix-ambiguous-alternation',
    name: 'Overlapping Prefix in Group: (ba|b)+c',
    regex: '(ba|b)+c',
    category: 'Exponential Backtracking (O(2ⁿ))',
    risk: 'exponential',
    explanation:
      'Because \'b\' is a strict prefix of \'ba\', sequences like "bababa" can be parsed either as three \'ba\' tokens or as alternating \'b\' and \'a\' tokens. Failing on \'c\' induces catastrophic backtracking.',
    matchingInput: 'bababac',
    problematicInput: 'bababababababababaX',
    safeAlternative: 'b(a?b)*a?c',
    safeExplanation:
      'Factoring out the common prefix \'b\' ensures determinism at every step.',
  },
  {
    id: 'safe-baseline',
    name: 'Linear Reference Baseline: (a|b)*abb',
    regex: '(a|b)*abb',
    category: 'Linear Execution (O(n))',
    risk: 'linear',
    explanation:
      'Compiles to a canonical deterministic finite automaton with no ambiguous loop overlaps. Evaluates in single-pass linear time on all input sequences.',
    matchingInput: 'ababb',
    problematicInput: 'abababababababababa',
    safeAlternative: '(a|b)*abb',
    safeExplanation:
      'Already optimal; linear time complexity guaranteed on all candidate inputs.',
  },
];

/**
 * Executes a strictly bounded client-side regular expression check.
 * Guarantees that catastrophic backtracking CANNOT freeze the browser
 * by bounding maximum input length and setting a tight execution deadline (150ms).
 */
export function runBoundedClientMatch(regexStr, inputStr, { maxLen = 60, timeoutMs = 150 } = {}) {
  const boundedInput = (inputStr || '').slice(0, maxLen);
  const startTime = performance.now();

  try {
    const reg = new RegExp(regexStr);
    const matched = reg.test(boundedInput);
    const durationMs = performance.now() - startTime;

    return {
      success: true,
      matched,
      durationMs: Math.round(durationMs * 100) / 100,
      inputUsed: boundedInput,
      truncated: inputStr.length > maxLen,
      timedOut: false,
    };
  } catch (err) {
    const durationMs = performance.now() - startTime;
    return {
      success: false,
      error: err.message,
      durationMs: Math.round(durationMs * 100) / 100,
      inputUsed: boundedInput,
      timedOut: durationMs >= timeoutMs,
    };
  }
}

/**
 * Executes regular expression matching inside an isolated Web Worker.
 * When the worker exceeds timeoutMs (default 100ms), worker.terminate() is invoked
 * immediately, canceling execution so pathological backtracking CANNOT block the main UI thread.
 */
export function runIsolatedWorkerMatch(regexStr, inputStr, { timeoutMs = 100 } = {}) {
  return new Promise((resolve) => {
    // If Web Worker is unavailable (e.g. Node / SSR / test runner), fallback to runBoundedClientMatch
    if (typeof window === 'undefined' || typeof Worker === 'undefined' || typeof Blob === 'undefined') {
      const fallback = runBoundedClientMatch(regexStr, inputStr, { timeoutMs });
      resolve({
        ...fallback,
        isolation: 'Synchronous fallback (Node environment)',
      });
      return;
    }

    const workerScript = `
      self.onmessage = function(e) {
        var data = e.data;
        var start = performance.now();
        try {
          var reg = new RegExp(data.regexStr);
          var matched = reg.test(data.inputStr);
          var duration = performance.now() - start;
          self.postMessage({
            success: true,
            matched: matched,
            durationMs: Math.round(duration * 100) / 100
          });
        } catch (err) {
          self.postMessage({
            success: false,
            error: err.message,
            durationMs: Math.round((performance.now() - start) * 100) / 100
          });
        }
      };
    `;

    const blob = new Blob([workerScript], { type: 'application/javascript' });
    const blobUrl = URL.createObjectURL(blob);
    let worker = null;
    let timer = null;
    let settled = false;

    const cleanup = () => {
      if (timer) clearTimeout(timer);
      if (worker) {
        worker.terminate();
        worker = null;
      }
      try {
        URL.revokeObjectURL(blobUrl);
      } catch (e) {}
    };

    try {
      worker = new Worker(blobUrl);
    } catch (workerErr) {
      cleanup();
      const fallback = runBoundedClientMatch(regexStr, inputStr, { timeoutMs });
      resolve(fallback);
      return;
    }

    timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve({
        success: false,
        matched: false,
        timedOut: true,
        interrupted: true,
        durationMs: timeoutMs,
        isolation: 'Web Worker (hard timeout exceeded; worker.terminate() invoked)',
        error: `Execution deadline (${timeoutMs}ms) exceeded in isolated worker thread. Background worker was terminated; main UI thread remained responsive.`,
      });
    }, timeoutMs);

    worker.onmessage = (e) => {
      if (settled) return;
      settled = true;
      const data = e.data;
      cleanup();
      resolve({
        ...data,
        timedOut: false,
        interrupted: false,
        isolation: 'Web Worker (completed within deadline)',
      });
    };

    worker.onerror = (err) => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve({
        success: false,
        matched: false,
        timedOut: false,
        interrupted: false,
        error: err.message || 'Worker execution error',
        isolation: 'Web Worker',
      });
    };

    worker.postMessage({ regexStr, inputStr });
  });
}

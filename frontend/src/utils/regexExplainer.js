/**
 * Regex Explainer & Tokenizer
 * ===========================
 * Generates plain-English explanations of regular expressions, parses tokens
 * with their semantic definitions, detects unsupported programming regex syntax
 * (PCRE/backreferences/lookaheads), and maps tokens to theoretical constructs.
 */

// Educational descriptions of core regular expression operators
export const OPERATOR_DEFINITIONS = {
  literal: 'Literal character: matches this exact symbol in the input string.',
  concat: 'Concatenation: matches the first subexpression followed immediately by the second.',
  alt: 'Alternation (|): represents a choice; matches either the left or the right expression.',
  star: 'Kleene Star (*): matches the preceding element zero or more times.',
  plus: 'Plus quantifier (+): matches the preceding element one or more times.',
  optional: 'Optional (?): matches the preceding element zero or one time.',
  group: 'Parenthesized group: groups subexpressions together as a single atomic unit.',
  char_class: 'Character class: matches any single character contained within the brackets.',
  anchor_start: 'Start anchor (^): asserts that matching begins at the start of the string.',
  anchor_end: 'End anchor ($): asserts that matching ends at the end of the string.',
  epsilon: 'Epsilon (ε): matches the empty string without consuming any character.',
  escape: 'Escaped symbol / shorthand: matches escaped metacharacters or shorthand sets (\\d, \\w, \\s).',
};

// Theory of Computation notes on language recognition vs programming regex engines
export const THEORY_NOTES = {
  matchingSemantics:
    'Full-String Acceptance Semantics: AutoMind AI tests whether the entire candidate string w belongs to the formal language L(r) (i.e. w ∈ L(r)), consuming every character from the start state to an accepting state. In contrast, programming regex engines typically perform unanchored substring search unless explicit ^ and $ anchors are specified.',
  dfaComplexity:
    'DFA Execution Complexity: For a fixed, compiled DFA, string recognition requires strictly linear time O(|w|) in the length of the input—exactly one deterministic state transition per character. However, compiling a regex to a DFA via Thompson construction and subset determinization can incur worst-case exponential state explosion O(2^|Q|).',
  lookarounds:
    'Lookarounds & Regularity: Lookaround assertions over regular subpatterns can still describe regular languages (as regular languages are closed under intersection and complement). However, this application does not currently support them because standard Thompson NFA and subset construction engines do not implement zero-width context assertions.',
  backreferences:
    'Backreferences & Non-Regularity: Backreferences (e.g. \\1) allow regexes to describe non-regular languages in general. For example, the language {ww | w ∈ Σ*} is non-regular for alphabets with at least two symbols, even though checking whether a specific string consists of two identical halves is straightforward (O(n) linear check). Finite automata cannot recognize such languages because comparing unbounded repeated substrings requires unbounded memory. (Separately, the general decision problem of matching an arbitrary regular expression with backreferences against a string is NP-complete.)',
  quantifierGreediness:
    'Greedy vs Lazy Quantifiers: Greedy (*, +) and lazy (*?, +?) quantifiers affect match selection and backtracking order during substring search in programming engines. For full-string language membership in the supported regular subset, greedy and lazy forms recognize the exact same set of strings.',
  tokenMapping:
    'Token-to-Graph Mapping: Direct 1-to-1 visual highlighting from regex tokens to graph nodes is unavailable because finite automata are synthesized through global transformations (Thompson NFA composition, powerset determinization, and Hopcroft partitioning). Use the State Inspector to view precise state origins.',
};

// Supported syntax catalog for education
export const SUPPORTED_SYNTAX = [
  { construct: 'a, b, 0, 1', name: 'Literal symbols', description: 'Matches the exact character from the alphabet.', formal: 'a ∈ Σ' },
  { construct: 'ab', name: 'Concatenation', description: 'Reads symbol a then symbol b in sequence.', formal: 'L(r₁) · L(r₂)' },
  { construct: 'a|b', name: 'Alternation (Union)', description: 'Chooses either branch a or branch b.', formal: 'L(r₁) ∪ L(r₂)' },
  { construct: 'a*', name: 'Kleene Star', description: 'Repeats a zero or more times (including empty string).', formal: 'L(r)*' },
  { construct: 'a+', name: 'Plus Quantifier', description: 'Repeats a one or more times (equivalent to aa*).', formal: 'L(r) · L(r)*' },
  { construct: 'a?', name: 'Optional Quantifier', description: 'Matches a zero or one time (equivalent to a|ε).', formal: 'L(r) ∪ {ε}' },
  { construct: '(...)', name: 'Grouping', description: 'Enforces precedence and defines a subexpression.', formal: '(r)' },
  { construct: '[a-z], [0-9]', name: 'Character Classes', description: 'Shorthand for union of all characters in the range.', formal: '∪ cᵢ' },
  { construct: '\\d, \\w, \\s', name: 'Character Shorthands', description: 'Digits (0-9), word characters, or whitespace.', formal: '∪ cᵢ' },
  { construct: '^, $', name: 'String Anchors', description: 'Specifies start and end boundaries of the input string.', formal: 'Full-string semantics' },
  { construct: 'ε', name: 'Epsilon', description: 'The empty string containing zero symbols.', formal: 'ε (length 0)' },
];

// Unsupported features catalog (distinguishing formal languages from programming engines)
export const UNSUPPORTED_FEATURES = [
  {
    pattern: /\(\?<=|\(\?<!|\(\?=|!\(\?!/,
    name: 'Lookaround Assertions',
    syntax: '(?=...), (?!...), (?<=...)',
    explanation:
      'Lookaround assertions over regular subpatterns can still describe regular languages (regular languages are closed under intersection and complement). However, this application does not currently support them because standard Thompson NFA and subset construction engines do not implement zero-width lookaround transitions.',
  },
  {
    pattern: /\\([1-9])/,
    name: 'Backreferences',
    syntax: '\\1, \\2',
    explanation:
      'Backreferences can describe non-regular languages in general. For example, {ww | w ∈ Σ*} is non-regular for alphabets with at least two symbols, although checking whether a given string consists of two identical halves is straightforward. Finite state automata cannot support backreferences in general because comparing repeated substrings requires unbounded memory. (This is distinct from general regex matching with backreferences, which is NP-complete).',
  },
  {
    pattern: /\*\?|\+\?|\?\?/,
    name: 'Lazy / Non-greedy Quantifiers',
    syntax: '*?, +?, ??',
    explanation:
      'Greedy versus lazy quantifiers affect match selection priority during substring search in backtracking engines. For full-string formal language membership in the supported regular subset, greedy and lazy quantifiers recognize the exact same set of strings.',
  },
  {
    pattern: /\(\?P<|\(\?<[a-zA-Z]/,
    name: 'Named Capture Groups',
    syntax: '(?<name>...)',
    explanation:
      'Named capture groups are runtime data extraction features of programming libraries rather than formal language recognizers.',
  },
];

/**
 * Checks for unsupported programming-regex features
 */
export function checkUnsupportedConstructs(regexStr) {
  if (!regexStr) return null;
  for (const feat of UNSUPPORTED_FEATURES) {
    if (feat.pattern.test(regexStr)) {
      return feat;
    }
  }
  return null;
}

/**
 * Tokenizes regex into interactive tokens with position and meaning
 */
export function tokenizeRegex(regexStr) {
  if (!regexStr) return [];
  const tokens = [];
  let i = 0;
  const n = regexStr.length;

  while (i < n) {
    const char = regexStr[i];

    // Escaped sequences and shorthands: \d, \w, \s, \*, \\, etc.
    if (char === '\\' && i + 1 < n) {
      const next = regexStr[i + 1];
      const escStr = `\\${next}`;
      let label = `Escaped '${next}'`;
      let meaning = `Matches the literal character '${next}'.`;
      let type = 'literal';

      if (next === 'd') {
        label = 'Digit shorthand \\d';
        meaning = 'Matches any digit character from 0 through 9.';
        type = 'char_class';
      } else if (next === 'w') {
        label = 'Word shorthand \\w';
        meaning = 'Matches any ASCII letter, digit, or underscore.';
        type = 'char_class';
      } else if (next === 's') {
        label = 'Whitespace shorthand \\s';
        meaning = 'Matches a whitespace character (space).';
        type = 'char_class';
      }

      tokens.push({
        index: i,
        char: escStr,
        type,
        label,
        meaning,
      });
      i += 2;
    } else if (char === 'ε') {
      tokens.push({
        index: i,
        char: 'ε',
        type: 'epsilon',
        label: 'Epsilon ε',
        meaning: 'Matches the empty string (0 symbols) without consuming input.',
      });
      i++;
    } else if (char === '.') {
      tokens.push({
        index: i,
        char: '.',
        type: 'char_class',
        label: 'Wildcard dot .',
        meaning: 'Matches any single symbol from the alphabet.',
      });
      i++;
    } else if (char === '(') {
      tokens.push({
        index: i,
        char,
        type: 'group',
        label: 'Group open (',
        meaning: 'Groups the enclosed subexpression to control operator precedence.',
      });
      i++;
    } else if (char === ')') {
      tokens.push({
        index: i,
        char,
        type: 'group',
        label: 'Group close )',
        meaning: 'Closes the grouped subexpression.',
      });
      i++;
    } else if (char === '|') {
      tokens.push({
        index: i,
        char,
        type: 'alt',
        label: 'Alternation |',
        meaning: 'Choose either the pattern before or the pattern after this operator.',
      });
      i++;
    } else if (char === '*') {
      tokens.push({
        index: i,
        char,
        type: 'star',
        label: 'Kleene Star *',
        meaning: 'Repeat the preceding element zero or more times (may match empty string).',
      });
      i++;
    } else if (char === '+') {
      tokens.push({
        index: i,
        char,
        type: 'plus',
        label: 'Plus quantifier +',
        meaning: 'Repeat the preceding element one or more times.',
      });
      i++;
    } else if (char === '?') {
      tokens.push({
        index: i,
        char,
        type: 'optional',
        label: 'Optional ?',
        meaning: 'The preceding element may appear zero or one time.',
      });
      i++;
    } else if (char === '^') {
      tokens.push({
        index: i,
        char,
        type: 'anchor_start',
        label: 'Start anchor ^',
        meaning: 'Requires the match to begin at the start of the string (full-string semantics).',
      });
      i++;
    } else if (char === '$') {
      tokens.push({
        index: i,
        char,
        type: 'anchor_end',
        label: 'End anchor $',
        meaning: 'Requires the match to conclude at the end of the string (full-string semantics).',
      });
      i++;
    } else if (char === '[') {
      // Find matching unescaped bracket
      let closeIdx = -1;
      for (let j = i + 1; j < n; j++) {
        if (regexStr[j] === '\\' && j + 1 < n) {
          j++;
        } else if (regexStr[j] === ']') {
          closeIdx = j;
          break;
        }
      }

      if (closeIdx !== -1) {
        const fullClass = regexStr.slice(i, closeIdx + 1);
        const isNegated = fullClass.startsWith('[^');
        tokens.push({
          index: i,
          char: fullClass,
          type: 'char_class',
          label: `Character class ${fullClass}`,
          meaning: isNegated
            ? `Matches any character except those in ${fullClass}.`
            : `Matches any single character from the set ${fullClass}.`,
        });
        i = closeIdx + 1;
      } else {
        tokens.push({
          index: i,
          char,
          type: 'literal',
          label: `Literal '${char}'`,
          meaning: `Matches the literal character '${char}'.`,
        });
        i++;
      }
    } else {
      tokens.push({
        index: i,
        char,
        type: 'literal',
        label: `Literal '${char}'`,
        meaning: `Matches the literal character '${char}' from the alphabet.`,
      });
      i++;
    }
  }

  return tokens;
}

/**
 * Generates plain-English narrative explanation of regex
 */
export function explainRegexPlainEnglish(regexStr) {
  if (!regexStr || !regexStr.trim()) {
    return 'Enter a regular expression to see its plain-English explanation.';
  }

  const trimmed = regexStr.trim();

  // Common pedagogical patterns
  if (trimmed === '(a|b)*abb') {
    return "Matches any string consisting of 'a' and 'b' that ends with the exact suffix 'abb'.";
  }
  if (trimmed === 'a*b+') {
    return "Matches zero or more 'a's followed by at least one 'b'.";
  }
  if (trimmed === 'a+b+') {
    return "Matches one or more 'a's followed by one or more 'b's.";
  }
  if (trimmed === '(01)*101') {
    return "Matches repeated alternating pairs of '01' followed by the sequence '101'.";
  }
  if (trimmed === '(a|b)*a(a|b)') {
    return "Matches strings of 'a' and 'b' where the second-to-last character is strictly 'a'.";
  }
  if (trimmed === '(1*01*0)*1*') {
    return "Matches binary strings containing an even number of '0's (with any number of '1's).";
  }
  if (trimmed === '(a+)+$' || trimmed === '(a+)+') {
    return "Matches strings of repeated 'a's grouped with nested plus quantifiers (exhibits exponential backtracking in backtracking engines).";
  }
  if (trimmed === 'a*a*b') {
    return "Matches repeated 'a's followed by 'b' using adjacent ambiguous Kleene stars (polynomial backtracking).";
  }

  // Generalized explanation builder
  const tokens = tokenizeRegex(trimmed);
  const parts = [];

  const hasStart = tokens.some((t) => t.type === 'anchor_start');
  const hasEnd = tokens.some((t) => t.type === 'anchor_end');

  if (hasStart && hasEnd) {
    parts.push('Matches strings that strictly span from start to end with:');
  } else if (hasStart) {
    parts.push('Matches strings beginning with:');
  } else if (hasEnd) {
    parts.push('Matches strings ending with:');
  } else {
    parts.push('Matches strings containing:');
  }

  const coreTokens = tokens.filter((t) => t.type !== 'anchor_start' && t.type !== 'anchor_end');
  const subexps = [];

  for (let i = 0; i < coreTokens.length; i++) {
    const t = coreTokens[i];
    if (t.type === 'alt') {
      subexps.push('or');
    } else if (t.type === 'literal') {
      subexps.push(`'${t.char}'`);
    } else if (t.type === 'star') {
      subexps.push('(repeated zero or more times)');
    } else if (t.type === 'plus') {
      subexps.push('(repeated one or more times)');
    } else if (t.type === 'optional') {
      subexps.push('(optional)');
    } else if (t.type === 'char_class') {
      subexps.push(`any character in ${t.char}`);
    } else if (t.type === 'group') {
      // Group boundary
    }
  }

  if (subexps.length > 0) {
    parts.push(subexps.slice(0, 8).join(' '));
    if (subexps.length > 8) parts.push('...');
  }

  return parts.join(' ');
}

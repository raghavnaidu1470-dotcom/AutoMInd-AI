/**
 * Syntax Validator & Error Parsing Utility
 * =========================================
 * Parses error messages from backend or local checks, extracts character positions,
 * and provides clear diagnostic tips on how to repair regular expression syntax.
 */

export function parseSyntaxError(errorMsg, regex = '') {
  if (!errorMsg || typeof errorMsg !== 'string') {
    return null;
  }

  const raw = errorMsg.replace(/^BACKEND ERROR:\s*/i, '').replace(/^Regex syntax error:\s*/i, '').trim();

  // Match "at position (\d+)"
  const posMatch = raw.match(/at position\s+(-?\d+)/i);
  let position = -1;
  let cleanMessage = raw;

  if (posMatch) {
    position = parseInt(posMatch[1], 10);
    cleanMessage = raw.replace(/\s+at position\s+-?\d+/i, '').trim();
  }

  // If position is -1 or beyond regex length, bound it
  if (position < 0 && regex.length > 0) {
    // Check if error message mentions unmatched parenthesis
    if (cleanMessage.includes("missing ')'") || cleanMessage.includes("Unbalanced parenthesis")) {
      position = regex.indexOf('(');
    } else if (cleanMessage.includes("Unexpected closing parenthesis")) {
      position = regex.indexOf(')');
    }
  }

  let tip = 'Check that your pattern syntax is balanced and uses valid operators.';

  if (cleanMessage.includes("missing ')'")) {
    tip = "Add a closing parenthesis ')' to match the opening '(' at position " + Math.max(0, position) + '.';
  } else if (cleanMessage.includes("Unexpected closing parenthesis")) {
    tip = "Remove this closing parenthesis ')' or add a matching '(' earlier in the pattern.";
  } else if (cleanMessage.includes("Empty alternation branch")) {
    tip = "Remove duplicate '|' or provide an expression on both sides of the alternation bar.";
  } else if (cleanMessage.includes("Multiple repeat operators")) {
    tip = "Remove the adjacent quantifier. You cannot follow a '*' with another repeat operator directly.";
  } else if (cleanMessage.includes("Dangling escape")) {
    tip = "Complete the escape sequence or remove the trailing backslash '\\'.";
  } else if (cleanMessage.includes("cannot be empty")) {
    tip = "Enter a valid regular expression, such as (a|b)*abb or a+b.";
  } else if (cleanMessage.includes("Unterminated character class")) {
    tip = "Add a closing bracket ']' to close the character set.";
  }

  return {
    message: cleanMessage,
    position: position >= 0 ? position : 0,
    hasExactPosition: position >= 0 && position < (regex ? regex.length : 1),
    tip,
  };
}

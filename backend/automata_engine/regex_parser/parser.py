r"""
Regex Parser & AST Construction
================================
Owned by: Member A (Automata Theory Engine)

This module receives a raw regular expression string and transforms it into
an Abstract Syntax Tree (AST) using a recursive-descent parser.

Precedence (lowest to highest):
  1. Alternation / Union `|`
  2. Concatenation (implicit, e.g. 'ab' -> 'a . b')
  3. Repetition / Unary Postfix operators: Kleene star `*`, Plus `+`, Optional `?`
  4. Atoms: Literals, Epsilon (`ε` or `()`), Escapes `\x`, Grouping `(...)`
"""

import string
from enum import Enum
from typing import Optional, List, Tuple, Set


class RegexSyntaxError(ValueError):
    """
    Exception raised when a regular expression contains a syntax error.
    Includes the specific error message and character position.
    """

    def __init__(self, message: str, position: int = -1):
        self.message = message
        self.position = position
        pos_str = f" at position {position}" if position >= 0 else ""
        super().__init__(f"{message}{pos_str}")


class RegexNodeType(str, Enum):
    """Types of nodes that can appear in a Regular Expression AST."""
    LITERAL = "LITERAL"              # Single character (e.g. 'a')
    EPSILON = "EPSILON"              # Empty string 'ε'
    CONCAT = "CONCAT"                # Binary concatenation (left . right)
    UNION = "UNION"                  # Binary alternation (left | right)
    STAR = "STAR"                    # Unary Kleene star (child*)
    PLUS = "PLUS"                    # Unary positive closure (child+)
    QUESTION = "QUESTION"            # Optional (child?)


class RegexNode:
    """
    Node in the Regular Expression AST.

    Attributes:
        type (RegexNodeType): The operation or terminal type.
        value (Optional[str]): Character value if type == LITERAL.
        left (Optional[RegexNode]): Left child node for binary ops.
        right (Optional[RegexNode]): Right child node for binary ops.
        child (Optional[RegexNode]): Child node for unary ops (*, +, ?).
    """

    def __init__(
        self,
        node_type: RegexNodeType,
        value: Optional[str] = None,
        left: Optional["RegexNode"] = None,
        right: Optional["RegexNode"] = None,
        child: Optional["RegexNode"] = None,
        source_span: Optional[Tuple[int, int]] = None,
        has_start_anchor: bool = False,
        has_end_anchor: bool = False,
    ):
        self.type = node_type
        self.value = value
        self.left = left
        self.right = right
        self.child = child
        self.source_span = source_span
        self.has_start_anchor = has_start_anchor
        self.has_end_anchor = has_end_anchor

    def __repr__(self) -> str:
        span_str = f", span={self.source_span}" if self.source_span is not None else ""
        if self.type == RegexNodeType.LITERAL:
            return f"Literal({self.value!r}{span_str})"
        if self.type == RegexNodeType.EPSILON:
            return f"Epsilon({span_str})"
        if self.type == RegexNodeType.STAR:
            return f"Star({self.child!r}{span_str})"
        if self.type == RegexNodeType.PLUS:
            return f"Plus({self.child!r}{span_str})"
        if self.type == RegexNodeType.QUESTION:
            return f"Question({self.child!r}{span_str})"
        if self.type == RegexNodeType.CONCAT:
            return f"Concat({self.left!r}, {self.right!r}{span_str})"
        if self.type == RegexNodeType.UNION:
            return f"Union({self.left!r}, {self.right!r}{span_str})"
        return f"Node({self.type.value}{span_str})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RegexNode):
            return False
        return (
            self.type == other.type
            and self.value == other.value
            and self.left == other.left
            and self.right == other.right
            and self.child == other.child
        )


class RegexParser:
    """
    Recursive-descent parser for regular expressions producing a RegexNode AST.
    """

    def __init__(self):
        self._pattern: str = ""
        self._pos: int = 0
        self._length: int = 0
        self._offset: int = 0
        self._bound_alphabet: Set[str] = set()

    def _extract_bound_alphabet(self, pattern: str) -> Set[str]:
        """Extracts character universe for wildcard '.' and negated classes."""
        explicit: Set[str] = set()
        special = set("()|*+?^$[]\\")
        i = 0
        while i < len(pattern):
            if pattern[i] == "\\" and i + 1 < len(pattern):
                i += 2
            elif pattern[i] not in special:
                explicit.add(pattern[i])
                i += 1
            else:
                i += 1
        base = set(string.ascii_lowercase[:6]) | {"0", "1", "_"}
        return explicit | base

    def _build_union_tree(self, chars: List[str], span: Optional[Tuple[int, int]] = None) -> RegexNode:
        """Constructs balanced binary union tree for character sets."""
        if not chars:
            return RegexNode(RegexNodeType.EPSILON, source_span=span)
        if len(chars) == 1:
            return RegexNode(RegexNodeType.LITERAL, value=chars[0], source_span=span)
        mid = len(chars) // 2
        left = self._build_union_tree(chars[:mid], span=span)
        right = self._build_union_tree(chars[mid:], span=span)
        return RegexNode(RegexNodeType.UNION, left=left, right=right, source_span=span)

    def _parse_character_class(self) -> RegexNode:
        open_pos = self._pos
        self._advance()  # consume '['
        if self._pos >= self._length:
            raise RegexSyntaxError("Unterminated character class '['", open_pos + self._offset)

        negated = False
        if self._peek() == "^":
            negated = True
            self._advance()

        chars: Set[str] = set()
        while self._pos < self._length and self._peek() != "]":
            c = self._advance()
            if c == "\\":
                if self._pos >= self._length:
                    raise RegexSyntaxError("Dangling escape inside character class", self._pos + self._offset)
                esc = self._advance()
                if esc == "d":
                    chars.update(str(d) for d in range(10))
                elif esc == "w":
                    chars.update(string.ascii_letters + string.digits + "_")
                elif esc == "s":
                    chars.add(" ")
                elif esc == "-":
                    chars.add("-")
                elif esc == "]":
                    chars.add("]")
                else:
                    chars.add(esc)
            elif self._peek() == "-" and self._pos + 1 < self._length and self._pattern[self._pos + 1] != "]":
                self._advance()  # consume '-'
                end_c = self._advance()
                if end_c == "\\":
                    if self._pos >= self._length:
                        raise RegexSyntaxError("Dangling escape inside character class", self._pos + self._offset)
                    end_c = self._advance()
                if ord(c) > ord(end_c):
                    raise RegexSyntaxError(f"Invalid character class range '{c}-{end_c}'", self._pos + self._offset)
                for code in range(ord(c), ord(end_c) + 1):
                    chars.add(chr(code))
            else:
                chars.add(c)

        if self._pos >= self._length or self._peek() != "]":
            raise RegexSyntaxError("Unterminated character class '['", open_pos + self._offset)

        self._advance()  # consume ']'
        span = (open_pos + self._offset, self._pos + self._offset)

        if negated:
            neg_universe = set(self._bound_alphabet) | set(string.ascii_lowercase) | set(string.digits) | {"_"}
            final_chars = sorted(list(neg_universe - chars))
            if not final_chars:
                final_chars = ["_"]
        else:
            final_chars = sorted(list(chars))

        return self._build_union_tree(final_chars, span=span)

    def parse(self, pattern: str) -> RegexNode:
        """
        Parses a regular expression pattern into an AST.
        Supports boundary anchors (^, $), character classes ([a-z], [^a]),
        escaped character shorthands (\\d, \\w, \\s), and dot (.) over bounded alphabet.

        Args:
            pattern (str): The regular expression pattern (e.g., "(a|b)*abb").

        Returns:
            RegexNode: Root of the parsed AST.

        Raises:
            RegexSyntaxError: If the pattern is malformed or uses unsupported syntax.
        """
        if pattern is None or len(pattern) == 0:
            raise RegexSyntaxError("Regex pattern cannot be empty.", 0)

        has_start = False
        has_end = False
        start_idx = 0
        end_idx = len(pattern)

        if pattern.startswith("^"):
            has_start = True
            start_idx = 1

        if pattern.endswith("$"):
            # Check not escaped \\$
            num_bs = 0
            k = len(pattern) - 2
            while k >= start_idx and pattern[k] == "\\":
                num_bs += 1
                k -= 1
            if num_bs % 2 == 0:
                has_end = True
                end_idx = len(pattern) - 1

        inner = pattern[start_idx:end_idx]
        if inner == "":
            root = RegexNode(
                RegexNodeType.EPSILON,
                source_span=(0, len(pattern)),
                has_start_anchor=has_start,
                has_end_anchor=has_end,
            )
            return root

        self._pattern = inner
        self._pos = 0
        self._length = len(inner)
        self._offset = start_idx
        self._bound_alphabet = self._extract_bound_alphabet(pattern)

        root = self._parse_expression()

        if self._pos < self._length:
            char = self._peek()
            if char == ")":
                raise RegexSyntaxError("Unexpected closing parenthesis ')'", self._pos + self._offset)
            raise RegexSyntaxError(f"Unexpected character '{char}'", self._pos + self._offset)

        root.has_start_anchor = has_start
        root.has_end_anchor = has_end
        root.source_span = (0, len(pattern))
        return root

    def _peek(self) -> Optional[str]:
        if self._pos < self._length:
            return self._pattern[self._pos]
        return None

    def _advance(self) -> str:
        ch = self._pattern[self._pos]
        self._pos += 1
        return ch

    def _parse_expression(self) -> RegexNode:
        """
        expression -> term ('|' term)*
        """
        if self._pos >= self._length:
            raise RegexSyntaxError("Unexpected end of pattern", self._pos)

        if self._peek() == "|":
            raise RegexSyntaxError("Empty alternation branch before '|'", self._pos)

        left = self._parse_term()

        while self._peek() == "|":
            pipe_pos = self._pos
            self._advance()  # consume '|'

            if self._pos >= self._length:
                raise RegexSyntaxError("Empty alternation branch after '|'", pipe_pos)
            if self._peek() == "|":
                raise RegexSyntaxError("Empty alternation branch between '||'", pipe_pos)
            if self._peek() == ")":
                raise RegexSyntaxError("Empty alternation branch before ')'", pipe_pos)

            right = self._parse_term()
            start_pos = left.source_span[0] if left.source_span is not None else 0
            end_pos = right.source_span[1] if right.source_span is not None else self._pos
            left = RegexNode(RegexNodeType.UNION, left=left, right=right, source_span=(start_pos, end_pos))

        return left

    def _parse_term(self) -> RegexNode:
        """
        term -> factor+
        Implicit concatenation of factors.
        """
        factors: List[RegexNode] = []

        while self._pos < self._length and self._peek() not in ("|", ")"):
            factor = self._parse_factor()
            factors.append(factor)

        if not factors:
            raise RegexSyntaxError("Expected expression or factor", self._pos)

        # Fold factors with CONCAT left-associatively
        result = factors[0]
        for next_factor in factors[1:]:
            start_pos = result.source_span[0] if result.source_span is not None else 0
            end_pos = next_factor.source_span[1] if next_factor.source_span is not None else self._pos
            result = RegexNode(RegexNodeType.CONCAT, left=result, right=next_factor, source_span=(start_pos, end_pos))
        return result

    def _parse_factor(self) -> RegexNode:
        """
        factor -> atom ('*' | '+' | '?')?
        """
        atom = self._parse_atom()

        if self._pos < self._length and self._peek() in ("*", "+", "?"):
            op = self._advance()
            if self._pos < self._length and self._peek() in ("*", "+", "?"):
                next_op = self._peek()
                raise RegexSyntaxError(f"Multiple repeat operators '{op}' and '{next_op}'", self._pos)
            start_pos = atom.source_span[0] if atom.source_span is not None else self._pos - 1
            span = (start_pos, self._pos)
            if op == "*":
                atom = RegexNode(RegexNodeType.STAR, child=atom, source_span=span)
            elif op == "+":
                atom = RegexNode(RegexNodeType.PLUS, child=atom, source_span=span)
            elif op == "?":
                atom = RegexNode(RegexNodeType.QUESTION, child=atom, source_span=span)

        return atom

    def _parse_atom(self) -> RegexNode:
        """
        atom -> '(' expression? ')' | '[' class ']' | '.' | '\\' char | 'ε' | literal
        """
        if self._pos >= self._length:
            raise RegexSyntaxError("Unexpected end of pattern", self._pos + self._offset)

        ch = self._peek()

        if ch in ("*", "+", "?"):
            raise RegexSyntaxError(f"Dangling operator '{ch}' with no preceding target", self._pos + self._offset)

        if ch == "|":
            raise RegexSyntaxError("Empty alternation branch before '|'", self._pos + self._offset)

        if ch == ")":
            raise RegexSyntaxError("Unexpected closing parenthesis ')'", self._pos + self._offset)

        if ch in ("^", "$"):
            raise RegexSyntaxError(
                f"Anchor '{ch}' is only supported at pattern boundaries (start/end).",
                self._pos + self._offset,
            )

        if ch == "[":
            return self._parse_character_class()

        if ch == ".":
            pos = self._pos
            self._advance()
            return self._build_union_tree(
                sorted(list(self._bound_alphabet)),
                span=(pos + self._offset, self._pos + self._offset),
            )

        if ch == "(":
            open_pos = self._pos
            self._advance()  # consume '('

            if self._pos >= self._length:
                raise RegexSyntaxError("Unbalanced parenthesis: missing ')'", open_pos + self._offset)

            if self._peek() == "?":
                raise RegexSyntaxError(
                    "Lookaround assertions and non-capturing groups '(?...)' are not supported in regular automata.",
                    open_pos + self._offset,
                )

            # Check for empty parentheses `()` -> Epsilon
            if self._peek() == ")":
                self._advance()  # consume ')'
                return RegexNode(RegexNodeType.EPSILON, source_span=(open_pos + self._offset, self._pos + self._offset))

            expr = self._parse_expression()

            if self._pos >= self._length or self._peek() != ")":
                raise RegexSyntaxError("Unbalanced parenthesis: missing ')'", open_pos + self._offset)

            self._advance()  # consume ')'
            expr.source_span = (open_pos + self._offset, self._pos + self._offset)
            return expr

        if ch == "\\":
            esc_pos = self._pos
            self._advance()  # consume '\'
            if self._pos >= self._length:
                raise RegexSyntaxError("Dangling escape character '\\' at end of pattern", esc_pos + self._offset)
            escaped_char = self._advance()
            span = (esc_pos + self._offset, self._pos + self._offset)

            if escaped_char in "123456789":
                raise RegexSyntaxError(
                    f"Backreferences '\\{escaped_char}' are not supported in regular automata.",
                    esc_pos + self._offset,
                )
            if escaped_char == "d":
                return self._build_union_tree([str(d) for d in range(10)], span=span)
            if escaped_char == "w":
                return self._build_union_tree(
                    sorted(list(string.ascii_letters + string.digits + "_")),
                    span=span,
                )
            if escaped_char == "s":
                return RegexNode(RegexNodeType.LITERAL, value=" ", source_span=span)

            return RegexNode(RegexNodeType.LITERAL, value=escaped_char, source_span=span)

        if ch == "ε":
            pos = self._pos
            self._advance()
            return RegexNode(RegexNodeType.EPSILON, source_span=(pos + self._offset, self._pos + self._offset))

        # Standard literal character
        pos = self._pos
        self._advance()
        return RegexNode(RegexNodeType.LITERAL, value=ch, source_span=(pos + self._offset, self._pos + self._offset))

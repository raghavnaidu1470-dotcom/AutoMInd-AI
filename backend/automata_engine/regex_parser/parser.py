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

from enum import Enum
from typing import Optional, List


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
    ):
        self.type = node_type
        self.value = value
        self.left = left
        self.right = right
        self.child = child

    def __repr__(self) -> str:
        if self.type == RegexNodeType.LITERAL:
            return f"Literal({self.value!r})"
        if self.type == RegexNodeType.EPSILON:
            return "Epsilon()"
        if self.type == RegexNodeType.STAR:
            return f"Star({self.child!r})"
        if self.type == RegexNodeType.PLUS:
            return f"Plus({self.child!r})"
        if self.type == RegexNodeType.QUESTION:
            return f"Question({self.child!r})"
        if self.type == RegexNodeType.CONCAT:
            return f"Concat({self.left!r}, {self.right!r})"
        if self.type == RegexNodeType.UNION:
            return f"Union({self.left!r}, {self.right!r})"
        return f"Node({self.type.value})"

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

    def parse(self, pattern: str) -> RegexNode:
        """
        Parses a regular expression pattern into an AST.

        Args:
            pattern (str): The regular expression pattern (e.g., "(a|b)*abb").

        Returns:
            RegexNode: Root of the parsed AST.

        Raises:
            RegexSyntaxError: If the pattern is malformed.
        """
        if pattern is None or len(pattern) == 0:
            raise RegexSyntaxError("Regex pattern cannot be empty.", 0)

        self._pattern = pattern
        self._pos = 0
        self._length = len(pattern)

        root = self._parse_expression()

        if self._pos < self._length:
            char = self._peek()
            if char == ")":
                raise RegexSyntaxError("Unexpected closing parenthesis ')'", self._pos)
            raise RegexSyntaxError(f"Unexpected character '{char}'", self._pos)

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
            left = RegexNode(RegexNodeType.UNION, left=left, right=right)

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
            result = RegexNode(RegexNodeType.CONCAT, left=result, right=next_factor)
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
            if op == "*":
                atom = RegexNode(RegexNodeType.STAR, child=atom)
            elif op == "+":
                atom = RegexNode(RegexNodeType.PLUS, child=atom)
            elif op == "?":
                atom = RegexNode(RegexNodeType.QUESTION, child=atom)

        return atom

    def _parse_atom(self) -> RegexNode:
        """
        atom -> '(' expression? ')' | '\' char | 'ε' | literal
        """
        if self._pos >= self._length:
            raise RegexSyntaxError("Unexpected end of pattern", self._pos)

        ch = self._peek()

        if ch in ("*", "+", "?"):
            raise RegexSyntaxError(f"Dangling operator '{ch}' with no preceding target", self._pos)

        if ch == "|":
            raise RegexSyntaxError("Empty alternation branch before '|'", self._pos)

        if ch == ")":
            raise RegexSyntaxError("Unexpected closing parenthesis ')'", self._pos)

        if ch == "(":
            open_pos = self._pos
            self._advance()  # consume '('

            if self._pos >= self._length:
                raise RegexSyntaxError("Unbalanced parenthesis: missing ')'", open_pos)

            # Check for empty parentheses `()` -> Epsilon
            if self._peek() == ")":
                self._advance()  # consume ')'
                return RegexNode(RegexNodeType.EPSILON)

            expr = self._parse_expression()

            if self._pos >= self._length or self._peek() != ")":
                raise RegexSyntaxError("Unbalanced parenthesis: missing ')'", open_pos)

            self._advance()  # consume ')'
            return expr

        if ch == "\\":
            esc_pos = self._pos
            self._advance()  # consume '\'
            if self._pos >= self._length:
                raise RegexSyntaxError("Dangling escape character '\\' at end of pattern", esc_pos)
            escaped_char = self._advance()
            return RegexNode(RegexNodeType.LITERAL, value=escaped_char)

        if ch == "ε":
            self._advance()
            return RegexNode(RegexNodeType.EPSILON)

        # Standard literal character
        self._advance()
        return RegexNode(RegexNodeType.LITERAL, value=ch)

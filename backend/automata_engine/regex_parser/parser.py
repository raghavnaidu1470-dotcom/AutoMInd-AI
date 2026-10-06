"""
Regex Parser & AST Construction
================================
Owned by: Member A (Automata Theory Engine)

Module Overview:
----------------
This module receives a raw regular expression string and transforms it into
an Abstract Syntax Tree (AST). The AST represents the hierarchical order of
operations according to formal regex precedence:
  1. Parentheses `(...)` (highest)
  2. Kleene star `*`
  3. Concatenation `.` (often implicit, e.g. 'ab' -> 'a.b')
  4. Alternation / Union `|` (lowest)

Expected Input:
---------------
  regex: str (e.g. "(a|b)*abb", "a(b|c)*", "01*|10*")

Expected Output:
----------------
  RegexNode (Root of the parsed AST)

Downstream Consumer:
--------------------
  Member A's `nfa_builder` (Thompson's construction traverses this AST).
"""

from enum import Enum
from typing import Optional, List


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
        if self.type == RegexNodeType.STAR:
            return f"Star({self.child!r})"
        if self.type == RegexNodeType.CONCAT:
            return f"Concat({self.left!r}, {self.right!r})"
        if self.type == RegexNodeType.UNION:
            return f"Union({self.left!r}, {self.right!r})"
        return f"Node({self.type.value})"


class RegexParser:
    """
    Parser for regular expressions.

    TODO (Member A):
      1. Preprocess string to insert explicit concatenation operators (e.g. "ab" -> "a.b").
      2. Convert infix regex to postfix (Shunting-yard algorithm) or implement recursive-descent parser.
      3. Construct the AST of RegexNode objects.
      4. Handle syntax validation and raise descriptive SyntaxError on malformed regexes.
    """

    def __init__(self):
        pass

    def parse(self, pattern: str) -> RegexNode:
        """
        Parses a regular expression string into an AST.

        Args:
            pattern (str): The regular expression pattern (e.g., "(a|b)*abb").

        Returns:
            RegexNode: Root of the parsed AST.

        Raises:
            NotImplementedError: Until Member A implements the parsing algorithm.
            ValueError: If pattern is empty or malformed.
        """
        if not pattern:
            raise ValueError("Regex pattern cannot be empty.")

        # --- PLACEHOLDER FOR MEMBER A ---
        # Implementation roadmap:
        # Step 1: Pre-process characters (insert explicit concat dots)
        # Step 2: Convert to Postfix via Shunting Yard
        # Step 3: Construct RegexNode tree from Postfix stack
        raise NotImplementedError(
            "RegexParser.parse() is assigned to Member A. "
            "Please implement lexical analysis and AST construction."
        )

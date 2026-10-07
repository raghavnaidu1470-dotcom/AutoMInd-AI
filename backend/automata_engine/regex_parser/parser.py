"""
Regex Parser
============
Converts a regular expression into an Abstract Syntax Tree (AST).

Supported operators:
    |   Union
    *   Kleene Star
    +   One or more
    ?   Zero or one
    ()  Grouping
    ε   Epsilon

Implicit concatenation is supported.

Examples:
    ab      -> a followed by b
    a|b     -> a or b
    a*      -> zero or more a's
    a+      -> one or more a's
    a?      -> zero or one a
    (ab)*   -> zero or more repetitions of ab
"""


from enum import Enum
from typing import Optional, List


class RegexNodeType(str, Enum):
    """Types of nodes that can appear in the regex AST."""

    LITERAL = "LITERAL"
    EPSILON = "EPSILON"
    CONCAT = "CONCAT"
    UNION = "UNION"
    STAR = "STAR"
    PLUS = "PLUS"
    QUESTION = "QUESTION"


class RegexNode:
    """A node in the regular-expression Abstract Syntax Tree."""

    def __init__(
        self,
        node_type: RegexNodeType,
        value: Optional[str] = None,
        left: Optional["RegexNode"] = None,
        right: Optional["RegexNode"] = None,
        child: Optional["RegexNode"] = None,
    ):
        self.node_type = node_type
        self.value = value
        self.left = left
        self.right = right
        self.child = child

    def __repr__(self):
        if self.node_type == RegexNodeType.LITERAL:
            return f"RegexNode(LITERAL, value={self.value!r})"

        if self.node_type == RegexNodeType.EPSILON:
            return "RegexNode(EPSILON)"

        if self.node_type in {
            RegexNodeType.STAR,
            RegexNodeType.PLUS,
            RegexNodeType.QUESTION,
        }:
            return f"RegexNode({self.node_type.value}, child={self.child!r})"

        return (
            f"RegexNode({self.node_type.value}, "
            f"left={self.left!r}, right={self.right!r})"
        )


class RegexParser:
    """
    Parses a regular expression and produces an AST.

    Supported syntax:

        a       literal
        ε       epsilon
        a|b     union
        ab      concatenation
        a*      Kleene star
        a+      one-or-more
        a?      optional
        (ab)    grouping
    """

    # Operator precedence.
    # Higher number = higher precedence.
    PRECEDENCE = {
        "|": 1,
        ".": 2,
        "*": 3,
        "+": 3,
        "?": 3,
    }

    BINARY_OPERATORS = {"|", "."}
    UNARY_OPERATORS = {"*", "+", "?"}

    def __init__(self):
        pass

    def parse(self, pattern: str) -> RegexNode:
        """
        Parse a regular expression into an AST.

        Args:
            pattern: Regular-expression string.

        Returns:
            RegexNode: Root node of the AST.

        Raises:
            SyntaxError: If the regular expression is invalid.
            ValueError: If the pattern is empty.
        """

        if pattern is None:
            raise ValueError("Regex pattern cannot be None.")

        pattern = pattern.strip()

        if not pattern:
            raise ValueError("Regex pattern cannot be empty.")

        # Step 1:
        # Insert explicit concatenation operators.
        tokens = self._tokenize(pattern)
        tokens = self._insert_concatenation(tokens)

        # Step 2:
        # Convert infix expression to postfix.
        postfix = self._to_postfix(tokens)

        # Step 3:
        # Build AST from postfix expression.
        return self._build_ast(postfix)

    # ------------------------------------------------------------------
    # TOKENIZATION
    # ------------------------------------------------------------------

    def _tokenize(self, pattern: str) -> List[str]:
        """
        Convert the input regex into individual tokens.

        Characters used as operators are kept as separate tokens.
        """

        tokens = []

        for char in pattern:
            if char.isspace():
                continue

            if char in {"(", ")", "|", "*", "+", "?", "ε"}:
                tokens.append(char)
            else:
                # Every other character is treated as a literal.
                tokens.append(char)

        return tokens

    # ------------------------------------------------------------------
    # CONCATENATION
    # ------------------------------------------------------------------

    def _is_operand_end(self, token: str) -> bool:
        """
        Returns True if a token can appear at the end of an expression
        or sub-expression.
        """

        return (
            token == ")"
            or token == "ε"
            or token not in {"(", "|", "*", "+", "?"}
        )

    def _is_operand_start(self, token: str) -> bool:
        """
        Returns True if a token can begin an expression or sub-expression.
        """

        return (
            token == "("
            or token == "ε"
            or token not in {")", "|", "*", "+", "?"}
        )

    def _insert_concatenation(self, tokens: List[str]) -> List[str]:
        """
        Insert explicit '.' operators wherever concatenation is implied.

        Example:

            ab      -> a . b
            a(b|c)  -> a . (b|c)
            (a|b)c  -> (a|b) . c
            a*b     -> a * . b
        """

        result = []

        for i, current in enumerate(tokens):
            result.append(current)

            if i == len(tokens) - 1:
                continue

            next_token = tokens[i + 1]

            if (
                self._is_operand_end(current)
                or current in self.UNARY_OPERATORS
            ) and self._is_operand_start(next_token):
                result.append(".")

        return result

    # ------------------------------------------------------------------
    # INFIX -> POSTFIX
    # ------------------------------------------------------------------

    def _to_postfix(self, tokens: List[str]) -> List[str]:
        """
        Convert the tokenized infix regex into postfix notation
        using the Shunting-yard algorithm.
        """

        output = []
        operator_stack = []

        previous = None

        for token in tokens:

            # ----------------------------------------------------------
            # Operand
            # ----------------------------------------------------------
            if self._is_literal(token) or token == "ε":
                output.append(token)

            # ----------------------------------------------------------
            # Opening parenthesis
            # ----------------------------------------------------------
            elif token == "(":
                operator_stack.append(token)

            # ----------------------------------------------------------
            # Closing parenthesis
            # ----------------------------------------------------------
            elif token == ")":

                if previous in {"|", "."}:
                    raise SyntaxError(
                        "Invalid regex: operator cannot appear "
                        "immediately before ')'."
                    )

                found_opening = False

                while operator_stack:
                    operator = operator_stack.pop()

                    if operator == "(":
                        found_opening = True
                        break

                    output.append(operator)

                if not found_opening:
                    raise SyntaxError(
                        "Invalid regex: unmatched closing parenthesis ')'."
                    )

            # ----------------------------------------------------------
            # Unary operators
            # ----------------------------------------------------------
            elif token in self.UNARY_OPERATORS:

                if previous is None:
                    raise SyntaxError(
                        f"Invalid regex: operator '{token}' "
                        "cannot appear at the beginning."
                    )

                if previous in {"|", ".", "("}:
                    raise SyntaxError(
                        f"Invalid regex: operator '{token}' "
                        "has no operand."
                    )

                # Unary operators directly apply to the previous operand.
                output.append(token)

            # ----------------------------------------------------------
            # Binary operators
            # ----------------------------------------------------------
            elif token in self.BINARY_OPERATORS:

                if previous is None:
                    raise SyntaxError(
                        f"Invalid regex: operator '{token}' "
                        "cannot appear at the beginning."
                    )

                if previous in {"|", ".", "("}:
                    raise SyntaxError(
                        f"Invalid regex: operator '{token}' "
                        "has no left operand."
                    )

                while (
                    operator_stack
                    and operator_stack[-1] != "("
                    and self.PRECEDENCE[operator_stack[-1]]
                    >= self.PRECEDENCE[token]
                ):
                    output.append(operator_stack.pop())

                operator_stack.append(token)

            else:
                raise SyntaxError(
                    f"Invalid regex token: {token!r}"
                )

            previous = token

        # Expression cannot end with a binary operator.
        if previous in {"|", "."}:
            raise SyntaxError(
                f"Invalid regex: expression cannot end with '{previous}'."
            )

        # Empty parentheses are invalid.
        if previous == "(":
            raise SyntaxError(
                "Invalid regex: empty parentheses '()' are not allowed."
            )

        while operator_stack:
            operator = operator_stack.pop()

            if operator == "(":
                raise SyntaxError(
                    "Invalid regex: unmatched opening parenthesis '('."
                )

            output.append(operator)

        return output

    # ------------------------------------------------------------------
    # AST CONSTRUCTION
    # ------------------------------------------------------------------

    def _build_ast(self, postfix: List[str]) -> RegexNode:
        """
        Construct an AST from postfix notation.
        """

        stack: List[RegexNode] = []

        for token in postfix:

            # ----------------------------------------------------------
            # Literal
            # ----------------------------------------------------------
            if self._is_literal(token):
                stack.append(
                    RegexNode(
                        RegexNodeType.LITERAL,
                        value=token,
                    )
                )

            # ----------------------------------------------------------
            # Epsilon
            # ----------------------------------------------------------
            elif token == "ε":
                stack.append(
                    RegexNode(
                        RegexNodeType.EPSILON
                    )
                )

            # ----------------------------------------------------------
            # Unary operators
            # ----------------------------------------------------------
            elif token in self.UNARY_OPERATORS:

                if not stack:
                    raise SyntaxError(
                        f"Invalid regex: operator '{token}' "
                        "has no operand."
                    )

                child = stack.pop()

                if token == "*":
                    node_type = RegexNodeType.STAR

                elif token == "+":
                    node_type = RegexNodeType.PLUS

                else:
                    node_type = RegexNodeType.QUESTION

                stack.append(
                    RegexNode(
                        node_type,
                        child=child,
                    )
                )

            # ----------------------------------------------------------
            # Binary operators
            # ----------------------------------------------------------
            elif token in self.BINARY_OPERATORS:

                if len(stack) < 2:
                    raise SyntaxError(
                        f"Invalid regex: operator '{token}' "
                        "does not have two operands."
                    )

                right = stack.pop()
                left = stack.pop()

                if token == "|":
                    node_type = RegexNodeType.UNION
                else:
                    node_type = RegexNodeType.CONCAT

                stack.append(
                    RegexNode(
                        node_type,
                        left=left,
                        right=right,
                    )
                )

            else:
                raise SyntaxError(
                    f"Unexpected token while building AST: {token!r}"
                )

        if len(stack) != 1:
            raise SyntaxError(
                "Invalid regex: could not construct a single AST."
            )

        return stack[0]

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _is_literal(self, token: str) -> bool:
        """
        Determine whether a token represents a literal character.
        """

        return token not in {
            "(",
            ")",
            "|",
            ".",
            "*",
            "+",
            "?",
            "ε",
        }
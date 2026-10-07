"""
Thompson NFA Builder
====================
Converts a regular-expression AST into an NFA using Thompson's construction.

Supported AST nodes:
    LITERAL
    EPSILON
    CONCAT
    UNION
    STAR
    PLUS
    QUESTION
"""

from typing import Optional, Tuple

from ..models import Automaton, State, Transition
from ..regex_parser.parser import RegexNode, RegexNodeType


class NFABuilder:
    """
    Builds an NFA from a regular-expression AST using
    Thompson's construction.
    """

    EPSILON = "ε"

    def __init__(self):
        self._state_counter = 0
        self._states = []
        self._transitions = []
        self._alphabet = set()

    # ------------------------------------------------------------------
    # STATE CREATION
    # ------------------------------------------------------------------

    def _reset(self):
        """Reset the builder so each build starts with fresh state IDs."""
        self._state_counter = 0
        self._states = []
        self._transitions = []
        self._alphabet = set()

    def _new_state_id(self) -> str:
        """Create a unique state ID."""
        state_id = f"s{self._state_counter}"
        self._state_counter += 1
        return state_id

    def _new_state(self) -> str:
        """Create a new state and return its ID."""
        state_id = self._new_state_id()

        self._states.append(
            State(
                id=state_id,
                label=state_id,
                is_start=False,
                is_accepting=False,
            )
        )

        return state_id

    def _add_transition(
        self,
        from_state: str,
        to_state: str,
        symbol: str,
    ):
        """Add a transition to the NFA."""

        self._transitions.append(
            Transition(
                from_state=from_state,
                to_state=to_state,
                symbol=symbol,
            )
        )

        if symbol != self.EPSILON:
            self._alphabet.add(symbol)

    # ------------------------------------------------------------------
    # THOMPSON CONSTRUCTION
    # ------------------------------------------------------------------

    def _build_fragment(
        self,
        node: RegexNode,
    ) -> Tuple[str, str]:
        """
        Recursively build an NFA fragment.

        Returns:
            (start_state, accept_state)
        """

        # --------------------------------------------------------------
        # LITERAL
        # --------------------------------------------------------------
        if node.node_type == RegexNodeType.LITERAL:

            start = self._new_state()
            accept = self._new_state()

            self._add_transition(
                start,
                accept,
                node.value,
            )

            return start, accept

        # --------------------------------------------------------------
        # EPSILON
        # --------------------------------------------------------------
        if node.node_type == RegexNodeType.EPSILON:

            start = self._new_state()
            accept = self._new_state()

            self._add_transition(
                start,
                accept,
                self.EPSILON,
            )

            return start, accept

        # --------------------------------------------------------------
        # CONCATENATION
        # --------------------------------------------------------------
        if node.node_type == RegexNodeType.CONCAT:

            if node.left is None or node.right is None:
                raise ValueError(
                    "CONCAT node must have both left and right children."
                )

            left_start, left_accept = self._build_fragment(node.left)
            right_start, right_accept = self._build_fragment(node.right)

            # Connect the two fragments using epsilon.
            self._add_transition(
                left_accept,
                right_start,
                self.EPSILON,
            )

            return left_start, right_accept

        # --------------------------------------------------------------
        # UNION
        # --------------------------------------------------------------
        if node.node_type == RegexNodeType.UNION:

            if node.left is None or node.right is None:
                raise ValueError(
                    "UNION node must have both left and right children."
                )

            start = self._new_state()
            accept = self._new_state()

            left_start, left_accept = self._build_fragment(node.left)
            right_start, right_accept = self._build_fragment(node.right)

            # Start can enter either branch.
            self._add_transition(
                start,
                left_start,
                self.EPSILON,
            )

            self._add_transition(
                start,
                right_start,
                self.EPSILON,
            )

            # Both branches can reach the common accept state.
            self._add_transition(
                left_accept,
                accept,
                self.EPSILON,
            )

            self._add_transition(
                right_accept,
                accept,
                self.EPSILON,
            )

            return start, accept

        # --------------------------------------------------------------
        # KLEENE STAR
        # --------------------------------------------------------------
        if node.node_type == RegexNodeType.STAR:

            if node.child is None:
                raise ValueError(
                    "STAR node must have a child."
                )

            start = self._new_state()
            accept = self._new_state()

            child_start, child_accept = self._build_fragment(node.child)

            # Empty string is allowed.
            self._add_transition(
                start,
                accept,
                self.EPSILON,
            )

            # Enter the repeated fragment.
            self._add_transition(
                start,
                child_start,
                self.EPSILON,
            )

            # Exit the fragment.
            self._add_transition(
                child_accept,
                accept,
                self.EPSILON,
            )

            # Repeat the fragment.
            self._add_transition(
                child_accept,
                child_start,
                self.EPSILON,
            )

            return start, accept

        # --------------------------------------------------------------
        # ONE OR MORE
        # --------------------------------------------------------------
        if node.node_type == RegexNodeType.PLUS:

            if node.child is None:
                raise ValueError(
                    "PLUS node must have a child."
                )

            start = self._new_state()
            accept = self._new_state()

            child_start, child_accept = self._build_fragment(node.child)

            # Must enter the child at least once.
            self._add_transition(
                start,
                child_start,
                self.EPSILON,
            )

            # Accept after one or more repetitions.
            self._add_transition(
                child_accept,
                accept,
                self.EPSILON,
            )

            # Allow additional repetitions.
            self._add_transition(
                child_accept,
                child_start,
                self.EPSILON,
            )

            return start, accept

        # --------------------------------------------------------------
        # ZERO OR ONE
        # --------------------------------------------------------------
        if node.node_type == RegexNodeType.QUESTION:

            if node.child is None:
                raise ValueError(
                    "QUESTION node must have a child."
                )

            start = self._new_state()
            accept = self._new_state()

            child_start, child_accept = self._build_fragment(node.child)

            # Skip the child completely.
            self._add_transition(
                start,
                accept,
                self.EPSILON,
            )

            # Or execute the child once.
            self._add_transition(
                start,
                child_start,
                self.EPSILON,
            )

            self._add_transition(
                child_accept,
                accept,
                self.EPSILON,
            )

            return start, accept

        raise ValueError(
            f"Unsupported regex node type: {node.node_type}"
        )

    # ------------------------------------------------------------------
    # PUBLIC BUILD METHOD
    # ------------------------------------------------------------------

    def build_from_ast(
        self,
        ast: RegexNode,
        regex: Optional[str] = None,
    ) -> Automaton:
        """
        Build an NFA from a regex AST.

        Args:
            ast: Root of the regex AST.
            regex: Original regex, used as metadata.

        Returns:
            Automaton with type='NFA'.
        """

        if ast is None:
            raise ValueError("AST cannot be None.")

        # Start fresh for every NFA.
        self._reset()

        start_state, accept_state = self._build_fragment(ast)

        # Mark start state.
        for state in self._states:
            if state.id == start_state:
                state.is_start = True

            if state.id == accept_state:
                state.is_accepting = True

        metadata = {
            "regex": regex,
            "state_count": len(self._states),
            "transition_count": len(self._transitions),
            "is_minimized": False,
            "description": "NFA generated using Thompson's construction.",
        }

        return Automaton(
            id="nfa",
            name="Thompson NFA",
            type="NFA",
            alphabet=sorted(self._alphabet),
            start_state=start_state,
            states=self._states,
            transitions=self._transitions,
            metadata=metadata,
        )
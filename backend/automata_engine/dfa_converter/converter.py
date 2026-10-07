"""
NFA -> DFA Converter
====================
Converts an NFA into a DFA using the subset/powerset construction.

Main steps:
    1. Compute epsilon-closure of the NFA start state.
    2. Treat that closure as the DFA start state.
    3. For every DFA state and input symbol:
         - move through matching NFA transitions
         - compute epsilon-closure
    4. Create a DFA state for every unique set of NFA states.
    5. A DFA state is accepting if it contains at least one
       accepting NFA state.
"""

from typing import Set, Dict, FrozenSet, List

from ..models import Automaton, State, Transition


class DFAConverter:
    """
    Converts an NFA into a DFA using subset construction.
    """

    EPSILON = "ε"

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # EPSILON CLOSURE
    # ------------------------------------------------------------------

    def epsilon_closure(
        self,
        nfa: Automaton,
        states: Set[str],
    ) -> Set[str]:
        """
        Find all states reachable from `states` using only epsilon
        transitions.

        Example:

            s0 --ε--> s1 --ε--> s2

        epsilon_closure({s0}) = {s0, s1, s2}
        """

        closure = set(states)
        stack = list(states)

        while stack:
            current = stack.pop()

            for transition in nfa.transitions:
                if (
                    transition.from_state == current
                    and transition.symbol in {self.EPSILON, ""}
                ):
                    target = transition.to_state

                    if target not in closure:
                        closure.add(target)
                        stack.append(target)

        return closure

    # ------------------------------------------------------------------
    # MOVE
    # ------------------------------------------------------------------

    def move(
        self,
        nfa: Automaton,
        states: Set[str],
        symbol: str,
    ) -> Set[str]:
        """
        Find all NFA states reachable from `states` using `symbol`.

        Epsilon transitions are not followed here.
        Epsilon closure is calculated separately.
        """

        result = set()

        for state in states:
            for transition in nfa.transitions:
                if (
                    transition.from_state == state
                    and transition.symbol == symbol
                ):
                    result.add(transition.to_state)

        return result

    # ------------------------------------------------------------------
    # DFA STATE ID
    # ------------------------------------------------------------------

    def _dfa_state_id(
        self,
        state_set: FrozenSet[str],
    ) -> str:
        """
        Generate a readable DFA state ID.

        Example:

            frozenset({"s0", "s1"}) -> "q0"
        """

        # The actual numbering is assigned in convert().
        return ""

    # ------------------------------------------------------------------
    # CONVERSION
    # ------------------------------------------------------------------

    def convert(self, nfa: Automaton) -> Automaton:
        """
        Convert an NFA into a DFA.

        Args:
            nfa: Automaton whose type must be "NFA".

        Returns:
            Automaton with type="DFA".

        Raises:
            ValueError: If the supplied automaton is not an NFA.
        """

        if nfa.type != "NFA":
            raise ValueError(
                "DFAConverter.convert() expects an automaton of type 'NFA'."
            )

        # --------------------------------------------------------------
        # Get NFA accepting states.
        # --------------------------------------------------------------

        accepting_states = {
            state.id
            for state in nfa.states
            if state.is_accepting
        }

        # --------------------------------------------------------------
        # Get alphabet.
        #
        # Epsilon is never part of the DFA alphabet.
        # --------------------------------------------------------------

        alphabet = sorted(
            symbol
            for symbol in nfa.alphabet
            if symbol not in {self.EPSILON, ""}
        )

        # --------------------------------------------------------------
        # Initial DFA state:
        #
        # epsilon-closure({NFA start state})
        # --------------------------------------------------------------

        start_closure = self.epsilon_closure(
            nfa,
            {nfa.start_state},
        )

        start_subset = frozenset(start_closure)

        # Map:
        #   set of NFA states -> DFA state ID
        subset_to_id: Dict[FrozenSet[str], str] = {
            start_subset: "q0"
        }

        # Store DFA subsets that still need processing.
        unprocessed: List[FrozenSet[str]] = [start_subset]

        dfa_states: List[State] = []
        dfa_transitions: List[Transition] = []

        # --------------------------------------------------------------
        # Create DFA start state.
        # --------------------------------------------------------------

        dfa_states.append(
            State(
                id="q0",
                label="q0",
                is_start=True,
                is_accepting=bool(
                    start_subset & accepting_states
                ),
                metadata={
                    "nfa_states": sorted(start_subset)
                },
            )
        )

        # --------------------------------------------------------------
        # Subset construction.
        # --------------------------------------------------------------

        while unprocessed:

            current_subset = unprocessed.pop(0)
            current_id = subset_to_id[current_subset]

            for symbol in alphabet:

                # Step 1:
                # Follow the current symbol.
                moved_states = self.move(
                    nfa,
                    set(current_subset),
                    symbol,
                )

                # If nothing can be reached, there is no transition.
                if not moved_states:
                    continue

                # Step 2:
                # Follow all epsilon transitions from the result.
                target_closure = self.epsilon_closure(
                    nfa,
                    moved_states,
                )

                target_subset = frozenset(target_closure)

                # ------------------------------------------------------
                # Create a new DFA state if this subset hasn't appeared.
                # ------------------------------------------------------

                if target_subset not in subset_to_id:

                    new_id = f"q{len(subset_to_id)}"

                    subset_to_id[target_subset] = new_id
                    unprocessed.append(target_subset)

                    dfa_states.append(
                        State(
                            id=new_id,
                            label=new_id,
                            is_start=False,
                            is_accepting=bool(
                                target_subset & accepting_states
                            ),
                            metadata={
                                "nfa_states": sorted(target_subset)
                            },
                        )
                    )

                target_id = subset_to_id[target_subset]

                # ------------------------------------------------------
                # Add DFA transition.
                # ------------------------------------------------------

                dfa_transitions.append(
                    Transition(
                        id=f"{current_id}_{symbol}_{target_id}",
                        from_state=current_id,
                        to_state=target_id,
                        symbol=symbol,
                    )
                )

        # --------------------------------------------------------------
        # Build final DFA.
        # --------------------------------------------------------------

        return Automaton(
            id="dfa",
            name="Subset Construction DFA",
            type="DFA",
            alphabet=alphabet,
            start_state="q0",
            states=dfa_states,
            transitions=dfa_transitions,
            metadata={
                "regex": (
                    nfa.metadata.regex
                    if nfa.metadata is not None
                    else None
                ),
                "state_count": len(dfa_states),
                "transition_count": len(dfa_transitions),
                "is_minimized": False,
                "description": (
                    "DFA generated using subset/powerset construction."
                ),
            },
        )
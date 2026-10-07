"""
DFA Minimizer
=============
Minimizes a DFA using partition refinement.

The implementation:
    1. Removes unreachable states.
    2. Separates accepting and non-accepting states.
    3. Refines partitions based on transition behavior.
    4. Merges equivalent states.
    5. Rebuilds the minimized DFA.
"""

from typing import List, Set, Dict, FrozenSet

from ..models import Automaton, State, Transition


class DFAMinimizer:
    """
    Minimizes deterministic finite automata using partition refinement.
    """

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # REACHABILITY
    # ------------------------------------------------------------------

    def _get_reachable_states(
        self,
        dfa: Automaton,
    ) -> Set[str]:
        """
        Find all states reachable from the DFA start state.
        """

        reachable = {dfa.start_state}
        stack = [dfa.start_state]

        while stack:
            current = stack.pop()

            for transition in dfa.transitions:
                if transition.from_state == current:
                    target = transition.to_state

                    if target not in reachable:
                        reachable.add(target)
                        stack.append(target)

        return reachable

    # ------------------------------------------------------------------
    # TRANSITION LOOKUP
    # ------------------------------------------------------------------

    def _get_target(
        self,
        dfa: Automaton,
        state: str,
        symbol: str,
    ):
        """
        Return the target state for a DFA transition.

        Returns None if no transition exists.
        """

        for transition in dfa.transitions:
            if (
                transition.from_state == state
                and transition.symbol == symbol
            ):
                return transition.to_state

        return None

    # ------------------------------------------------------------------
    # PARTITION REFINEMENT
    # ------------------------------------------------------------------

    def _refine_partitions(
        self,
        dfa: Automaton,
        partitions: List[Set[str]],
        alphabet: List[str],
    ) -> List[Set[str]]:
        """
        Refine partitions until equivalent states can no longer
        be separated.
        """

        changed = True

        while changed:
            changed = False

            # Map each state to the partition containing it.
            state_to_partition = {}

            for index, partition in enumerate(partitions):
                for state in partition:
                    state_to_partition[state] = index

            new_partitions = []

            for partition in partitions:

                groups: Dict[tuple, Set[str]] = {}

                for state in partition:

                    signature = []

                    for symbol in alphabet:
                        target = self._get_target(
                            dfa,
                            state,
                            symbol,
                        )

                        if target is None:
                            # Missing transitions go to an implicit
                            # dead/trap behavior.
                            signature.append(None)
                        else:
                            signature.append(
                                state_to_partition[target]
                            )

                    signature = tuple(signature)

                    if signature not in groups:
                        groups[signature] = set()

                    groups[signature].add(state)

                # If one old partition became multiple groups,
                # refinement occurred.
                if len(groups) > 1:
                    changed = True

                new_partitions.extend(groups.values())

            partitions = new_partitions

        return partitions

    # ------------------------------------------------------------------
    # MINIMIZATION
    # ------------------------------------------------------------------

    def minimize(self, dfa: Automaton) -> Automaton:
        """
        Minimize a DFA.

        Args:
            dfa: DFA to minimize.

        Returns:
            Minimized DFA.

        Raises:
            ValueError: If the automaton is not a DFA.
        """

        if dfa.type not in {"DFA", "MINIMIZED_DFA"}:
            raise ValueError(
                "DFAMinimizer.minimize() expects an automaton "
                "of type 'DFA' or 'MINIMIZED_DFA'."
            )

        # --------------------------------------------------------------
        # 1. Remove unreachable states.
        # --------------------------------------------------------------

        reachable = self._get_reachable_states(dfa)

        reachable_states = [
            state
            for state in dfa.states
            if state.id in reachable
        ]

        reachable_transitions = [
            transition
            for transition in dfa.transitions
            if (
                transition.from_state in reachable
                and transition.to_state in reachable
            )
        ]

        accepting = {
            state.id
            for state in reachable_states
            if state.is_accepting
        }

        non_accepting = {
            state.id
            for state in reachable_states
            if not state.is_accepting
        }

        alphabet = list(dfa.alphabet)

        # --------------------------------------------------------------
        # 2. Initial partition:
        #
        # accepting vs non-accepting.
        # --------------------------------------------------------------

        partitions: List[Set[str]] = []

        if accepting:
            partitions.append(accepting)

        if non_accepting:
            partitions.append(non_accepting)

        # --------------------------------------------------------------
        # 3. Refine partitions.
        # --------------------------------------------------------------

        reachable_dfa = Automaton(
            id=dfa.id,
            name=dfa.name,
            type="DFA",
            alphabet=alphabet,
            start_state=dfa.start_state,
            states=reachable_states,
            transitions=reachable_transitions,
            metadata=dfa.metadata,
        )

        partitions = self._refine_partitions(
            reachable_dfa,
            partitions,
            alphabet,
        )

        # --------------------------------------------------------------
        # 4. Give each equivalence class a new state ID.
        # --------------------------------------------------------------

        state_to_new_id: Dict[str, str] = {}

        # Put the partition containing the original start state first.
        start_partition = None

        for partition in partitions:
            if dfa.start_state in partition:
                start_partition = partition
                break

        ordered_partitions = []

        if start_partition is not None:
            ordered_partitions.append(start_partition)

        for partition in partitions:
            if partition is not start_partition:
                ordered_partitions.append(partition)

        for index, partition in enumerate(ordered_partitions):
            new_id = f"q{index}"

            for old_state in partition:
                state_to_new_id[old_state] = new_id

        # --------------------------------------------------------------
        # 5. Build minimized states.
        # --------------------------------------------------------------

        minimized_states: List[State] = []

        for index, partition in enumerate(ordered_partitions):

            new_id = f"q{index}"

            is_accepting = any(
                state in accepting
                for state in partition
            )

            minimized_states.append(
                State(
                    id=new_id,
                    label=new_id,
                    is_start=(
                        dfa.start_state in partition
                    ),
                    is_accepting=is_accepting,
                    metadata={
                        "merged_states": sorted(partition)
                    },
                )
            )

        # --------------------------------------------------------------
        # 6. Rebuild transitions.
        # --------------------------------------------------------------

        minimized_transitions: List[Transition] = []

        # Keep track of transitions already added.
        added = set()

        for partition in ordered_partitions:

            representative = next(iter(partition))

            from_state = state_to_new_id[representative]

            for symbol in alphabet:

                target = self._get_target(
                    reachable_dfa,
                    representative,
                    symbol,
                )

                if target is None:
                    continue

                to_state = state_to_new_id[target]

                transition_key = (
                    from_state,
                    to_state,
                    symbol,
                )

                if transition_key in added:
                    continue

                added.add(transition_key)

                minimized_transitions.append(
                    Transition(
                        id=(
                            f"{from_state}_"
                            f"{symbol}_"
                            f"{to_state}"
                        ),
                        from_state=from_state,
                        to_state=to_state,
                        symbol=symbol,
                    )
                )

        # --------------------------------------------------------------
        # 7. Build final minimized DFA.
        # --------------------------------------------------------------

        return Automaton(
            id="minimized_dfa",
            name="Minimized DFA",
            type="MINIMIZED_DFA",
            alphabet=alphabet,
            start_state=state_to_new_id[dfa.start_state],
            states=minimized_states,
            transitions=minimized_transitions,
            metadata={
                "regex": (
                    dfa.metadata.regex
                    if dfa.metadata is not None
                    else None
                ),
                "state_count": len(minimized_states),
                "transition_count": len(minimized_transitions),
                "is_minimized": True,
                "description": (
                    "DFA minimized using partition refinement."
                ),
            },
        )
"""
Subset Construction (NFA -> DFA Converter)
==========================================
Owned by: Member A (Automata Theory Engine)

This module implements the Subset Construction (Powerset Construction) algorithm.
It transforms an NFA into an equivalent Deterministic Finite Automaton (DFA) where:
  1. For every state and every alphabet symbol, there is exactly one transition.
  2. No epsilon (ε) transitions exist.
  3. Each DFA state corresponds to a subset of NFA states reachable via ε-closure.
  4. An explicit dead/trap state is added only when necessary to ensure the
     transition function is complete over the entire alphabet.
  5. State naming (q0, q1, ...) and transition ordering are strictly deterministic.
"""

from typing import Set, Dict, FrozenSet, List, Tuple, Optional
import uuid

from ..models import Automaton, State, Transition, AutomatonMetadata


class DFAConverter:
    """
    Converts an NFA to a DFA using Subset Construction.
    """

    def __init__(self):
        pass

    def convert(self, nfa: Automaton) -> Automaton:
        """
        Executes the subset construction algorithm on the input NFA.

        Args:
            nfa (Automaton): The source NFA to determinize.

        Returns:
            Automaton: An equivalent DFA conforming to docs/json_schema.md.

        Raises:
            ValueError: If input automaton is not an NFA.
        """
        if nfa.type != "NFA":
            raise ValueError(f"Expected automaton type 'NFA', but got '{nfa.type}'.")

        alphabet = sorted(list(set(nfa.alphabet)))
        accepting_nfa_states: Set[str] = {s.id for s in nfa.states if s.is_accepting}

        # Build adjacency structures
        epsilon_transitions: Dict[str, Set[str]] = {s.id: set() for s in nfa.states}
        symbol_transitions: Dict[Tuple[str, str], Set[str]] = {}

        for t in nfa.transitions:
            if t.symbol in ("ε", ""):
                epsilon_transitions.setdefault(t.from_state, set()).add(t.to_state)
            else:
                symbol_transitions.setdefault((t.from_state, t.symbol), set()).add(t.to_state)

        def epsilon_closure(states: FrozenSet[str]) -> FrozenSet[str]:
            closure = set(states)
            stack = list(states)
            while stack:
                curr = stack.pop()
                for nxt in epsilon_transitions.get(curr, set()):
                    if nxt not in closure:
                        closure.add(nxt)
                        stack.append(nxt)
            return frozenset(closure)

        def move(states: FrozenSet[str], symbol: str) -> FrozenSet[str]:
            targets: Set[str] = set()
            for s in states:
                targets.update(symbol_transitions.get((s, symbol), set()))
            return frozenset(targets)

        # 1. Initial DFA state: epsilon-closure of NFA start state
        start_closure = epsilon_closure(frozenset([nfa.start_state]))

        subset_to_id: Dict[FrozenSet[str], str] = {start_closure: "q0"}
        id_to_subset: Dict[str, FrozenSet[str]] = {"q0": start_closure}
        queue: List[FrozenSet[str]] = [start_closure]

        dfa_transitions: Dict[Tuple[str, str], str] = {}

        # 2. Explore reachable subsets in BFS order
        while queue:
            current_subset = queue.pop(0)
            current_id = subset_to_id[current_subset]

            for sym in alphabet:
                target_subset = epsilon_closure(move(current_subset, sym))
                if target_subset:
                    if target_subset not in subset_to_id:
                        new_id = f"q{len(subset_to_id)}"
                        subset_to_id[target_subset] = new_id
                        id_to_subset[new_id] = target_subset
                        queue.append(target_subset)
                    dfa_transitions[(current_id, sym)] = subset_to_id[target_subset]

        # 3. Handle explicit dead/trap state if needed
        # An explicit dead state is added if any (state, symbol) transition is missing,
        # ensuring the DFA is complete over its alphabet.
        needs_dead_state = False
        all_created_ids = list(id_to_subset.keys())

        for sid in all_created_ids:
            for sym in alphabet:
                if (sid, sym) not in dfa_transitions:
                    needs_dead_state = True
                    break
            if needs_dead_state:
                break

        if needs_dead_state:
            dead_id = f"q{len(id_to_subset)}"
            id_to_subset[dead_id] = frozenset()
            # The dead state self-loops on all symbols
            for sym in alphabet:
                dfa_transitions[(dead_id, sym)] = dead_id
            # Route all missing transitions to the dead state
            for sid in all_created_ids:
                for sym in alphabet:
                    if (sid, sym) not in dfa_transitions:
                        dfa_transitions[(sid, sym)] = dead_id

        # 4. Construct States in deterministic index order
        def _state_key(s_id: str):
            if s_id.startswith("q") and s_id[1:].isdigit():
                return int(s_id[1:])
            return s_id

        sorted_state_ids = sorted(id_to_subset.keys(), key=_state_key)
        states: List[State] = []

        for sid in sorted_state_ids:
            subset = id_to_subset[sid]
            is_accepting = any(s in accepting_nfa_states for s in subset)
            is_start = (sid == "q0")
            nfa_subset_list = sorted(list(subset), key=lambda x: (int(x[1:]) if x.startswith("q") and x[1:].isdigit() else x))
            states.append(
                State(
                    id=sid,
                    label=sid,
                    is_start=is_start,
                    is_accepting=is_accepting,
                    metadata={"nfa_subset": nfa_subset_list},
                )
            )

        # 5. Construct Transitions sorted deterministically
        def _trans_sort_key(item: Tuple[Tuple[str, str], str]):
            (u, sym), v = item
            u_idx = int(u[1:]) if u.startswith("q") and u[1:].isdigit() else u
            v_idx = int(v[1:]) if v.startswith("q") and v[1:].isdigit() else v
            return (u_idx, sym, v_idx)

        sorted_transitions = sorted(dfa_transitions.items(), key=_trans_sort_key)
        transitions: List[Transition] = [
            Transition(
                id=f"dt{idx}",
                from_state=u,
                to_state=v,
                symbol=sym,
            )
            for idx, ((u, sym), v) in enumerate(sorted_transitions)
        ]

        pattern_str = nfa.metadata.regex if nfa.metadata else ""

        metadata = AutomatonMetadata(
            regex=pattern_str,
            state_count=len(states),
            transition_count=len(transitions),
            is_minimized=False,
            description="Constructed using Subset Construction (Powerset) Algorithm",
        )

        return Automaton(
            id=f"dfa_{uuid.uuid4().hex[:8]}",
            name=f"DFA for {pattern_str}" if pattern_str else "DFA",
            type="DFA",
            alphabet=alphabet,
            start_state="q0",
            states=states,
            transitions=transitions,
            metadata=metadata,
        )

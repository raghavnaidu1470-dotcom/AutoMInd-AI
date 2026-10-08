"""
DFA Minimization (Hopcroft's Algorithm)
=======================================
Owned by: Member A (Automata Theory Engine)

This module implements DFA state minimization using Hopcroft's algorithm.
Given an arbitrary DFA, it computes the unique minimal DFA (up to isomorphism)
recognizing the exact same formal language.

Algorithmic Steps:
------------------
1. Reachability Filter: Remove unreachable states from start_state using BFS.
2. Initial Partition: P = { F, Q \\ F } (accepting and non-accepting states).
3. Hopcroft's Refinement: Iteratively split partition blocks using inverse transitions.
4. Canonical State Synthesis: Synthesize new states and order them canonically
   via BFS discovery from the minimal start state, producing deterministic state
   names (q0, q1, ...) and stable transition tables.
"""

from typing import List, Set, Dict, FrozenSet, Tuple, Optional
import uuid

from ..models import Automaton, State, Transition, AutomatonMetadata


class DFAMinimizer:
    """
    Minimizes a DFA using Hopcroft's algorithm with deterministic BFS state ordering.
    """

    def __init__(self):
        pass

    def minimize(self, dfa: Automaton) -> Automaton:
        """
        Executes DFA minimization on the input DFA.

        Args:
            dfa (Automaton): The unminimized or candidate DFA.

        Returns:
            Automaton: Minimized DFA conforming to docs/json_schema.md.

        Raises:
            ValueError: If input is not a DFA.
        """
        if dfa.type not in ("DFA", "MINIMIZED_DFA"):
            raise ValueError(f"Expected DFA for minimization, got '{dfa.type}'.")

        alphabet = sorted(list(set(dfa.alphabet)))
        state_dict: Dict[str, State] = {s.id: s for s in dfa.states}

        # 1. Reachability Filter: BFS from dfa.start_state
        reachable: Set[str] = set()
        queue: List[str] = [dfa.start_state]
        visited: Set[str] = {dfa.start_state}

        # Transition lookups for reachable analysis
        adj: Dict[str, Dict[str, str]] = {s.id: {} for s in dfa.states}
        for t in dfa.transitions:
            adj.setdefault(t.from_state, {})[t.symbol] = t.to_state

        while queue:
            curr = queue.pop(0)
            reachable.add(curr)
            for sym, nxt in adj.get(curr, {}).items():
                if nxt in state_dict and nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)

        if not reachable:
            # Degenerate case: no reachable states, keep start state
            reachable = {dfa.start_state}

        # 2. Build complete transition and inverse transition tables over reachable states
        delta: Dict[Tuple[str, str], str] = {}
        delta_inv: Dict[Tuple[str, str], Set[str]] = {}

        for t in dfa.transitions:
            if t.from_state in reachable and t.to_state in reachable:
                delta[(t.from_state, t.symbol)] = t.to_state
                delta_inv.setdefault((t.to_state, t.symbol), set()).add(t.from_state)

        # 3. Initial Partition P and Worklist W
        accepting: Set[str] = {sid for sid in reachable if state_dict[sid].is_accepting}
        non_accepting: Set[str] = reachable - accepting

        partition: List[FrozenSet[str]] = []
        if accepting:
            partition.append(frozenset(accepting))
        if non_accepting:
            partition.append(frozenset(non_accepting))

        if not partition:
            partition = [frozenset(reachable)]

        # Worklist: initialize with smaller of the two sets if both exist
        worklist: List[FrozenSet[str]] = []
        if len(partition) == 2:
            smaller = min(partition, key=len)
            worklist.append(smaller)
        else:
            worklist.append(partition[0])

        # 4. Hopcroft's Partition Refinement Loop
        while worklist:
            A = worklist.pop(0)

            for c in alphabet:
                # X = { s in reachable | delta(s, c) in A }
                X: Set[str] = set()
                for target_state in A:
                    X.update(delta_inv.get((target_state, c), set()))

                if not X:
                    continue

                X_frozen = frozenset(X)
                new_partition: List[FrozenSet[str]] = []

                for Y in partition:
                    Y1 = Y & X_frozen
                    Y2 = Y - X_frozen

                    if Y1 and Y2:
                        new_partition.append(Y1)
                        new_partition.append(Y2)

                        if Y in worklist:
                            worklist.remove(Y)
                            worklist.append(Y1)
                            worklist.append(Y2)
                        else:
                            if len(Y1) <= len(Y2):
                                worklist.append(Y1)
                            else:
                                worklist.append(Y2)
                    else:
                        new_partition.append(Y)

                partition = new_partition

        # 5. Canonical State Synthesis
        # Find start block containing dfa.start_state
        start_block: Optional[FrozenSet[str]] = None
        for block in partition:
            if dfa.start_state in block:
                start_block = block
                break

        if start_block is None:
            start_block = partition[0]

        # Order blocks using BFS starting from start_block for stable deterministic naming
        ordered_blocks: List[FrozenSet[str]] = [start_block]
        block_queue: List[FrozenSet[str]] = [start_block]
        discovered_blocks_set: Set[FrozenSet[str]] = {start_block}

        # Helper to find block containing a given state
        def find_block(state_id: str) -> FrozenSet[str]:
            for b in partition:
                if state_id in b:
                    return b
            return start_block

        while block_queue:
            curr_b = block_queue.pop(0)
            rep = next(iter(curr_b))

            for c in alphabet:
                target_state = delta.get((rep, c))
                if target_state:
                    target_b = find_block(target_state)
                    if target_b not in discovered_blocks_set:
                        discovered_blocks_set.add(target_b)
                        ordered_blocks.append(target_b)
                        block_queue.append(target_b)

        # Include any remaining partition blocks (if any disconnected components exist)
        for b in partition:
            if b not in discovered_blocks_set:
                ordered_blocks.append(b)

        # Map each block to deterministic state id: q0, q1, ...
        block_to_id: Dict[FrozenSet[str], str] = {
            b: f"q{idx}" for idx, b in enumerate(ordered_blocks)
        }

        # 6. Build Minimized States
        states: List[State] = []
        for b in ordered_blocks:
            sid = block_to_id[b]
            is_start = (b == start_block)
            is_accepting = any(state_dict[orig].is_accepting for orig in b)
            merged_nfa_subsets: List[str] = []
            for orig in b:
                orig_meta = state_dict[orig].metadata or {}
                merged_nfa_subsets.extend(orig_meta.get("nfa_subset", [orig]))

            # Sort and deduplicate metadata subsets
            def _sub_sort_key(s: str):
                if s.startswith("q") and s[1:].isdigit():
                    return int(s[1:])
                return s

            clean_subsets = sorted(list(set(merged_nfa_subsets)), key=_sub_sort_key)

            states.append(
                State(
                    id=sid,
                    label=sid,
                    is_start=is_start,
                    is_accepting=is_accepting,
                    metadata={"nfa_subset": clean_subsets, "merged_states": sorted(list(b), key=_sub_sort_key)},
                )
            )

        # 7. Build Minimized Transitions
        min_transitions_dict: Dict[Tuple[str, str], str] = {}
        for b in ordered_blocks:
            from_id = block_to_id[b]
            rep = next(iter(b))
            for c in alphabet:
                target_state = delta.get((rep, c))
                if target_state:
                    target_b = find_block(target_state)
                    to_id = block_to_id[target_b]
                    min_transitions_dict[(from_id, c)] = to_id

        def _trans_sort_key(item: Tuple[Tuple[str, str], str]):
            (u, sym), v = item
            u_idx = int(u[1:]) if u.startswith("q") and u[1:].isdigit() else u
            v_idx = int(v[1:]) if v.startswith("q") and v[1:].isdigit() else v
            return (u_idx, sym, v_idx)

        sorted_transitions = sorted(min_transitions_dict.items(), key=_trans_sort_key)
        transitions: List[Transition] = [
            Transition(
                id=f"mt{idx}",
                from_state=u,
                to_state=v,
                symbol=sym,
            )
            for idx, ((u, sym), v) in enumerate(sorted_transitions)
        ]

        pattern_str = dfa.metadata.regex if dfa.metadata else ""

        metadata = AutomatonMetadata(
            regex=pattern_str,
            state_count=len(states),
            transition_count=len(transitions),
            is_minimized=True,
            description="Constructed using Hopcroft's DFA Minimization Algorithm",
        )

        return Automaton(
            id=f"min_dfa_{uuid.uuid4().hex[:8]}",
            name=f"Minimized DFA for {pattern_str}" if pattern_str else "Minimized DFA",
            type="MINIMIZED_DFA",
            alphabet=alphabet,
            start_state="q0",
            states=states,
            transitions=transitions,
            metadata=metadata,
        )

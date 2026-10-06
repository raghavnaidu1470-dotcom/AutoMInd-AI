"""
Subset Construction (NFA -> DFA Converter)
==========================================
Owned by: Member A (Automata Theory Engine)

Module Overview:
----------------
This module implements the Subset Construction (Powerset Construction) algorithm.
It transforms an NFA (which may contain epsilon transitions and non-deterministic
branching) into an equivalent Deterministic Finite Automaton (DFA) where:
  1. For every state and every alphabet symbol, there is at most one transition.
  2. No epsilon (ε) transitions exist.
  3. Each DFA state corresponds to a subset of NFA states reachable via ε-closure.

Key Algorithmic Steps:
----------------------
1. Epsilon Closure: For a set of states S, `epsilon_closure(S)` computes all
   states reachable via zero or more ε transitions.
2. Initial State: Compute `epsilon_closure({nfa.start_state})`. This becomes
   the start state of the DFA.
3. Transition Computation: For each unprocessed DFA state (subset of NFA states)
   and for each alphabet symbol `a`:
     target_subset = epsilon_closure(move(current_subset, a))
4. Accepting States: Any DFA state containing at least one NFA accepting state
   becomes an accepting state in the DFA.

Expected Input:
---------------
  nfa: Automaton (type="NFA")

Expected Output:
----------------
  Automaton (type="DFA", conforming to docs/json_schema.md)
"""

from typing import Set, Dict, FrozenSet, List
from ..models import Automaton, State, Transition


class DFAConverter:
    """
    Converts an NFA to a DFA using Subset Construction.

    TODO (Member A):
      1. Implement `epsilon_closure(states: Set[str]) -> Set[str]`.
      2. Implement `move(states: Set[str], symbol: str) -> Set[str]`.
      3. Track visited subsets using `FrozenSet[str]` mapped to DFA state names (e.g. q0, q1, ...).
      4. Populate each DFA state's metadata with the list of underlying NFA states.
      5. Construct and return the `Automaton` object with type="DFA".
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
            NotImplementedError: Until Member A implements subset construction.
            ValueError: If input automaton is not an NFA.
        """
        if nfa.type != "NFA":
            raise ValueError(f"Expected automaton type 'NFA', but got '{nfa.type}'.")

        # --- PLACEHOLDER FOR MEMBER A ---
        # Implementation roadmap:
        # 1. epsilon_closure computation using BFS/DFS
        # 2. Queue-based subset exploration over alphabet symbols
        # 3. Mapping frozenset(subsets) -> dfa_state_id
        # 4. Marking accepting states and transitions
        raise NotImplementedError(
            "DFAConverter.convert() is assigned to Member A. "
            "Please implement the Subset Construction algorithm."
        )

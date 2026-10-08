"""
Automata String Simulator & Execution Trace Logger
===================================================
Owned by: Member A (Automata Theory Engine)

This module tests whether an input string belongs to the formal language
defined by an automaton (DFA or NFA). It simulates string consumption symbol
by symbol and captures an ordered execution trace of every step.

Supports:
  - Deterministic DFA simulation
  - Set-of-states NFA simulation with epsilon-closure
  - Empty string evaluation
  - Symbols outside the alphabet (early rejection with clear trace record)
  - Long input strings with fast transition lookup
"""

import time
from typing import List, Set, Dict, Tuple, Optional

from ..models import Automaton, SimulationResult, SimulationStep, Transition


def _state_sort_key(s_id: str):
    if s_id.startswith("q") and s_id[1:].isdigit():
        return int(s_id[1:])
    return s_id


class AutomataSimulator:
    """
    Simulates string execution over finite automata (DFA and NFA).
    """

    def __init__(self):
        pass

    def simulate(self, automaton: Automaton, input_string: str) -> SimulationResult:
        """
        Runs an input string on the given automaton and records the trace.

        Args:
            automaton (Automaton): The finite automaton (NFA, DFA, or MINIMIZED_DFA).
            input_string (str): Candidate string to validate.

        Returns:
            SimulationResult: Execution trace, final states, and acceptance verdict.
        """
        if automaton.type == "NFA":
            return self._simulate_nfa(automaton, input_string)
        return self._simulate_dfa(automaton, input_string)

    def _simulate_dfa(self, automaton: Automaton, input_string: str) -> SimulationResult:
        """Simulates candidate string execution on a DFA."""
        start_time = time.perf_counter()
        accepting_states: Set[str] = {s.id for s in automaton.states if s.is_accepting}

        # Build fast transition map: (from_state, symbol) -> Transition
        trans_map: Dict[Tuple[str, str], Transition] = {}
        for t in automaton.transitions:
            key = (t.from_state, t.symbol)
            if key not in trans_map:
                trans_map[key] = t

        steps: List[SimulationStep] = []
        current_state = automaton.start_state

        # Step 0: Initial state configuration
        steps.append(
            SimulationStep(
                step=0,
                current_states=[current_state],
                symbol_read=None,
                transition_taken=None,
                next_states=[current_state],
            )
        )

        # Empty string case
        if len(input_string) == 0:
            accepted = current_state in accepting_states
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
            return SimulationResult(
                automaton_id=automaton.id,
                input_string=input_string,
                accepted=accepted,
                final_states=[current_state],
                execution_time_ms=elapsed_ms,
                steps=steps,
            )

        rejected_early = False
        for idx, char in enumerate(input_string):
            key = (current_state, char)
            t_obj = trans_map.get(key)

            if t_obj is not None:
                next_state = t_obj.to_state
                step_record = SimulationStep(
                    step=idx + 1,
                    current_states=[current_state],
                    symbol_read=char,
                    transition_taken=t_obj,
                    next_states=[next_state],
                )
                steps.append(step_record)
                current_state = next_state
            else:
                # No transition on symbol (either dead end or symbol not in alphabet)
                step_record = SimulationStep(
                    step=idx + 1,
                    current_states=[current_state],
                    symbol_read=char,
                    transition_taken=None,
                    next_states=[],
                )
                steps.append(step_record)
                rejected_early = True
                break

        accepted = (not rejected_early) and (current_state in accepting_states)
        final_states = [] if rejected_early else [current_state]
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

        return SimulationResult(
            automaton_id=automaton.id,
            input_string=input_string,
            accepted=accepted,
            final_states=final_states,
            execution_time_ms=elapsed_ms,
            steps=steps,
        )

    def _simulate_nfa(self, automaton: Automaton, input_string: str) -> SimulationResult:
        """Simulates candidate string execution on an NFA using epsilon closures."""
        start_time = time.perf_counter()
        accepting_states: Set[str] = {s.id for s in automaton.states if s.is_accepting}

        # Build adjacency structures
        eps_adj: Dict[str, Set[str]] = {s.id: set() for s in automaton.states}
        sym_adj: Dict[Tuple[str, str], List[Transition]] = {}

        for t in automaton.transitions:
            if t.symbol in ("ε", ""):
                eps_adj.setdefault(t.from_state, set()).add(t.to_state)
            else:
                sym_adj.setdefault((t.from_state, t.symbol), []).append(t)

        def eps_closure(states: Set[str]) -> Set[str]:
            closure = set(states)
            stack = list(states)
            while stack:
                curr = stack.pop()
                for nxt in eps_adj.get(curr, set()):
                    if nxt not in closure:
                        closure.add(nxt)
                        stack.append(nxt)
            return closure

        current_set = eps_closure({automaton.start_state})
        sorted_current = sorted(list(current_set), key=_state_sort_key)
        steps: List[SimulationStep] = []

        # Step 0: Initial state configuration
        steps.append(
            SimulationStep(
                step=0,
                current_states=sorted_current,
                symbol_read=None,
                transition_taken=None,
                next_states=sorted_current,
            )
        )

        # Empty string case
        if len(input_string) == 0:
            accepted = any(s in accepting_states for s in current_set)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
            return SimulationResult(
                automaton_id=automaton.id,
                input_string=input_string,
                accepted=accepted,
                final_states=sorted_current,
                execution_time_ms=elapsed_ms,
                steps=steps,
            )

        rejected_early = False
        for idx, char in enumerate(input_string):
            matching_transitions: List[Transition] = []
            target_states: Set[str] = set()

            for s in current_set:
                matches = sym_adj.get((s, char), [])
                if matches:
                    matching_transitions.extend(matches)
                    for m in matches:
                        target_states.add(m.to_state)

            if matching_transitions:
                next_set = eps_closure(target_states)
                sorted_next = sorted(list(next_set), key=_state_sort_key)
                primary_transition = matching_transitions[0]

                step_record = SimulationStep(
                    step=idx + 1,
                    current_states=sorted_current,
                    symbol_read=char,
                    transition_taken=primary_transition,
                    next_states=sorted_next,
                )
                steps.append(step_record)
                current_set = next_set
                sorted_current = sorted_next

                if not current_set:
                    rejected_early = True
                    break
            else:
                # No transition possible on character
                step_record = SimulationStep(
                    step=idx + 1,
                    current_states=sorted_current,
                    symbol_read=char,
                    transition_taken=None,
                    next_states=[],
                )
                steps.append(step_record)
                current_set = set()
                sorted_current = []
                rejected_early = True
                break

        accepted = (not rejected_early) and any(s in accepting_states for s in current_set)
        final_states = sorted_current
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

        return SimulationResult(
            automaton_id=automaton.id,
            input_string=input_string,
            accepted=accepted,
            final_states=final_states,
            execution_time_ms=elapsed_ms,
            steps=steps,
        )

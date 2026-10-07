"""
Automata String Simulator & Execution Trace Logger
===================================================
Simulates input strings against DFAs and NFAs.

Features:
    - DFA simulation
    - NFA simulation
    - Epsilon-closure handling
    - Step-by-step execution trace
    - Acceptance/rejection result
    - Execution-time measurement
"""

import time
from typing import List, Optional, Set, Dict

from ..models import (
    Automaton,
    SimulationResult,
    SimulationStep,
    Transition,
)


class AutomataSimulator:
    """
    Simulates input strings over finite automata.

    Supports:
        - DFA
        - MINIMIZED_DFA
        - NFA
    """

    EPSILON = "ε"

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # EPSILON CLOSURE
    # ------------------------------------------------------------------

    def _epsilon_closure(
        self,
        automaton: Automaton,
        states: Set[str],
    ) -> Set[str]:
        """
        Find every state reachable using only epsilon transitions.
        """

        closure = set(states)
        stack = list(states)

        while stack:
            current = stack.pop()

            for transition in automaton.transitions:
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
    # TRANSITION LOOKUP
    # ------------------------------------------------------------------

    def _get_transitions(
        self,
        automaton: Automaton,
        states: Set[str],
        symbol: str,
    ) -> List[Transition]:
        """
        Find all transitions from the supplied states using `symbol`.
        """

        result = []

        for transition in automaton.transitions:
            if (
                transition.from_state in states
                and transition.symbol == symbol
            ):
                result.append(transition)

        return result

    # ------------------------------------------------------------------
    # ACCEPTING STATES
    # ------------------------------------------------------------------

    def _get_accepting_states(
        self,
        automaton: Automaton,
    ) -> Set[str]:
        """Return the IDs of all accepting states."""

        return {
            state.id
            for state in automaton.states
            if state.is_accepting
        }

    # ------------------------------------------------------------------
    # DFA SIMULATION
    # ------------------------------------------------------------------

    def _simulate_dfa(
        self,
        automaton: Automaton,
        input_string: str,
    ):
        """
        Simulate a DFA.

        Returns:
            final_states, steps, accepted
        """

        accepting_states = self._get_accepting_states(automaton)

        current_state = automaton.start_state

        steps: List[SimulationStep] = []

        # --------------------------------------------------------------
        # Initial step.
        # --------------------------------------------------------------

        steps.append(
            SimulationStep(
                step=0,
                current_states=[current_state],
                symbol_read=None,
                transition_taken=None,
                next_states=[current_state],
            )
        )

        # --------------------------------------------------------------
        # Read input one symbol at a time.
        # --------------------------------------------------------------

        for index, symbol in enumerate(input_string, start=1):

            transition_taken: Optional[Transition] = None
            next_state: Optional[str] = None

            for transition in automaton.transitions:
                if (
                    transition.from_state == current_state
                    and transition.symbol == symbol
                ):
                    transition_taken = transition
                    next_state = transition.to_state
                    break

            # ----------------------------------------------------------
            # No transition = rejected.
            # ----------------------------------------------------------

            if next_state is None:

                steps.append(
                    SimulationStep(
                        step=index,
                        current_states=[current_state],
                        symbol_read=symbol,
                        transition_taken=None,
                        next_states=[],
                    )
                )

                return (
                    [],
                    steps,
                    False,
                )

            # ----------------------------------------------------------
            # Normal DFA transition.
            # ----------------------------------------------------------

            steps.append(
                SimulationStep(
                    step=index,
                    current_states=[current_state],
                    symbol_read=symbol,
                    transition_taken=transition_taken,
                    next_states=[next_state],
                )
            )

            current_state = next_state

        accepted = current_state in accepting_states

        return (
            [current_state],
            steps,
            accepted,
        )

    # ------------------------------------------------------------------
    # NFA SIMULATION
    # ------------------------------------------------------------------

    def _simulate_nfa(
        self,
        automaton: Automaton,
        input_string: str,
    ):
        """
        Simulate an NFA using active-state sets and epsilon closure.

        Returns:
            final_states, steps, accepted
        """

        accepting_states = self._get_accepting_states(automaton)

        # --------------------------------------------------------------
        # Initial epsilon closure.
        # --------------------------------------------------------------

        active_states = self._epsilon_closure(
            automaton,
            {automaton.start_state},
        )

        steps: List[SimulationStep] = []

        # Initial state before reading input.
        steps.append(
            SimulationStep(
                step=0,
                current_states=sorted(active_states),
                symbol_read=None,
                transition_taken=None,
                next_states=sorted(active_states),
            )
        )

        # --------------------------------------------------------------
        # Process each input symbol.
        # --------------------------------------------------------------

        for index, symbol in enumerate(input_string, start=1):

            current_states = set(active_states)

            matching_transitions = self._get_transitions(
                automaton,
                current_states,
                symbol,
            )

            next_states = {
                transition.to_state
                for transition in matching_transitions
            }

            # ----------------------------------------------------------
            # After consuming the symbol, follow epsilon transitions.
            # ----------------------------------------------------------

            next_states = self._epsilon_closure(
                automaton,
                next_states,
            )

            # SimulationStep can contain one Transition object.
            #
            # For an NFA there may be multiple transitions because
            # several branches can execute simultaneously. We store
            # the first matching transition while next_states records
            # the complete resulting state set.
            transition_taken = (
                matching_transitions[0]
                if matching_transitions
                else None
            )

            steps.append(
                SimulationStep(
                    step=index,
                    current_states=sorted(current_states),
                    symbol_read=symbol,
                    transition_taken=transition_taken,
                    next_states=sorted(next_states),
                )
            )

            active_states = next_states

            # ----------------------------------------------------------
            # No active states means no branch can accept.
            # We can stop early.
            # ----------------------------------------------------------

            if not active_states:
                return (
                    [],
                    steps,
                    False,
                )

        accepted = bool(
            active_states & accepting_states
        )

        return (
            sorted(active_states),
            steps,
            accepted,
        )

    # ------------------------------------------------------------------
    # PUBLIC SIMULATION METHOD
    # ------------------------------------------------------------------

    def simulate(
        self,
        automaton: Automaton,
        input_string: str,
    ) -> SimulationResult:
        """
        Run an input string against an automaton.

        Args:
            automaton:
                Automaton of type NFA, DFA, or MINIMIZED_DFA.

            input_string:
                String to test.

        Returns:
            SimulationResult containing:
                - acceptance verdict
                - final states
                - execution trace
                - execution time

        Raises:
            ValueError:
                If the automaton type is unsupported.
        """

        if automaton.type not in {
            "NFA",
            "DFA",
            "MINIMIZED_DFA",
        }:
            raise ValueError(
                "AutomataSimulator supports only "
                "NFA, DFA, and MINIMIZED_DFA."
            )

        if input_string is None:
            raise ValueError(
                "input_string cannot be None."
            )

        # --------------------------------------------------------------
        # Start timer.
        # --------------------------------------------------------------

        start_time = time.perf_counter()

        # --------------------------------------------------------------
        # Choose simulation method.
        # --------------------------------------------------------------

        if automaton.type == "NFA":

            final_states, steps, accepted = self._simulate_nfa(
                automaton,
                input_string,
            )

        else:

            final_states, steps, accepted = self._simulate_dfa(
                automaton,
                input_string,
            )

        # --------------------------------------------------------------
        # Calculate execution time.
        # --------------------------------------------------------------

        execution_time_ms = (
            time.perf_counter() - start_time
        ) * 1000

        # --------------------------------------------------------------
        # Return canonical SimulationResult.
        # --------------------------------------------------------------

        return SimulationResult(
            automaton_id=automaton.id,
            input_string=input_string,
            accepted=accepted,
            final_states=final_states,
            execution_time_ms=execution_time_ms,
            steps=steps,
        )
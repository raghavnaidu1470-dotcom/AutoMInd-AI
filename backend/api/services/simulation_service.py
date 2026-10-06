"""
Simulation Orchestration Service
================================
Owned by: Member C (API, Visualization & Integration)

Coordinates candidate string execution against automata. Provides fallback
trace evaluation if Member A's simulator module is pending implementation.
"""

from typing import Dict, Any, Optional, List
import time

from backend.automata_engine.models import Automaton, SimulationResult, SimulationStep, Transition
from backend.automata_engine.simulator.simulator import AutomataSimulator


class SimulationService:
    """Service executing candidate strings on automata."""

    def __init__(self):
        self.simulator = AutomataSimulator()

    def run_simulation(self, automaton: Automaton, input_string: str) -> SimulationResult:
        """
        Runs input string on the automaton and produces a complete execution trace.
        """
        try:
            return self.simulator.simulate(automaton, input_string)
        except NotImplementedError:
            return self._fallback_simulate(automaton, input_string)

    def _fallback_simulate(self, automaton: Automaton, input_string: str) -> SimulationResult:
        """
        Deterministic simulation engine supporting DFAs with transition lookup.
        """
        start_time = time.time()
        start_state = automaton.start_state
        accepting_ids = {s.id for s in automaton.states if s.is_accepting}

        current_state = start_state
        steps: List[SimulationStep] = []

        # Step 0: Initial state
        steps.append(
            SimulationStep(
                step=0,
                current_states=[current_state],
                symbol_read=None,
                transition_taken=None,
                next_states=[current_state],
            )
        )

        for idx, char in enumerate(input_string):
            # Look for matching transition
            matching_trans = None
            for t in automaton.transitions:
                if t.from_state == current_state and t.symbol == char:
                    matching_trans = t
                    break

            if matching_trans:
                next_state = matching_trans.to_state
            else:
                # Dead state or no transition
                next_state = "trap"

            step_obj = SimulationStep(
                step=idx + 1,
                current_states=[current_state],
                symbol_read=char,
                transition_taken=matching_trans,
                next_states=[next_state],
            )
            steps.append(step_obj)
            current_state = next_state

        accepted = current_state in accepting_ids
        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return SimulationResult(
            automaton_id=automaton.id,
            input_string=input_string,
            accepted=accepted,
            final_states=[current_state],
            execution_time_ms=elapsed_ms,
            steps=steps,
        )

"""
Simulation Orchestration Service
================================
Owned by: Member C (API, Visualization & Integration) & Member A (Automata Engine)

Coordinates candidate string execution against finite automata (NFA, DFA, MINIMIZED_DFA)
using the real automata engine simulator.
"""

from typing import Dict, Any, Optional, List
import logging

from backend.automata_engine.models import Automaton, SimulationResult
from backend.automata_engine.simulator.simulator import AutomataSimulator

logger = logging.getLogger(__name__)

# Sensible guardrail for string length
MAX_INPUT_STRING_LENGTH = 5000


class SimulationService:
    """Service executing candidate strings on automata."""

    def __init__(self):
        self.simulator = AutomataSimulator()

    def run_simulation(self, automaton: Automaton, input_string: str) -> SimulationResult:
        """
        Runs input string on the automaton and produces a complete execution trace.

        Args:
            automaton: The automaton model (NFA, DFA, or MINIMIZED_DFA).
            input_string: The string to test.

        Returns:
            SimulationResult with step-by-step trace and acceptance flag.

        Raises:
            ValueError: If input string exceeds maximum length limit.
        """
        if len(input_string) > MAX_INPUT_STRING_LENGTH:
            raise ValueError(
                f"Input string length ({len(input_string)}) exceeds maximum limit of {MAX_INPUT_STRING_LENGTH} characters."
            )

        return self.simulator.simulate(automaton, input_string)

"""
AutoMind AI — Automata Engine
==============================
Owned and maintained by: Member A (Automata Theory Engine)

This package contains:
- `regex_parser`: Tokenizes and parses regular expressions into ASTs
- `nfa_builder`: Constructs NFAs using Thompson's construction
- `dfa_converter`: Converts NFAs to DFAs via subset construction
- `dfa_minimizer`: Minimizes DFAs using Hopcroft's / Myhill-Nerode algorithms
- `simulator`: Validates strings and logs execution traces
- `models`: Canonical Pydantic schemas for Automaton and SimulationResult
"""

from .models import Automaton, State, Transition, SimulationResult, SimulationStep

__all__ = [
    "Automaton",
    "State",
    "Transition",
    "SimulationResult",
    "SimulationStep",
]

"""
AutoMind AI — Automata Engine
==============================
Owned and maintained by: Member A (Automata Theory Engine)

This package contains:
- `regex_parser`: Tokenizes and parses regular expressions into ASTs
- `nfa_builder`: Constructs NFAs using Thompson's construction
- `dfa_converter`: Converts NFAs to DFAs via subset construction
- `dfa_minimizer`: Minimizes DFAs using Hopcroft's algorithm
- `simulator`: Validates strings and logs execution traces
- `engine`: Top-level facade exposing build_all(regex)
- `models`: Canonical Pydantic schemas for Automaton and SimulationResult
"""

from .models import Automaton, State, Transition, SimulationResult, SimulationStep, AutomatonMetadata
from .regex_parser.parser import RegexParser, RegexNode, RegexNodeType, RegexSyntaxError
from .nfa_builder.builder import NFABuilder
from .dfa_converter.converter import DFAConverter
from .dfa_minimizer.minimizer import DFAMinimizer
from .simulator.simulator import AutomataSimulator
from .engine import AutomataEngine, build_all

__all__ = [
    "Automaton",
    "State",
    "Transition",
    "SimulationResult",
    "SimulationStep",
    "AutomatonMetadata",
    "RegexParser",
    "RegexNode",
    "RegexNodeType",
    "RegexSyntaxError",
    "NFABuilder",
    "DFAConverter",
    "DFAMinimizer",
    "AutomataSimulator",
    "AutomataEngine",
    "build_all",
]

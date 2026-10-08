"""
Automata Engine Facade
======================
Owned by: Member A (Automata Theory Engine)

Provides the top-level orchestration facade `build_all(regex)` that consumes
a regular expression string and returns the complete bundle:
  - NFA (Thompson's Construction)
  - DFA (Subset Construction)
  - Minimized DFA (Hopcroft's Algorithm)
  - Alphabet symbols
"""

from typing import Dict, Any, List

from .models import Automaton
from .regex_parser.parser import RegexParser, RegexSyntaxError
from .nfa_builder.builder import NFABuilder
from .dfa_converter.converter import DFAConverter
from .dfa_minimizer.minimizer import DFAMinimizer
from .simulator.simulator import AutomataSimulator


class AutomataEngine:
    """
    Unified engine facade for regular expressions and finite automata.
    """

    def __init__(self):
        self.parser = RegexParser()
        self.nfa_builder = NFABuilder()
        self.dfa_converter = DFAConverter()
        self.dfa_minimizer = DFAMinimizer()
        self.simulator = AutomataSimulator()

    def build_all(self, regex: str) -> Dict[str, Any]:
        """
        Builds NFA, DFA, and Minimized DFA from a regular expression pattern.

        Args:
            regex (str): The input regular expression pattern.

        Returns:
            Dict containing:
              - 'nfa': Automaton
              - 'dfa': Automaton
              - 'minimized_dfa': Automaton
              - 'alphabet': List[str]
        """
        ast = self.parser.parse(regex)
        nfa = self.nfa_builder.build_from_ast(ast, regex_str=regex)
        dfa = self.dfa_converter.convert(nfa)
        minimized_dfa = self.dfa_minimizer.minimize(dfa)

        return {
            "nfa": nfa,
            "dfa": dfa,
            "minimized_dfa": minimized_dfa,
            "alphabet": dfa.alphabet,
        }


# Singleton engine instance for simple function-level calls
_DEFAULT_ENGINE = AutomataEngine()


def build_all(regex: str) -> Dict[str, Any]:
    """
    Top-level helper function to compile regex into all three automaton representations.

    Args:
        regex (str): Regular expression string.

    Returns:
        Dict with keys: 'nfa', 'dfa', 'minimized_dfa', 'alphabet'.
    """
    return _DEFAULT_ENGINE.build_all(regex)

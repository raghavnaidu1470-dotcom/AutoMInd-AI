"""
Automata Orchestration Service
==============================
Owned by: Member C (API, Visualization & Integration) & Member A (Automata Engine)

Coordinates regular expression parsing, NFA generation via Thompson's Construction,
DFA conversion via Subset Construction, and DFA minimization via Hopcroft's Algorithm.
"""

from typing import Dict, Any, Optional
import logging

from backend.automata_engine.models import Automaton
from backend.automata_engine.engine import AutomataEngine
from backend.automata_engine.regex_parser.parser import RegexSyntaxError

logger = logging.getLogger(__name__)

# Sensible security and resource guardrails
MAX_REGEX_LENGTH = 300
MAX_DFA_STATES = 1000


class AutomataService:
    """
    High-level service coordinating Regex parsing, NFA generation,
    DFA conversion, and DFA minimization using the real automata engine.
    """

    def __init__(self):
        self.engine = AutomataEngine()

    def process_regex(self, regex: str) -> Dict[str, Automaton]:
        """
        Processes a regular expression through the full automata pipeline:
        AST -> NFA -> DFA -> Minimized DFA.

        Args:
            regex (str): The regular expression pattern.

        Returns:
            Dict containing:
              - 'nfa': Automaton
              - 'dfa': Automaton
              - 'minimized_dfa': Automaton

        Raises:
            RegexSyntaxError: On syntax errors in the regular expression.
            ValueError: If input exceeds length limits or produced state counts.
        """
        if not regex or not regex.strip():
            raise RegexSyntaxError("Regex cannot be empty.", 0)

        cleaned_regex = regex.strip()
        if len(cleaned_regex) > MAX_REGEX_LENGTH:
            raise ValueError(
                f"Regular expression exceeds maximum allowed length of {MAX_REGEX_LENGTH} characters."
            )

        bundle = self.engine.build_all(cleaned_regex)

        dfa = bundle["dfa"]
        if len(dfa.states) > MAX_DFA_STATES:
            raise ValueError(
                f"Generated DFA has {len(dfa.states)} states, exceeding maximum limit of {MAX_DFA_STATES}."
            )

        return {
            "nfa": bundle["nfa"],
            "dfa": dfa,
            "minimized_dfa": bundle["minimized_dfa"],
        }

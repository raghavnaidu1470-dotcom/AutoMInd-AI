"""
Automata Orchestration Service
==============================
Owned by: Member C (API, Visualization & Integration)

Coordinates Member A's Automata Engine modules. Provides seamless mock
fallbacks so Member B (XAI) and Member C (Frontend) can develop and test
without waiting on Member A's core implementation.
"""

from typing import Dict, Any, Optional
import uuid
import logging

from backend.automata_engine.models import Automaton, State, Transition, AutomatonMetadata
from backend.automata_engine.regex_parser.parser import RegexParser
from backend.automata_engine.nfa_builder.builder import NFABuilder
from backend.automata_engine.dfa_converter.converter import DFAConverter
from backend.automata_engine.dfa_minimizer.minimizer import DFAMinimizer

logger = logging.getLogger(__name__)


class AutomataService:
    """
    High-level service coordinating Regex parsing, NFA generation,
    DFA conversion, and DFA minimization.
    """

    def __init__(self):
        self.parser = RegexParser()
        self.nfa_builder = NFABuilder()
        self.dfa_converter = DFAConverter()
        self.minimizer = DFAMinimizer()

    def process_regex(self, regex: str) -> Dict[str, Automaton]:
        """
        Processes a regular expression through the full pipeline:
        AST -> NFA -> DFA -> Minimized DFA.

        Returns:
            Dict containing:
              - 'nfa': Automaton
              - 'dfa': Automaton
              - 'minimized_dfa': Automaton
        """
        try:
            ast = self.parser.parse(regex)
            nfa = self.nfa_builder.build_from_ast(ast, regex)
            dfa = self.dfa_converter.convert(nfa)
            min_dfa = self.minimizer.minimize(dfa)
            return {
                "nfa": nfa,
                "dfa": dfa,
                "minimized_dfa": min_dfa,
            }
        except NotImplementedError as e:
            logger.info("Automata Engine placeholder intercepted (%s). Using mock generator fallback.", str(e))
            return self._generate_mock_pipeline_automata(regex)

    def _generate_mock_pipeline_automata(self, regex: str) -> Dict[str, Automaton]:
        """
        Generates realistic NFA, DFA, and Minimized DFA structures for development.
        """
        clean_regex = regex.strip() or "a*b"

        # Canonical DFA for (a|b)*abb
        if "abb" in clean_regex:
            return self._build_ends_with_abb_suite(clean_regex)

        # Default standard recognizer (e.g. a*b)
        return self._build_default_suite(clean_regex)

    def _build_ends_with_abb_suite(self, regex: str) -> Dict[str, Automaton]:
        """Mock suite for patterns ending in 'abb'."""
        nfa = Automaton(
            id="nfa_" + str(uuid.uuid4())[:8],
            name=f"NFA for {regex}",
            type="NFA",
            alphabet=["a", "b"],
            start_state="s0",
            states=[
                State(id="s0", label="s0", is_start=True, is_accepting=False),
                State(id="s1", label="s1", is_start=False, is_accepting=False),
                State(id="s2", label="s2", is_start=False, is_accepting=False),
                State(id="s3", label="s3", is_start=False, is_accepting=True),
            ],
            transitions=[
                Transition(id="nt1", from_state="s0", to_state="s0", symbol="a"),
                Transition(id="nt2", from_state="s0", to_state="s0", symbol="b"),
                Transition(id="nt3", from_state="s0", to_state="s1", symbol="a"),
                Transition(id="nt4", from_state="s1", to_state="s2", symbol="b"),
                Transition(id="nt5", from_state="s2", to_state="s3", symbol="b"),
            ],
            metadata=AutomatonMetadata(regex=regex, state_count=4, transition_count=5),
        )

        dfa = Automaton(
            id="dfa_" + str(uuid.uuid4())[:8],
            name=f"DFA for {regex}",
            type="DFA",
            alphabet=["a", "b"],
            start_state="q0",
            states=[
                State(id="q0", label="q0 (Start)", is_start=True, is_accepting=False),
                State(id="q1", label="q1 (Saw a)", is_start=False, is_accepting=False),
                State(id="q2", label="q2 (Saw ab)", is_start=False, is_accepting=False),
                State(id="q3", label="q3 (Saw abb)", is_start=False, is_accepting=True),
            ],
            transitions=[
                Transition(id="dt1", from_state="q0", to_state="q1", symbol="a"),
                Transition(id="dt2", from_state="q0", to_state="q0", symbol="b"),
                Transition(id="dt3", from_state="q1", to_state="q1", symbol="a"),
                Transition(id="dt4", from_state="q1", to_state="q2", symbol="b"),
                Transition(id="dt5", from_state="q2", to_state="q1", symbol="a"),
                Transition(id="dt6", from_state="q2", to_state="q3", symbol="b"),
                Transition(id="dt7", from_state="q3", to_state="q1", symbol="a"),
                Transition(id="dt8", from_state="q3", to_state="q0", symbol="b"),
            ],
            metadata=AutomatonMetadata(regex=regex, state_count=4, transition_count=8, is_minimized=True),
        )

        return {"nfa": nfa, "dfa": dfa, "minimized_dfa": dfa}

    def _build_default_suite(self, regex: str) -> Dict[str, Automaton]:
        """Default mock suite for general regex patterns."""
        dfa = Automaton(
            id="dfa_" + str(uuid.uuid4())[:8],
            name=f"DFA for {regex}",
            type="DFA",
            alphabet=["a", "b"],
            start_state="q0",
            states=[
                State(id="q0", label="q0", is_start=True, is_accepting=False),
                State(id="q1", label="q1", is_start=False, is_accepting=True),
                State(id="q_trap", label="q_trap", is_start=False, is_accepting=False),
            ],
            transitions=[
                Transition(id="t1", from_state="q0", to_state="q0", symbol="a"),
                Transition(id="t2", from_state="q0", to_state="q1", symbol="b"),
                Transition(id="t3", from_state="q1", to_state="q_trap", symbol="a"),
                Transition(id="t4", from_state="q1", to_state="q_trap", symbol="b"),
                Transition(id="t5", from_state="q_trap", to_state="q_trap", symbol="a"),
                Transition(id="t6", from_state="q_trap", to_state="q_trap", symbol="b"),
            ],
            metadata=AutomatonMetadata(regex=regex, state_count=3, transition_count=6, is_minimized=True),
        )

        nfa = Automaton(
            id="nfa_" + str(uuid.uuid4())[:8],
            name=f"NFA for {regex}",
            type="NFA",
            alphabet=["a", "b"],
            start_state="s0",
            states=[
                State(id="s0", label="s0", is_start=True, is_accepting=False),
                State(id="s1", label="s1", is_start=False, is_accepting=True),
            ],
            transitions=[
                Transition(id="nt1", from_state="s0", to_state="s0", symbol="a"),
                Transition(id="nt2", from_state="s0", to_state="s1", symbol="b"),
            ],
            metadata=AutomatonMetadata(regex=regex, state_count=2, transition_count=2),
        )

        return {"nfa": nfa, "dfa": dfa, "minimized_dfa": dfa}

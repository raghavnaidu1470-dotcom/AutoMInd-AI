"""
Unit Tests for DFA Minimizer (Hopcroft's Algorithm)
===================================================
Tests DFA state minimization, equivalence class merging, reachability, and idempotency.
"""

import pytest
from backend.automata_engine.regex_parser.parser import RegexParser
from backend.automata_engine.nfa_builder.builder import NFABuilder
from backend.automata_engine.dfa_converter.converter import DFAConverter
from backend.automata_engine.dfa_minimizer.minimizer import DFAMinimizer
from backend.automata_engine.models import Automaton, State, Transition


@pytest.fixture
def parser():
    return RegexParser()


@pytest.fixture
def nfa_builder():
    return NFABuilder()


@pytest.fixture
def converter():
    return DFAConverter()


@pytest.fixture
def minimizer():
    return DFAMinimizer()


def test_minimization_ends_with_abb(parser, nfa_builder, converter, minimizer):
    # (a|b)*abb subset construction generates 5 states; Hopcroft should minimize to 4 states
    ast = parser.parse("(a|b)*abb")
    nfa = nfa_builder.build_from_ast(ast, "(a|b)*abb")
    dfa = converter.convert(nfa)
    min_dfa = minimizer.minimize(dfa)

    assert min_dfa.type == "MINIMIZED_DFA"
    assert len(min_dfa.states) == 4
    assert len(dfa.states) >= 4
    assert min_dfa.start_state == "q0"
    assert min_dfa.metadata.is_minimized is True


def test_minimization_idempotency(parser, nfa_builder, converter, minimizer):
    # Minimizing a minimized DFA should yield the exact same state and transition counts
    ast = parser.parse("a(b|c)*d")
    nfa = nfa_builder.build_from_ast(ast, "a(b|c)*d")
    dfa = converter.convert(nfa)
    min1 = minimizer.minimize(dfa)
    min2 = minimizer.minimize(min1)

    assert len(min1.states) == len(min2.states)
    assert len(min1.transitions) == len(min2.transitions)
    s1 = [s.id for s in min1.states]
    s2 = [s.id for s in min2.states]
    assert s1 == s2


def test_minimizer_removes_unreachable_states(minimizer):
    # Manually create a DFA with an unreachable state
    dfa = Automaton(
        id="test_unreachable",
        type="DFA",
        alphabet=["a"],
        start_state="q0",
        states=[
            State(id="q0", is_start=True, is_accepting=False),
            State(id="q1", is_start=False, is_accepting=True),
            State(id="q_orphan", is_start=False, is_accepting=False),
        ],
        transitions=[
            Transition(from_state="q0", to_state="q1", symbol="a"),
            Transition(from_state="q1", to_state="q1", symbol="a"),
            Transition(from_state="q_orphan", to_state="q_orphan", symbol="a"),
        ],
    )

    min_dfa = minimizer.minimize(dfa)
    state_ids = [s.id for s in min_dfa.states]
    # Orphan state should be purged
    assert len(state_ids) <= 2
    assert "q_orphan" not in state_ids

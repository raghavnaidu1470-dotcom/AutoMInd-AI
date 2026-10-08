"""
Unit Tests for DFA Converter (Subset Construction)
==================================================
Tests NFA to DFA determinization, complete alphabet transitions, and deterministic naming.
"""

import pytest
from backend.automata_engine.regex_parser.parser import RegexParser
from backend.automata_engine.nfa_builder.builder import NFABuilder
from backend.automata_engine.dfa_converter.converter import DFAConverter


@pytest.fixture
def converter():
    return DFAConverter()


@pytest.fixture
def parser():
    return RegexParser()


@pytest.fixture
def nfa_builder():
    return NFABuilder()


def test_dfa_conversion_ends_with_abb(parser, nfa_builder, converter):
    ast = parser.parse("(a|b)*abb")
    nfa = nfa_builder.build_from_ast(ast, "(a|b)*abb")
    dfa = converter.convert(nfa)

    assert dfa.type == "DFA"
    assert dfa.start_state == "q0"
    assert set(dfa.alphabet) == {"a", "b"}

    # In a DFA, no epsilon transitions
    for t in dfa.transitions:
        assert t.symbol not in ("ε", "")

    # For each state and each symbol, exactly one transition exists
    for s in dfa.states:
        for sym in dfa.alphabet:
            matching = [t for t in dfa.transitions if t.from_state == s.id and t.symbol == sym]
            assert len(matching) == 1, f"State {s.id} does not have exactly 1 transition on {sym}"

    # Metadata nfa_subset populated on all states
    for s in dfa.states:
        assert "nfa_subset" in s.metadata
        assert isinstance(s.metadata["nfa_subset"], list)


def test_dfa_deterministic_output(parser, nfa_builder, converter):
    ast = parser.parse("a(b|c)*d")
    nfa = nfa_builder.build_from_ast(ast, "a(b|c)*d")
    dfa1 = converter.convert(nfa)
    dfa2 = converter.convert(nfa)

    s1 = [s.id for s in dfa1.states]
    s2 = [s.id for s in dfa2.states]
    assert s1 == s2

    t1 = [(t.from_state, t.symbol, t.to_state) for t in dfa1.transitions]
    t2 = [(t.from_state, t.symbol, t.to_state) for t in dfa2.transitions]
    assert t1 == t2


def test_dfa_dead_state_generation(parser, nfa_builder, converter):
    # Regex 'a' over alphabet with only 'a'
    ast = parser.parse("a")
    nfa = nfa_builder.build_from_ast(ast, "a")
    dfa = converter.convert(nfa)

    # State q0 -> 'a' -> q1 (accepting).
    # From q1, reading 'a' has no match in original NFA, so dead state is added to make DFA complete.
    states_count = len(dfa.states)
    assert states_count >= 2

    # Verify every state has an outgoing transition for 'a'
    for s in dfa.states:
        matching = [t for t in dfa.transitions if t.from_state == s.id and t.symbol == "a"]
        assert len(matching) == 1

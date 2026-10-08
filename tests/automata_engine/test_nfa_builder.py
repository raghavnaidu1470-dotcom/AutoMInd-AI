"""
Unit Tests for NFA Builder (Thompson's Construction)
===================================================
Tests NFA construction from ASTs, state naming, and Thompson invariants.
"""

import pytest
from backend.automata_engine.regex_parser.parser import RegexParser
from backend.automata_engine.nfa_builder.builder import NFABuilder


@pytest.fixture
def parser():
    return RegexParser()


@pytest.fixture
def builder():
    return NFABuilder()


def test_nfa_single_literal(parser, builder):
    ast = parser.parse("a")
    nfa = builder.build_from_ast(ast, "a")

    assert nfa.type == "NFA"
    assert nfa.start_state == "q0"
    assert len(nfa.states) == 2
    assert nfa.alphabet == ["a"]

    # Invariant: exactly one start and one accept state
    starts = [s for s in nfa.states if s.is_start]
    accepts = [s for s in nfa.states if s.is_accepting]
    assert len(starts) == 1
    assert len(accepts) == 1
    assert starts[0].id == "q0"
    assert accepts[0].id == "q1"


def test_nfa_concatenation(parser, builder):
    ast = parser.parse("ab")
    nfa = builder.build_from_ast(ast, "ab")

    assert nfa.start_state == "q0"
    assert nfa.alphabet == ["a", "b"]
    assert len(nfa.states) == 4

    starts = [s for s in nfa.states if s.is_start]
    accepts = [s for s in nfa.states if s.is_accepting]
    assert len(starts) == 1
    assert len(accepts) == 1


def test_nfa_union(parser, builder):
    ast = parser.parse("a|b")
    nfa = builder.build_from_ast(ast, "a|b")

    assert nfa.start_state == "q0"
    assert sorted(nfa.alphabet) == ["a", "b"]
    # Union introduces 2 outer states + 2*2 inner states = 6 states
    assert len(nfa.states) == 6

    # Verify transitions out of start state are epsilon
    start_transitions = [t for t in nfa.transitions if t.from_state == "q0"]
    assert len(start_transitions) == 2
    for t in start_transitions:
        assert t.symbol == "ε"


def test_nfa_kleene_star(parser, builder):
    ast = parser.parse("a*")
    nfa = builder.build_from_ast(ast, "a*")

    assert nfa.start_state == "q0"
    assert nfa.alphabet == ["a"]
    # Star introduces 2 outer states + 2 inner = 4 states
    assert len(nfa.states) == 4

    # Verify bypass epsilon transition from start to accept
    accept_id = [s.id for s in nfa.states if s.is_accepting][0]
    bypass = [t for t in nfa.transitions if t.from_state == "q0" and t.to_state == accept_id]
    assert len(bypass) == 1
    assert bypass[0].symbol == "ε"


def test_nfa_deterministic_state_order(parser, builder):
    ast = parser.parse("(a|b)*abb")
    nfa1 = builder.build_from_ast(ast, "(a|b)*abb")
    nfa2 = builder.build_from_ast(ast, "(a|b)*abb")

    # Verify deterministic naming q0, q1, ...
    state_ids1 = [s.id for s in nfa1.states]
    state_ids2 = [s.id for s in nfa2.states]
    assert state_ids1 == state_ids2
    assert state_ids1[0] == "q0"
    assert state_ids1[-1] == f"q{len(state_ids1) - 1}"

    # Verify transition list identity
    trans1 = [(t.from_state, t.symbol, t.to_state) for t in nfa1.transitions]
    trans2 = [(t.from_state, t.symbol, t.to_state) for t in nfa2.transitions]
    assert trans1 == trans2

"""
Unit Tests for ReDoS Guard Suggested Repair & Equivalence Verification (Part 6)
==============================================================================
Tests rule-based rewrites, minimized DFA equivalence verification,
repaired ambiguity linear classification, and rejection of unsupported features.
"""

import pytest
from backend.redos_guard.repair import (
    ReDoSRepairEngine,
    are_dfas_equivalent,
    check_unsupported_features,
)
from backend.automata_engine.engine import AutomataEngine


@pytest.fixture
def repair_engine():
    return ReDoSRepairEngine()


def test_repair_nested_plus(repair_engine):
    """Verify (a+)+ collapses to a+ with verified language equivalence."""
    res = repair_engine.repair("(a+)+")
    assert res.success is True
    assert res.repaired_regex == "a+"
    assert res.equivalence_verified is True
    assert "collapse_nested_plus" in res.repair_technique


def test_repair_nested_star(repair_engine):
    """Verify (a*)*b collapses to a*b with verified language equivalence."""
    res = repair_engine.repair("(a*)*b")
    assert res.success is True
    assert res.repaired_regex == "a*b"
    assert res.equivalence_verified is True
    assert "collapse_nested_star" in res.repair_technique


def test_repair_overlapping_alternation(repair_engine):
    """Verify (a|aa)+ collapses to a+ with verified language equivalence."""
    res = repair_engine.repair("(a|aa)+")
    assert res.success is True
    assert res.repaired_regex == "a+"
    assert res.equivalence_verified is True


def test_repair_chained_repetitions(repair_engine):
    """Verify a*a*b merges to a*b with verified language equivalence."""
    res = repair_engine.repair("a*a*b")
    assert res.success is True
    assert res.repaired_regex == "a*b"
    assert res.equivalence_verified is True


def test_dfa_equivalence_checker_detects_mismatch():
    """Verify are_dfas_equivalent rejects DFAs with different languages (e.g. a+ vs a*)."""
    engine = AutomataEngine()
    b1 = engine.build_all("a+")
    b2 = engine.build_all("a*")
    is_equiv, witness = are_dfas_equivalent(b1["minimized_dfa"], b2["minimized_dfa"])
    assert is_equiv is False
    assert "Languages differ" in witness


def test_dfa_equivalence_checker_accepts_equivalent_dfas():
    """Verify are_dfas_equivalent accepts genuinely equivalent DFAs."""
    engine = AutomataEngine()
    b1 = engine.build_all("(a+)+")
    b2 = engine.build_all("a+")
    is_equiv, witness = are_dfas_equivalent(b1["minimized_dfa"], b2["minimized_dfa"])
    assert is_equiv is True
    assert witness is None


def test_reject_backreferences(repair_engine):
    """Verify backreferences are rejected with a clear message."""
    res = repair_engine.repair(r"(a+)\1")
    assert res.success is False
    assert res.error is not None
    assert "Backreferences" in res.error


def test_reject_lookaheads_and_lookbehinds(repair_engine):
    """Verify lookaheads and lookbehinds are rejected with informative messages."""
    res1 = repair_engine.repair("(?=abc)a*")
    assert res1.success is False
    assert "Lookahead assertions are not supported" in res1.error

    res2 = repair_engine.repair("(?<=abc)a*")
    assert res2.success is False
    assert "Lookbehind assertions are not supported" in res2.error

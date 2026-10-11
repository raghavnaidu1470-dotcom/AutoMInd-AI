"""
Unit Tests for ReDoS Guard Exact Ambiguity Analyzer (Part 2)
===========================================================
Tests exact ambiguity classification (Linear, Polynomial, Exponential),
attack string synthesis, trimmed NFA analysis, and performance boundaries
(size limits and timeouts) based on Weber & Seidl (1991).
"""

import pytest
from backend.redos_guard.analyzer import (
    AmbiguityAnalyzer,
    AmbiguityRisk,
    AttackString,
    AmbiguityAnalysisResult,
)
from backend.automata_engine.models import Automaton, State, Transition, AutomatonMetadata


@pytest.fixture
def analyzer():
    return AmbiguityAnalyzer(max_states=500, timeout_sec=3.0)


def test_exponential_ambiguity_nested_plus(analyzer):
    """Test (a+)+ classic nested quantifier ReDoS pattern."""
    result = analyzer.analyze("(a+)+")
    assert result.risk_class == AmbiguityRisk.EXPONENTIAL
    assert result.is_vulnerable is True
    assert len(result.offending_states) > 0
    assert len(result.offending_transitions) > 0
    assert result.attack_string is not None
    assert result.attack_string.pump == "a"
    attack = result.attack_string.build(repeats=10)
    assert "aaaaaaaaaa" in attack
    assert "Exponential Ambiguity" in result.explanation


def test_exponential_ambiguity_overlapping_alternation(analyzer):
    """Test (a|aa)+ overlapping repetition pattern."""
    result = analyzer.analyze("(a|aa)+")
    assert result.risk_class == AmbiguityRisk.EXPONENTIAL
    assert result.is_vulnerable is True
    assert result.attack_string is not None
    assert "a" in result.attack_string.pump
    assert result.attack_string.suffix != ""


def test_exponential_ambiguity_nested_star(analyzer):
    """Test (a*)*b nested Kleene star pattern."""
    result = analyzer.analyze("(a*)*b")
    assert result.risk_class == AmbiguityRisk.EXPONENTIAL
    assert result.is_vulnerable is True
    assert result.attack_string is not None
    assert result.attack_string.pump == "a"


def test_polynomial_ambiguity_chained_stars(analyzer):
    """Test a*a*b chained overlapping star patterns (degree >= 2)."""
    result = analyzer.analyze("a*a*b")
    assert result.risk_class == AmbiguityRisk.POLYNOMIAL
    assert result.is_vulnerable is True
    assert result.degree is not None
    assert result.degree >= 2
    assert result.attack_string is not None
    assert result.attack_string.pump == "a"
    assert "Polynomial Ambiguity" in result.explanation


def test_linear_ambiguity_safe_patterns(analyzer):
    """Test unambiguous / deterministic / safe regular expressions."""
    safe_patterns = [
        "(a|b)*abb",
        "a*b+",
        "a(b|c)*d",
        "(0|1)*00",
        "hello",
    ]
    for pattern in safe_patterns:
        result = analyzer.analyze(pattern)
        assert result.risk_class == AmbiguityRisk.LINEAR, f"Failed for {pattern}: {result.explanation}"
        assert result.is_vulnerable is False
        assert result.attack_string is None


def test_attack_string_builder():
    """Test AttackString prefix + pump^k + suffix construction."""
    att = AttackString(prefix="head_", pump="repeat_", suffix="_tail")
    rendered = att.build(repeats=3)
    assert rendered == "head_repeat_repeat_repeat__tail"


def test_analyzer_size_limit():
    """Test that NFA exceeding max_states returns graceful linear classification with explanation."""
    strict_analyzer = AmbiguityAnalyzer(max_states=5)
    # Pattern with > 5 NFA states
    result = strict_analyzer.analyze("(a|b)*abb")
    assert result.risk_class == AmbiguityRisk.LINEAR
    assert "exceeds analyzer threshold" in result.explanation


def test_analyzer_empty_language(analyzer):
    """Test analyzer behavior on automaton with unreachable or empty accepting paths."""
    # Create an automaton with no accepting states
    nfa = Automaton(
        id="empty_nfa",
        type="NFA",
        states=[State(id="q0", is_start=True, is_accepting=False)],
        alphabet=["a"],
        transitions=[],
        start_state="q0",
    )
    res = analyzer.analyze(nfa)
    assert res.risk_class == AmbiguityRisk.LINEAR
    assert res.is_vulnerable is False

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


def test_polynomial_ambiguity_triple_product_criterion(analyzer):
    """
    Test triple-product condition for polynomial ambiguity:
    a*a*b and a*a*a*b must be classified as POLYNOMIAL.
    """
    for pat in ["a*a*b", "a*a*a*b"]:
        res = analyzer.analyze(pat)
        assert res.risk_class == AmbiguityRisk.POLYNOMIAL, f"Expected {pat} to be POLYNOMIAL, got {res.risk_class}"
        assert res.is_vulnerable is True
        assert res.degree is not None and res.degree >= 2
        assert res.attack_string is not None


def test_disjoint_alternations_must_not_be_polynomial(analyzer):
    """
    Verify that disjoint alternations with off-diagonal pair-graph cycles
    are NOT classified as polynomial because the triple condition fails:
    x(a+|a+)y, (a+|a+), and (a*|a*)c must be classified as LINEAR.
    """
    non_polynomial_patterns = [
        "x(a+|a+)y",
        "(a+|a+)",
        "(a*|a*)c",
    ]
    for pat in non_polynomial_patterns:
        res = analyzer.analyze(pat)
        assert res.risk_class == AmbiguityRisk.LINEAR, (
            f"Pattern '{pat}' must NOT be classified polynomial; got {res.risk_class.value}: {res.explanation}"
        )
        assert res.is_vulnerable is False



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


def test_realistic_patterns_with_classes_and_anchors(analyzer):
    """
    Test 5+ realistic simplified patterns using character classes and anchors.
    Verifies that safe anchored patterns are recognized as LINEAR,
    while genuinely ambiguous patterns with classes/anchors are correctly flagged.
    """
    realistic_safe = [
        r"^[a-z]+@[a-z]+\.[a-z]+$",    # Anchored email
        r"^\d\d\d-\d\d\d\d$",          # Anchored phone
        "^user_[a-zA-Z0-9]+$",         # Anchored identifier
        r"^[0-9]+(\.[0-9]+)?$",        # Anchored float
        "^https?://[a-z0-9]+$",        # Anchored URL
    ]
    for pat in realistic_safe:
        res = analyzer.analyze(pat)
        assert res.risk_class == AmbiguityRisk.LINEAR, f"Expected {pat} to be LINEAR, got {res.risk_class.value}"
        assert res.is_vulnerable is False
        assert res.has_start_anchor is True
        assert res.has_end_anchor is True

    # Ambiguous patterns containing character classes or boundary anchors
    exp_res = analyzer.analyze(r"([a-z]+)+$")
    assert exp_res.risk_class == AmbiguityRisk.EXPONENTIAL
    assert exp_res.has_end_anchor is True

    poly_res = analyzer.analyze(r"\d*\d*$")
    assert poly_res.risk_class == AmbiguityRisk.POLYNOMIAL
    assert poly_res.has_end_anchor is True


def test_superlinear_growth_validation_on_attack_strings(analyzer):
    """
    Validates attack strings by running real Python re and confirming
    super-linear execution time growth for exponential and polynomial patterns.
    """
    import re
    import time

    # Exponential test: (a+)+$
    res = analyzer.analyze(r"(a+)+$")
    assert res.risk_class == AmbiguityRisk.EXPONENTIAL
    assert res.attack_string is not None

    pump = res.attack_string.pump
    suffix = res.attack_string.suffix or "!"
    pat_re = re.compile(r"(a+)+$")

    # Time growth on increasing repeat counts
    t_short_start = time.perf_counter()
    pat_re.search(pump * 10 + suffix)
    t_short = time.perf_counter() - t_short_start

    t_long_start = time.perf_counter()
    pat_re.search(pump * 24 + suffix)
    t_long = time.perf_counter() - t_long_start

    # For (a+)+$, length 24 backtracks ~2^24 times, which is significantly slower than length 10
    assert t_long > t_short, f"Expected superlinear growth: t_long ({t_long:.4f}s) <= t_short ({t_short:.4f}s)"
    assert res.engine_nuance_note is not None
    assert "search" in res.engine_nuance_note

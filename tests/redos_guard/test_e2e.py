"""
End-to-End Integration Tests for ReDoS Guard (Part 9)
=====================================================
Validates complete lifecycle:
  Regex Input -> Exact Ambiguity Analysis -> GNNExplainer Localization
  -> Rule-Based Repair -> Minimized DFA Equivalence Verification.
"""

import pytest
from backend.redos_guard.analyzer import AmbiguityAnalyzer, AmbiguityRisk
from backend.redos_guard.explainer import ReDoSExplainer
from backend.redos_guard.repair import ReDoSRepairEngine
from backend.redos_guard.benchmark import run_empirical_benchmark


def test_full_pipeline_exponential_e2e():
    """
    End-to-end test on classic exponential ReDoS pattern (a+)+$:
      1. Exact Analyzer detects Exponential Ambiguity (EDA) and synthesizes attack.
      2. GNNExplainer localizes the offending AST character span.
      3. Repair Engine rewrites pattern to a+$.
      4. Minimized DFA isomorphism verifies 100% language equivalence.
      5. Repaired regex is confirmed Linear (safe).
    """
    analyzer = AmbiguityAnalyzer()
    explainer = ReDoSExplainer()
    repair_engine = ReDoSRepairEngine()

    pattern = "(a+)+$"

    # 1. Exact Analysis
    analysis = analyzer.analyze(pattern)
    assert analysis.risk_class == AmbiguityRisk.EXPONENTIAL
    assert analysis.is_vulnerable is True
    assert analysis.attack_string is not None
    attack = analysis.attack_string.build(repeats=10)
    assert "aaaaaaaaaa" in attack

    # 2. Explainable Localization
    explanation = explainer.explain(pattern)
    assert explanation.predicted_risk == "exponential"
    assert len(explanation.highlighted_spans) > 0
    span = explanation.highlighted_spans[0]
    assert span.start == 0
    assert span.end >= 5
    assert "(a+)+" in span.fragment
    assert "nested quantifier" in explanation.explanation.lower()

    # 3. Repair & Verification
    repair = repair_engine.repair(pattern)
    assert repair.success is True
    assert repair.repaired_regex == "a+$"
    assert repair.equivalence_verified is True

    # 4. Confirm repaired pattern is safe
    repaired_analysis = analyzer.analyze(repair.repaired_regex)
    assert repaired_analysis.risk_class == AmbiguityRisk.LINEAR
    assert repaired_analysis.is_vulnerable is False


def test_full_pipeline_polynomial_e2e():
    """
    End-to-end test on polynomial ReDoS pattern a*a*b:
      1. Exact Analyzer detects Polynomial Ambiguity (PDA).
      2. Repair Engine rewrites to a*b.
      3. Minimized DFA equivalence verified.
      4. Repaired regex confirmed Linear (safe).
    """
    analyzer = AmbiguityAnalyzer()
    repair_engine = ReDoSRepairEngine()

    pattern = "a*a*b"

    # 1. Exact Analysis
    analysis = analyzer.analyze(pattern)
    assert analysis.risk_class == AmbiguityRisk.POLYNOMIAL
    assert analysis.degree >= 2

    # 2. Repair & Verification
    repair = repair_engine.repair(pattern)
    assert repair.success is True
    assert repair.repaired_regex == "a*b"
    assert repair.equivalence_verified is True

    # 3. Confirm safe
    repaired_analysis = analyzer.analyze(repair.repaired_regex)
    assert repaired_analysis.risk_class == AmbiguityRisk.LINEAR


def test_full_pipeline_safe_regex_e2e():
    """End-to-end test on safe regex (a|b)*abb: confirmed linear, no repair needed."""
    analyzer = AmbiguityAnalyzer()
    repair_engine = ReDoSRepairEngine()

    pattern = "(a|b)*abb"
    analysis = analyzer.analyze(pattern)
    assert analysis.risk_class == AmbiguityRisk.LINEAR
    assert analysis.is_vulnerable is False

    repair = repair_engine.repair(pattern)
    assert repair.success is True
    assert repair.repaired_regex == pattern
    assert repair.equivalence_verified is True

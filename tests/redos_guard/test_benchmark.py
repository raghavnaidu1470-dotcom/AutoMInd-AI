"""
Unit Tests for ReDoS Guard Empirical Benchmark (Part 3)
======================================================
Tests sandboxed subprocess execution, timeout enforcement,
time-vs-length measurement, and curated validation suite.
"""

import pytest
from backend.redos_guard.analyzer import AmbiguityRisk
from backend.redos_guard.benchmark import (
    run_sandboxed_re,
    run_empirical_benchmark,
    validate_curated_suite,
)


def test_sandboxed_re_safe_execution():
    """Verify sandboxed subprocess evaluates safe regex promptly."""
    duration_ms, timed_out, err = run_sandboxed_re("(a|b)*abb", "ab" * 20 + "abb", timeout_sec=1.0)
    assert not timed_out
    assert err is None
    assert duration_ms >= 0.0
    assert duration_ms < 50.0


def test_sandboxed_re_timeout_enforcement():
    """Verify sandboxed subprocess safely enforces hard timeout on catastrophic backtracking."""
    # 28 'a's on (a+)+$ causes ~10 seconds of backtracking in Python re without timeout
    duration_ms, timed_out, err = run_sandboxed_re("(a+)+$", "a" * 28 + "!", timeout_sec=0.2)
    assert timed_out is True
    assert "timeout" in err.lower()
    assert duration_ms >= 190.0  # within range of 200ms


def test_empirical_benchmark_exponential_scaling():
    """Verify run_empirical_benchmark detects exponential scaling on (a+)+$."""
    res = run_empirical_benchmark("(a+)+$", repeats_list=[4, 8, 12, 16, 20, 24], timeout_per_run_sec=0.3)
    assert res.empirical_risk == AmbiguityRisk.EXPONENTIAL
    assert len(res.points) > 0
    assert res.points[-1].length > res.points[0].length


def test_empirical_benchmark_linear_scaling():
    """Verify run_empirical_benchmark detects linear scaling on safe regex."""
    res = run_empirical_benchmark("(a|b)*abb", repeats_list=[4, 8, 12, 16, 20], timeout_per_run_sec=0.3)
    assert res.empirical_risk == AmbiguityRisk.LINEAR
    assert not res.timed_out
    assert res.max_duration_ms < 50.0


def test_curated_validation_suite():
    """Verify curated validation suite runs and reports results including honest mismatches."""
    suite = validate_curated_suite()
    assert suite["total_cases"] == 7
    assert len(suite["results"]) == 7
    # Verify that at least (a+)+$ and safe regexes matched
    matched_patterns = [r["pattern"] for r in suite["results"] if r["match"]]
    assert "(a+)+$" in matched_patterns
    assert "(a|b)*abb" in matched_patterns
    assert "a*b+" in matched_patterns

    # Check that any mismatch is explicitly documented
    if suite["mismatches"]:
        mismatch_pats = [m["pattern"] for m in suite["mismatches"]]
        assert "^(([a-z])+.)+[A-Z]([a-z])+$" in mismatch_pats

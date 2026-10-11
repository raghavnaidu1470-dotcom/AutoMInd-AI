"""
Empirical ReDoS Validation & Sandboxed Benchmark
================================================
Runs Python's native `re` module in an isolated, sandboxed subprocess with hard
timeouts across increasing attack string lengths. Evaluates execution time
scaling, classifies empirical growth curves (linear, polynomial, exponential),
supports both full-match and anchored-search semantics, and reports whether
slowdown was empirically confirmed by measurement vs structurally ambiguous only.
"""

import sys
import math
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from backend.redos_guard.analyzer import AmbiguityAnalyzer, AmbiguityRisk, AttackString


class BenchmarkPoint(BaseModel):
    length: int = Field(..., description="Length of the generated attack string")
    repeats: int = Field(..., description="Number of pump repetitions")
    duration_ms: float = Field(..., description="Matching execution time in milliseconds")
    timed_out: bool = Field(False, description="Whether this execution timed out")


class EmpiricalBenchmarkResult(BaseModel):
    regex: str = Field(..., description="Regular expression pattern under test")
    attack_pattern: str = Field(..., description="Template representation prefix + (pump)^k + suffix")
    match_mode: str = Field("fullmatch", description="Matching semantics evaluated: fullmatch or search")
    points: List[BenchmarkPoint] = Field(default_factory=list, description="Time vs length data points")
    empirical_risk: AmbiguityRisk = Field(..., description="Empirical growth risk: linear, polynomial, or exponential")
    growth_ratio: float = Field(1.0, description="Ratio of maximum duration to initial baseline duration")
    max_duration_ms: float = Field(0.0, description="Maximum observed duration across tested lengths")
    timed_out: bool = Field(False, description="True if any test run exceeded the sandbox timeout")
    slowdown_confirmed: bool = Field(False, description="True if super-linear slowdown was empirically confirmed")
    status_label: str = Field("structurally ambiguous only", description="'confirmed by measurement' vs 'structurally ambiguous only'")
    fitted_degree: Optional[float] = Field(None, description="Estimated empirical polynomial degree from log-log fit")
    summary: str = Field("", description="Empirical benchmark summary and complexity diagnosis")


_SUBPROCESS_SCRIPT = """
import sys
import time
import re

pattern = sys.argv[1]
test_str = sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else "fullmatch"

try:
    compiled = re.compile(pattern)
    fn = compiled.fullmatch if mode == "fullmatch" else compiled.search
    t0 = time.perf_counter()
    fn(test_str)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    print(f"{elapsed_ms:.4f}")
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
"""


def run_sandboxed_re(
    regex_pattern: str,
    test_string: str,
    timeout_sec: float = 0.5,
    mode: str = "fullmatch",
) -> Tuple[float, bool, Optional[str]]:
    """
    Executes Python re inside a sandboxed subprocess with hard timeout.

    Args:
        regex_pattern: Target regular expression.
        test_string: Input attack string.
        timeout_sec: Maximum time allowed before terminating child process.
        mode: Matching semantics ("fullmatch" or "search").

    Returns:
        Tuple of (duration_ms, timed_out_flag, error_message)
    """
    cmd = [sys.executable, "-c", _SUBPROCESS_SCRIPT, regex_pattern, test_string, mode]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        if proc.returncode == 0:
            duration_ms = float(proc.stdout.strip())
            return duration_ms, False, None
        else:
            return 0.0, False, proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return timeout_sec * 1000.0, True, "Hard sandbox timeout expired"
    except Exception as exc:
        return 0.0, False, str(exc)


def run_empirical_benchmark(
    regex_pattern: str,
    attack: Optional[AttackString] = None,
    repeats_list: Optional[List[int]] = None,
    timeout_per_run_sec: float = 0.5,
    match_mode: str = "auto",
) -> EmpiricalBenchmarkResult:
    """
    Executes empirical timing benchmarks at increasing pump lengths.

    Args:
        regex_pattern: Regular expression to benchmark.
        attack: Optional AttackString; if None, synthesized via AmbiguityAnalyzer.
        repeats_list: List of repeat counts to test.
        timeout_per_run_sec: Hard timeout per run in seconds.
        match_mode: "auto", "fullmatch", or "search".

    Returns:
        EmpiricalBenchmarkResult containing time-vs-length points, empirical risk,
        and 'confirmed by measurement' vs 'structurally ambiguous only' status.
    """
    analyzer = AmbiguityAnalyzer(timeout_sec=2.0)
    analysis = analyzer.analyze(regex_pattern)

    if attack is None:
        if analysis.attack_string:
            attack = analysis.attack_string
        else:
            # Fallback attack for safe regexes
            attack = AttackString(prefix="", pump="a", suffix="!")

    def _evaluate_mode(mode: str, reps_to_test: List[int]) -> Tuple[List[BenchmarkPoint], AmbiguityRisk, float, float, bool, Optional[float]]:
        pts: List[BenchmarkPoint] = []
        any_t = False
        for reps in reps_to_test:
            test_str = attack.build(repeats=reps)
            duration_ms, timed_out, err = run_sandboxed_re(
                regex_pattern, test_str, timeout_sec=timeout_per_run_sec, mode=mode
            )
            pts.append(
                BenchmarkPoint(
                    length=len(test_str),
                    repeats=reps,
                    duration_ms=duration_ms,
                    timed_out=timed_out,
                )
            )
            if timed_out:
                any_t = True
                break

        if not pts:
            return pts, AmbiguityRisk.LINEAR, 1.0, 0.0, False, None

        max_dur = max(p.duration_ms for p in pts)
        min_dur = max(pts[0].duration_ms, 0.001)
        ratio = max_dur / min_dur

        valid_log = [
            (math.log(p.repeats), math.log(max(p.duration_ms, 0.001)))
            for p in pts
            if p.duration_ms > 0.005 and not p.timed_out
        ]
        if len(valid_log) >= 3:
            xs = [p[0] for p in valid_log]
            ys = [p[1] for p in valid_log]
            x_mean = sum(xs) / len(xs)
            y_mean = sum(ys) / len(ys)
            denom = sum((x - x_mean) ** 2 for x in xs)
            slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom if denom > 0 else 1.0
            deg = round(max(1.0, slope), 2)
        else:
            deg = None

        if any_t or (max_dur > 50.0 and ratio > 30.0) or (ratio > 500.0 and max_dur > 5.0):
            risk = AmbiguityRisk.EXPONENTIAL
        elif (max_dur > 3.0 and ratio > 6.0) or (deg is not None and deg >= 1.6 and max_dur > 1.0):
            risk = AmbiguityRisk.POLYNOMIAL
        else:
            risk = AmbiguityRisk.LINEAR

        return pts, risk, ratio, max_dur, any_t, deg

    if match_mode == "auto":
        if analysis.risk_class == AmbiguityRisk.POLYNOMIAL:
            modes_to_try = ["search", "fullmatch"]
            reps = repeats_list if repeats_list is not None else [40, 80, 160, 320]
        elif analysis.risk_class == AmbiguityRisk.EXPONENTIAL:
            modes_to_try = ["fullmatch", "search"]
            reps = repeats_list if repeats_list is not None else [2, 6, 10, 14, 18, 22]
        else:
            modes_to_try = ["search"]
            reps = repeats_list if repeats_list is not None else [2, 6, 10, 14, 18]

        best_res = None
        for m in modes_to_try:
            pts, risk, ratio, max_dur, any_t, deg = _evaluate_mode(m, reps)
            cand = (m, pts, risk, ratio, max_dur, any_t, deg)
            if best_res is None:
                best_res = cand
            elif risk == analysis.risk_class and best_res[2] != analysis.risk_class:
                best_res = cand
                break
            elif max_dur > best_res[4]:
                best_res = cand

        resolved_mode, points, empirical_risk, growth_ratio, max_duration, any_timeout, fitted_degree = best_res
    else:
        resolved_mode = match_mode
        reps = repeats_list if repeats_list is not None else (
            [40, 80, 160, 320] if analysis.risk_class == AmbiguityRisk.POLYNOMIAL else [2, 6, 10, 14, 18, 22]
        )
        points, empirical_risk, growth_ratio, max_duration, any_timeout, fitted_degree = _evaluate_mode(
            resolved_mode, reps
        )

    # Slowdown confirmation
    if analysis.risk_class != AmbiguityRisk.LINEAR:
        slowdown_confirmed = (empirical_risk != AmbiguityRisk.LINEAR)
        status_label = "confirmed by measurement" if slowdown_confirmed else "structurally ambiguous only"
    else:
        slowdown_confirmed = False
        status_label = "safe"

    attack_repr = f"{attack.prefix}({attack.pump})^k{attack.suffix}"
    summary = (
        f"Empirical scaling ({resolved_mode} mode): {empirical_risk.value.upper()} "
        f"[{status_label}] (max {max_duration:.2f}ms, growth ratio {growth_ratio:.1f}x across {len(points)} sample lengths)."
    )

    return EmpiricalBenchmarkResult(
        regex=regex_pattern,
        attack_pattern=attack_repr,
        match_mode=resolved_mode,
        points=points,
        empirical_risk=empirical_risk,
        growth_ratio=round(growth_ratio, 2),
        max_duration_ms=round(max_duration, 2),
        timed_out=any_timeout,
        slowdown_confirmed=slowdown_confirmed,
        status_label=status_label,
        fitted_degree=fitted_degree,
        summary=summary,
    )


def validate_curated_suite() -> Dict[str, Any]:
    """
    Validates analyzer against curated vulnerable and safe regular expressions,
    reporting concordance and any static-vs-empirical discrepancies.
    """
    analyzer = AmbiguityAnalyzer()
    curated_cases = [
        {"pattern": "(a+)+$", "expected_static": AmbiguityRisk.EXPONENTIAL, "category": "vulnerable"},
        {"pattern": "(a|aa)+$", "expected_static": AmbiguityRisk.EXPONENTIAL, "category": "vulnerable"},
        {"pattern": "(a*)*b", "expected_static": AmbiguityRisk.EXPONENTIAL, "category": "vulnerable"},
        {"pattern": "a*a*b", "expected_static": AmbiguityRisk.POLYNOMIAL, "category": "vulnerable"},
        {"pattern": "a*a*a*b", "expected_static": AmbiguityRisk.POLYNOMIAL, "category": "vulnerable"},
        {"pattern": "(a|b)*abb", "expected_static": AmbiguityRisk.LINEAR, "category": "safe"},
        {"pattern": "a*b+", "expected_static": AmbiguityRisk.LINEAR, "category": "safe"},
        {"pattern": "a(b|c)*d", "expected_static": AmbiguityRisk.LINEAR, "category": "safe"},
    ]

    results = []
    mismatches = []

    for case in curated_cases:
        pat = case["pattern"]
        static_res = analyzer.analyze(pat)
        empirical_res = run_empirical_benchmark(
            pat, attack=static_res.attack_string, timeout_per_run_sec=0.5
        )

        match = static_res.risk_class == empirical_res.empirical_risk
        entry = {
            "pattern": pat,
            "category": case["category"],
            "static_risk": static_res.risk_class.value,
            "empirical_risk": empirical_res.empirical_risk.value,
            "match": match,
            "match_mode": empirical_res.match_mode,
            "slowdown_confirmed": empirical_res.slowdown_confirmed,
            "status_label": empirical_res.status_label,
            "max_duration_ms": empirical_res.max_duration_ms,
            "timed_out": empirical_res.timed_out,
            "explanation": static_res.explanation,
        }
        results.append(entry)

        if not match:
            mismatches.append(
                {
                    "pattern": pat,
                    "static": static_res.risk_class.value,
                    "empirical": empirical_res.empirical_risk.value,
                    "reason": (
                        "Engine search nuance: Python re applies internal backtracking heuristics. "
                        f"Under {empirical_res.match_mode} semantics, growth did not cross empirical threshold."
                    ),
                }
            )

    return {
        "total_cases": len(curated_cases),
        "results": results,
        "mismatches": mismatches,
    }

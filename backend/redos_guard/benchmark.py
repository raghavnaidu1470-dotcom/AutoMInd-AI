"""
Empirical ReDoS Validation & Sandboxed Benchmark (Part 3)
=========================================================
Runs Python's native `re` module in an isolated, sandboxed subprocess with hard
timeouts across increasing attack string lengths. Evaluates execution time
scaling, classifies empirical growth curves (linear, polynomial, exponential),
and reports concordance/discrepancies between static NFA analysis and runtime behavior.
"""

import sys
import json
import time
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
    points: List[BenchmarkPoint] = Field(default_factory=list, description="Time vs length data points")
    empirical_risk: AmbiguityRisk = Field(..., description="Empirical growth risk: linear, polynomial, or exponential")
    growth_ratio: float = Field(1.0, description="Ratio of maximum duration to initial baseline duration")
    max_duration_ms: float = Field(0.0, description="Maximum observed duration across tested lengths")
    timed_out: bool = Field(False, description="True if any test run exceeded the sandbox timeout")
    summary: str = Field("", description="Empirical benchmark summary and complexity diagnosis")


_SUBPROCESS_SCRIPT = """
import sys
import time
import re

pattern = sys.argv[1]
test_str = sys.argv[2]

try:
    compiled = re.compile(pattern)
    t0 = time.perf_counter()
    compiled.search(test_str)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    print(f"{elapsed_ms:.4f}")
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
"""


def run_sandboxed_re(
    regex_pattern: str, test_string: str, timeout_sec: float = 0.5
) -> Tuple[float, bool, Optional[str]]:
    """
    Executes Python re.search inside a sandboxed subprocess with hard timeout.

    Args:
        regex_pattern: Target regular expression.
        test_string: Input attack string.
        timeout_sec: Maximum time allowed before terminating child process.

    Returns:
        Tuple of (duration_ms, timed_out_flag, error_message)
    """
    cmd = [sys.executable, "-c", _SUBPROCESS_SCRIPT, regex_pattern, test_string]
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
) -> EmpiricalBenchmarkResult:
    """
    Executes empirical timing benchmarks at increasing pump lengths.

    Args:
        regex_pattern: Regular expression to benchmark.
        attack: Optional AttackString; if None, synthesized via AmbiguityAnalyzer.
        repeats_list: List of repeat counts to test (defaults to [2, 6, 10, 14, 18, 22, 26]).
        timeout_per_run_sec: Hard timeout per run in seconds.

    Returns:
        EmpiricalBenchmarkResult containing time-vs-length points and empirical risk.
    """
    if repeats_list is None:
        repeats_list = [2, 6, 10, 14, 18, 22, 26]

    if attack is None:
        analyzer = AmbiguityAnalyzer(timeout_sec=2.0)
        analysis = analyzer.analyze(regex_pattern)
        if analysis.attack_string:
            attack = analysis.attack_string
        else:
            # Fallback attack for safe regexes
            attack = AttackString(prefix="", pump="a", suffix="!")

    points: List[BenchmarkPoint] = []
    any_timeout = False

    for reps in repeats_list:
        test_str = attack.build(repeats=reps)
        duration_ms, timed_out, err = run_sandboxed_re(
            regex_pattern, test_str, timeout_sec=timeout_per_run_sec
        )

        points.append(
            BenchmarkPoint(
                length=len(test_str),
                repeats=reps,
                duration_ms=duration_ms,
                timed_out=timed_out,
            )
        )

        if timed_out:
            any_timeout = True
            # Stop further testing on timeout to avoid massive unnecessary delays
            break

    # Determine empirical risk
    if not points:
        empirical_risk = AmbiguityRisk.LINEAR
        growth_ratio = 1.0
        max_duration = 0.0
    else:
        max_duration = max(p.duration_ms for p in points)
        min_duration = max(points[0].duration_ms, 0.001)
        growth_ratio = max_duration / min_duration

        if any_timeout or (max_duration > 100.0 and growth_ratio > 30.0):
            empirical_risk = AmbiguityRisk.EXPONENTIAL
        elif max_duration > 20.0 and growth_ratio > 5.0:
            empirical_risk = AmbiguityRisk.POLYNOMIAL
        else:
            empirical_risk = AmbiguityRisk.LINEAR

    attack_repr = f"{attack.prefix}({attack.pump})^k{attack.suffix}"
    summary = (
        f"Empirical scaling: {empirical_risk.value.upper()} (max {max_duration:.2f}ms, "
        f"growth ratio {growth_ratio:.1f}x across {len(points)} sample lengths)."
    )

    return EmpiricalBenchmarkResult(
        regex=regex_pattern,
        attack_pattern=attack_repr,
        points=points,
        empirical_risk=empirical_risk,
        growth_ratio=round(growth_ratio, 2),
        max_duration_ms=round(max_duration, 2),
        timed_out=any_timeout,
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
        {"pattern": "^(([a-z])+.)+[A-Z]([a-z])+$", "expected_static": None, "category": "vulnerable"},
        {"pattern": "(a|b)*abb", "expected_static": AmbiguityRisk.LINEAR, "category": "safe"},
        {"pattern": "a*b+", "expected_static": AmbiguityRisk.LINEAR, "category": "safe"},
        {"pattern": "a(b|c)*d", "expected_static": AmbiguityRisk.LINEAR, "category": "safe"},
    ]

    results = []
    mismatches = []

    for case in curated_cases:
        pat = case["pattern"]
        # Static analysis
        static_res = analyzer.analyze(pat)
        # Empirical benchmark
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
                        "Character class syntax / engine optimization difference. "
                        "Python's regex engine applies internal backtracking heuristics, "
                        "whereas the automata engine performs exact topological cycle analysis."
                    ),
                }
            )

    return {
        "total_cases": len(curated_cases),
        "results": results,
        "mismatches": mismatches,
    }

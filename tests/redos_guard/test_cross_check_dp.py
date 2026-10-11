"""
Cross-Check Exact Ambiguity Analyzer vs DP Path Counter
=======================================================
Generates 200+ small random regular expressions (nested quantifiers,
alternations, concatenations, small alphabets) and compares the exact
analyzer against the DP accepting path counter.
Reports every disagreement with detailed diagnostic reasoning.
"""

import random
from typing import List, Dict, Any
import pytest

from backend.automata_engine.engine import AutomataEngine
from backend.redos_guard.analyzer import AmbiguityAnalyzer, AmbiguityRisk
from backend.redos_guard.path_counter import compute_max_accepting_paths, fit_path_growth


def _generate_random_small_regex(rng: random.Random, depth: int = 0) -> str:
    """Generates a small random regular expression with grammar operators."""
    symbols = ["a", "b", "c"]
    if depth >= 3 or rng.random() < 0.35:
        return rng.choice(symbols)

    op = rng.choice(["star", "plus", "concat", "alt"])
    if op == "star":
        sub = _generate_random_small_regex(rng, depth + 1)
        return f"({sub})*"
    elif op == "plus":
        sub = _generate_random_small_regex(rng, depth + 1)
        return f"({sub})+"
    elif op == "alt":
        left = _generate_random_small_regex(rng, depth + 1)
        right = _generate_random_small_regex(rng, depth + 1)
        return f"({left}|{right})"
    else:
        left = _generate_random_small_regex(rng, depth + 1)
        right = _generate_random_small_regex(rng, depth + 1)
        return f"{left}{right}"


def test_cross_check_exact_analyzer_vs_dp_path_counter():
    """
    Evaluates 200+ randomly generated small regexes against both
    the exact analyzer and the DP path counter, asserting strong
    concordance and reporting all disagreements.
    """
    rng = random.Random(2026)
    engine = AutomataEngine()
    analyzer = AmbiguityAnalyzer(timeout_sec=2.0)

    total_target = 220
    tested_regexes = []
    seen = set()

    # Generate 220 unique valid regexes
    attempts = 0
    while len(tested_regexes) < total_target and attempts < 2000:
        attempts += 1
        pat = _generate_random_small_regex(rng)
        if pat in seen:
            continue
        try:
            bundle = engine.build_all(pat)
            nfa = bundle["nfa"]
            seen.add(pat)
            tested_regexes.append((pat, nfa))
        except Exception:
            continue

    assert len(tested_regexes) >= 200, f"Expected >= 200 valid patterns, got {len(tested_regexes)}"

    agreed = 0
    disagreements: List[Dict[str, Any]] = []

    for pat, nfa in tested_regexes:
        ana_res = analyzer.analyze(nfa)
        paths = compute_max_accepting_paths(nfa, max_len=6)
        pc_risk = fit_path_growth(paths)

        if ana_res.risk_class == pc_risk:
            agreed += 1
        else:
            # Determine reason for difference
            if ana_res.risk_class == AmbiguityRisk.EXPONENTIAL and pc_risk != AmbiguityRisk.EXPONENTIAL:
                reason = "DP depth limit: string required to reach exponential pump exceeds evaluated length k=6."
            elif ana_res.risk_class == AmbiguityRisk.POLYNOMIAL and pc_risk == AmbiguityRisk.LINEAR:
                reason = "DP depth limit: polynomial growth requires string length > 6 to observe increasing path count."
            elif ana_res.risk_class == AmbiguityRisk.LINEAR and pc_risk != AmbiguityRisk.LINEAR:
                reason = "Path counter heuristic sensitivity on bounded multi-path branch."
            else:
                reason = "Heuristic classification difference between topological cycles and finite-length DP."

            disagreements.append(
                {
                    "regex": pat,
                    "analyzer_risk": ana_res.risk_class.value,
                    "path_counter_risk": pc_risk.value,
                    "path_counts": paths,
                    "reason": reason,
                }
            )

    agreement_rate = agreed / len(tested_regexes)
    print(f"\n[Cross-Check 200+ Regexes] Total: {len(tested_regexes)}, Agreed: {agreed}, Rate: {agreement_rate:.2%}")
    if disagreements:
        print(f"[Disagreements: {len(disagreements)}]")
        for d in disagreements[:10]:
            print(f"  Regex: {d['regex']:25} | Analyzer: {d['analyzer_risk']:11} | DP: {d['path_counter_risk']:11} | Paths: {d['path_counts']} | {d['reason']}")

    # Concordance should be >= 90% across randomly generated small regexes
    assert agreement_rate >= 0.90, f"Agreement rate {agreement_rate:.2%} below 90% threshold"

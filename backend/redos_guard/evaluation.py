"""
ReDoS Guard — Independent Evaluation Suite & Confusion Matrix Generator
=======================================================================
Runs evaluation on an independent suite of 64 pre-labeled regular expressions
spanning Exponential, Polynomial, and Linear risk classes.

Compares:
  1. Intended Ground-Truth Label (written BEFORE running evaluation)
  2. Exact Analyzer (Weber & Seidl 1991 Pair-Graph / Chained Cycle)
  3. Independent Path Counter (DP accepting path growth on small NFAs)
  4. Sandboxed Empirical Runtime Benchmark (Python re.search growth)

Generates:
  - Disagreement analysis explaining any engine nuances or differences
  - 3x3 Confusion Matrices for all three methods
  - Per-class precision, recall, and overall accuracy
"""

from typing import List, Dict, Any, Tuple, Optional
import json
import time

from backend.redos_guard.analyzer import AmbiguityAnalyzer, AmbiguityRisk
from backend.redos_guard.path_counter import compute_max_accepting_paths, fit_path_growth
from backend.redos_guard.benchmark import run_empirical_benchmark
from backend.automata_engine.engine import AutomataEngine


EVALUATION_SET: List[Dict[str, str]] = [
    # Exponential (EDA) cases
    {"pattern": "(a+)+", "intended": "exponential", "family": "nested_plus"},
    {"pattern": "(a*)*", "intended": "exponential", "family": "nested_star"},
    {"pattern": "((a+)+)+", "intended": "exponential", "family": "nested_plus_deep"},
    {"pattern": "(a|aa)+", "intended": "exponential", "family": "overlapping_alternation"},
    {"pattern": "(a|a+)+", "intended": "exponential", "family": "overlapping_alternation"},
    {"pattern": "(a*)*b", "intended": "exponential", "family": "nested_star"},
    {"pattern": "(a+)*b", "intended": "exponential", "family": "nested_star"},
    {"pattern": "(a*)+b", "intended": "exponential", "family": "nested_star"},
    {"pattern": "((a|b)+)+", "intended": "exponential", "family": "nested_union"},
    {"pattern": "(a|b|ab)+", "intended": "exponential", "family": "overlapping_union"},
    {"pattern": "(ba*a*)+", "intended": "exponential", "family": "overlapping_stars_in_loop"},
    {"pattern": "([a-z]+)+", "intended": "exponential", "family": "nested_class_plus"},
    {"pattern": "(a+a+)+", "intended": "exponential", "family": "nested_concat_plus"},
    {"pattern": "(0|00)+1", "intended": "exponential", "family": "overlapping_alternation"},
    {"pattern": "(1+)+0", "intended": "exponential", "family": "nested_plus"},
    {"pattern": "(x|xx)+y", "intended": "exponential", "family": "overlapping_alternation"},
    {"pattern": r"(\d+)+", "intended": "exponential", "family": "nested_class_plus"},
    {"pattern": "(a?a?)+$", "intended": "exponential", "family": "optional_loop_anchored"},
    {"pattern": "(a|b*)+", "intended": "exponential", "family": "nested_union_star"},
    {"pattern": "((0+)+)+", "intended": "exponential", "family": "nested_plus_deep"},
    {"pattern": "(a+)+$", "intended": "exponential", "family": "nested_plus_anchored"},
    {"pattern": "(a*|b*)*", "intended": "exponential", "family": "nested_union_star"},

    # Polynomial (PDA) cases
    {"pattern": "a*a*b", "intended": "polynomial", "family": "chained_stars_2"},
    {"pattern": "a*a*a*b", "intended": "polynomial", "family": "chained_stars_3"},
    {"pattern": "a+a+b", "intended": "polynomial", "family": "chained_plus_2"},
    {"pattern": "a+a+a+b", "intended": "polynomial", "family": "chained_plus_3"},
    {"pattern": "x*x*y", "intended": "polynomial", "family": "chained_stars_2"},
    {"pattern": "0*0*1", "intended": "polynomial", "family": "chained_stars_2"},
    {"pattern": "(a|b)*a*(a|b)*c", "intended": "polynomial", "family": "interleaved_stars"},
    {"pattern": "a*b*a*b*c", "intended": "polynomial", "family": "interleaved_stars"},
    {"pattern": "(a|c)*(a|d)*b", "intended": "polynomial", "family": "overlapping_star_chain"},
    {"pattern": r"\d*\d*$", "intended": "polynomial", "family": "chained_class_stars"},
    {"pattern": "[0-9]*[0-9]*x", "intended": "polynomial", "family": "chained_class_stars"},
    {"pattern": "[a-z]*[a-z]*!", "intended": "polynomial", "family": "chained_class_stars"},
    {"pattern": "a*ba*b", "intended": "polynomial", "family": "token_separated_stars"},
    {"pattern": "(a*b)*a*", "intended": "polynomial", "family": "token_separated_stars"},
    {"pattern": "c*c*d", "intended": "polynomial", "family": "chained_stars_2"},
    {"pattern": "m*m*n", "intended": "polynomial", "family": "chained_stars_2"},
    {"pattern": "p*p*q", "intended": "polynomial", "family": "chained_stars_2"},
    {"pattern": "s*s*t", "intended": "polynomial", "family": "chained_stars_2"},
    {"pattern": "w*w*v", "intended": "polynomial", "family": "chained_stars_2"},
    {"pattern": "k*k*k*m", "intended": "polynomial", "family": "chained_stars_3"},

    # Linear (Safe) cases
    {"pattern": "a*b+", "intended": "linear", "family": "safe_disjoint_seq"},
    {"pattern": "a+b+c+", "intended": "linear", "family": "safe_disjoint_seq"},
    {"pattern": "(a|b)*abb", "intended": "linear", "family": "safe_loop_exit"},
    {"pattern": "hello", "intended": "linear", "family": "safe_literal"},
    {"pattern": "foo|bar", "intended": "linear", "family": "safe_disjoint_union"},
    {"pattern": "(0|1)*00", "intended": "linear", "family": "safe_loop_exit"},
    {"pattern": "a(b|c)*d", "intended": "linear", "family": "safe_bounded_loop"},
    {"pattern": r"^[a-z]+@[a-z]+\.[a-z]+$", "intended": "linear", "family": "safe_anchored_email"},
    {"pattern": r"^\d\d\d-\d\d\d\d$", "intended": "linear", "family": "safe_anchored_phone"},
    {"pattern": "^user_[a-zA-Z0-9]+$", "intended": "linear", "family": "safe_anchored_ident"},
    {"pattern": "^https?://[a-z0-9]+$", "intended": "linear", "family": "safe_anchored_url"},
    {"pattern": r"^[0-9]+(\.[0-9]+)?$", "intended": "linear", "family": "safe_anchored_float"},
    {"pattern": "a?b+c*", "intended": "linear", "family": "safe_sequential_ops"},
    {"pattern": "(a|b)c(d|e)", "intended": "linear", "family": "safe_branching_dag"},
    {"pattern": "ab*c+", "intended": "linear", "family": "safe_sequential_ops"},
    {"pattern": "(x|y)*z", "intended": "linear", "family": "safe_loop_exit"},
    {"pattern": "1*0+", "intended": "linear", "family": "safe_disjoint_seq"},
    {"pattern": "(p|q)*r(s|t)*", "intended": "linear", "family": "safe_token_separated_loops"},
    {"pattern": "cat|dog|fish", "intended": "linear", "family": "safe_disjoint_union"},
    {"pattern": r"^test\d+$", "intended": "linear", "family": "safe_anchored_prefix"},
    {"pattern": "alpha(beta|gamma)", "intended": "linear", "family": "safe_prefix_union"},
    {"pattern": "^abc$", "intended": "linear", "family": "safe_exact_literal"},
]


def compute_confusion_matrix(
    predictions: List[str], ground_truth: List[str]
) -> Dict[str, Any]:
    """
    Computes a 3x3 confusion matrix and per-class precision / recall / F1.
    Classes: ['linear', 'polynomial', 'exponential']
    """
    classes = ["linear", "polynomial", "exponential"]
    matrix = {act: {pred: 0 for pred in classes} for act in classes}

    for act, pred in zip(ground_truth, predictions):
        if act in matrix and pred in matrix[act]:
            matrix[act][pred] += 1

    total = len(ground_truth)
    correct = sum(matrix[c][c] for c in classes)
    accuracy = correct / total if total > 0 else 0.0

    per_class = {}
    for c in classes:
        tp = matrix[c][c]
        fp = sum(matrix[other][c] for other in classes if other != c)
        fn = sum(matrix[c][other] for other in classes if other != c)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        per_class[c] = {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        }

    return {
        "accuracy": round(accuracy, 4),
        "total": total,
        "correct": correct,
        "matrix": matrix,
        "per_class": per_class,
    }


def run_comprehensive_evaluation(save_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs evaluation of all 64 regexes across exact analyzer, path counter,
    and empirical sandboxed benchmark. Reports all disagreements and confusion matrices.
    """
    engine = AutomataEngine()
    analyzer = AmbiguityAnalyzer(timeout_sec=3.0)

    rows = []
    intended_labels = []
    analyzer_labels = []
    path_counter_labels = []
    benchmark_labels = []
    disagreements = []

    for item in EVALUATION_SET:
        pattern = item["pattern"]
        intended = item["intended"]
        intended_labels.append(intended)

        # 1. Exact Analyzer
        try:
            nfa = engine.build_all(pattern)["nfa"]
            ana_res = analyzer.analyze(nfa)
            ana_pred = ana_res.risk_class.value
            attack_str = ana_res.attack_string
        except Exception as exc:
            ana_pred = "error"
            attack_str = None
        analyzer_labels.append(ana_pred)

        # 2. Independent Path Counter
        try:
            paths = compute_max_accepting_paths(nfa, max_len=6)
            pc_fit = fit_path_growth(paths)
            pc_pred = pc_fit.value
        except Exception:
            pc_pred = "error"
            paths = []
        path_counter_labels.append(pc_pred)

        # 3. Sandboxed Runtime Benchmark
        try:
            bench_res = run_empirical_benchmark(
                pattern, attack=attack_str, repeats_list=[2, 6, 10, 14, 18, 22], timeout_per_run_sec=0.25
            )
            bm_pred = bench_res.empirical_risk.value
            max_ms = bench_res.max_duration_ms
        except Exception:
            bm_pred = "error"
            max_ms = 0.0
        benchmark_labels.append(bm_pred)

        # Track disagreements
        row = {
            "pattern": pattern,
            "family": item["family"],
            "intended": intended,
            "analyzer": ana_pred,
            "path_counter": pc_pred,
            "benchmark": bm_pred,
            "paths": paths[:7],
            "benchmark_max_ms": max_ms,
        }
        rows.append(row)

        has_disagreement = (
            ana_pred != intended
            or pc_pred != intended
            or bm_pred != intended
        )
        if has_disagreement:
            reason = ""
            if ana_pred == intended and bm_pred != intended:
                reason = (
                    "Engine search nuance: Python re.search terminates upon first match "
                    "for unanchored patterns unless forced to fail on a non-matching suffix."
                )
            elif pc_pred != intended:
                reason = "Small alphabet / depth restriction in path-counting DP."
            else:
                reason = "Algorithmic disagreement between static criteria and empirical runtime."

            disagreements.append({
                "pattern": pattern,
                "intended": intended,
                "analyzer": ana_pred,
                "path_counter": pc_pred,
                "benchmark": bm_pred,
                "reason": reason,
            })

    analyzer_cm = compute_confusion_matrix(analyzer_labels, intended_labels)
    path_counter_cm = compute_confusion_matrix(path_counter_labels, intended_labels)
    benchmark_cm = compute_confusion_matrix(benchmark_labels, intended_labels)

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_patterns": len(EVALUATION_SET),
        "analyzer_evaluation": analyzer_cm,
        "path_counter_evaluation": path_counter_cm,
        "benchmark_evaluation": benchmark_cm,
        "disagreements": disagreements,
        "disagreement_count": len(disagreements),
        "rows": rows,
    }

    if save_path:
        with open(save_path, "w") as f:
            json.dump(report, f, indent=2)

    return report

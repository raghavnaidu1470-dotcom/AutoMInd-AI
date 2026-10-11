"""
ReDoS Guard — Grammar-Based Regex Dataset Generator
===================================================
Generates at least 3,000 diverse regular expressions spanning Linear,
Polynomial, and Exponential ambiguity classes using grammar-based production
rules (nested quantifiers, alternations, concatenations, small alphabets,
disjoint and overlapping structures).

Labels each regular expression with the optimized Exact Ambiguity Analyzer,
canonicalizes templates (normalizing literal tokens while preserving operators),
and splits strictly by template family to guarantee zero template overlap
between training and test sets.
"""

import os
import json
import random
from typing import List, Dict, Tuple, Any, Set
from collections import defaultdict

from backend.redos_guard.analyzer import AmbiguityAnalyzer, AmbiguityRisk


def extract_canonical_template(pattern: str) -> str:
    """
    Normalizes variable literal tokens into canonical positional slots (V0, V1, ...)
    while preserving regex structure, quantifiers, groups, and alternations:
    ()|*+?^$[]- and escape sequences.
    """
    i = 0
    var_map: Dict[str, str] = {}
    var_counter = 0
    res: List[str] = []

    while i < len(pattern):
        c = pattern[i]
        if c == "\\":
            res.append(pattern[i : i + 2])
            i += 2
        elif c in "()*+?|.^$[]-":
            res.append(c)
            i += 1
        else:
            if c not in var_map:
                var_map[c] = f"V{var_counter}"
                var_counter += 1
            res.append(var_map[c])
            i += 1

    return "".join(res)


# Define structural families and production rules
# Alphabets used to generate rich literal variations
ALPHABETS = [
    ["a", "b", "c", "d"],
    ["0", "1", "2", "3"],
    ["x", "y", "z", "w"],
    ["p", "q", "r", "s"],
    ["m", "n", "k", "l"],
    ["u", "v", "w", "x"],
]

# Exponential (EDA) rules: (family, rule_fn)
EXP_RULES: List[Tuple[str, Any]] = [
    # nested_plus family (Train)
    ("nested_plus", lambda A: f"(({A[0]}+)+)"),
    ("nested_plus", lambda A: f"(({A[0]}+)+){A[1]}"),
    ("nested_plus", lambda A: f"(({A[0]}+)+)$"),
    ("nested_plus", lambda A: f"{A[1]}(({A[0]}+)+){A[2]}"),
    # nested_star family (Train)
    ("nested_star", lambda A: f"(({A[0]}*)*)"),
    ("nested_star", lambda A: f"(({A[0]}*)*){A[1]}"),
    ("nested_star", lambda A: f"({A[0]}*)*{A[1]}"),
    # overlapping_union family (Train)
    ("overlapping_union", lambda A: f"({A[0]}|{A[1]}|{A[0]}{A[1]})+"),
    ("overlapping_union", lambda A: f"({A[0]}|{A[1]}|{A[1]}{A[0]})+{A[2]}"),
    ("overlapping_union", lambda A: f"({A[0]}|{A[1]}|{A[0]}{A[1]})+{A[2]}"),
    # nested_concat_plus family (Train)
    ("nested_concat_plus", lambda A: f"({A[0]}+{A[0]}+)+"),
    ("nested_concat_plus", lambda A: f"({A[0]}+{A[0]}+)+{A[1]}"),
    ("nested_concat_plus", lambda A: f"({A[0]}*{A[0]}*)+"),
    # overlapping_stars_in_loop family (Train)
    ("overlapping_stars_in_loop", lambda A: f"({A[1]}{A[0]}*{A[0]}*)+"),
    ("overlapping_stars_in_loop", lambda A: f"({A[1]}{A[0]}*{A[0]}*)+{A[2]}"),
    # nested_plus_deep family (Test)
    ("nested_plus_deep", lambda A: f"((({A[0]}+)+)+)"),
    ("nested_plus_deep", lambda A: f"((({A[0]}+)+)+){A[1]}"),
    # nested_star_deep family (Test)
    ("nested_star_deep", lambda A: f"((({A[0]}*)*)*)"),
    ("nested_star_deep", lambda A: f"((({A[0]}*)*)*){A[1]}"),
    # overlapping_alternation family (Test)
    ("overlapping_alternation", lambda A: f"({A[0]}|{A[0]}{A[0]})+"),
    ("overlapping_alternation", lambda A: f"({A[0]}|{A[0]}+)+"),
    ("overlapping_alternation", lambda A: f"({A[0]}|{A[0]}{A[0]})+{A[1]}"),
    ("overlapping_alternation", lambda A: f"({A[0]}|{A[0]}{A[0]})+{A[1]}$"),
    # nested_union_star family (Test)
    ("nested_union_star", lambda A: f"({A[0]}|{A[1]}*)+"),
    ("nested_union_star", lambda A: f"({A[0]}*|{A[1]}*)*"),
    ("nested_union_star", lambda A: f"({A[0]}|{A[0]}*)+"),
]

# Polynomial (PDA) rules: (family, rule_fn)
POLY_RULES: List[Tuple[str, Any]] = [
    # chained_stars_2 family (Train)
    ("chained_stars_2", lambda A: f"{A[0]}*{A[0]}*{A[1]}"),
    ("chained_stars_2", lambda A: f"{A[0]}*{A[0]}*{A[1]}$"),
    ("chained_stars_2", lambda A: f"^{A[0]}*{A[0]}*{A[1]}$"),
    # chained_plus_2 family (Train)
    ("chained_plus_2", lambda A: f"{A[0]}+{A[0]}+{A[1]}"),
    ("chained_plus_2", lambda A: f"{A[0]}+{A[0]}+{A[1]}$"),
    # chained_stars_4 family (Train)
    ("chained_stars_4", lambda A: f"{A[0]}*{A[0]}*{A[0]}*{A[0]}*{A[1]}"),
    ("chained_stars_4", lambda A: f"{A[0]}*{A[0]}*{A[0]}*{A[0]}*{A[1]}$"),
    # interleaved_stars family (Train)
    ("interleaved_stars", lambda A: f"{A[0]}*{A[1]}*{A[0]}*{A[1]}*{A[2]}"),
    ("interleaved_stars", lambda A: f"({A[0]}|{A[1]})*{A[0]}*({A[0]}|{A[1]})*{A[2]}"),
    # chained_stars_3 family (Test)
    ("chained_stars_3", lambda A: f"{A[0]}*{A[0]}*{A[0]}*{A[1]}"),
    ("chained_stars_3", lambda A: f"{A[0]}*{A[0]}*{A[0]}*{A[1]}$"),
    # chained_plus_3 family (Test)
    ("chained_plus_3", lambda A: f"{A[0]}+{A[0]}+{A[0]}+{A[1]}"),
    ("chained_plus_3", lambda A: f"{A[0]}+{A[0]}+{A[0]}+{A[1]}$"),
    # overlapping_star_chain family (Test)
    ("overlapping_star_chain", lambda A: f"({A[0]}|{A[1]})*({A[0]}|{A[2]})*{A[3]}"),
    ("overlapping_star_chain", lambda A: f"({A[0]}|{A[2]})*({A[1]}|{A[2]})*{A[3]}"),
    # chained_prefixed_stars family (Test)
    ("chained_prefixed_stars", lambda A: f"{A[1]}{A[0]}*{A[0]}*{A[2]}"),
    ("chained_prefixed_stars", lambda A: f"{A[1]}{A[0]}*{A[0]}*{A[0]}*{A[2]}"),
]

# Linear / Safe rules: (family, rule_fn)
LINEAR_RULES: List[Tuple[str, Any]] = [
    # safe_disjoint_seq family (Train)
    ("safe_disjoint_seq", lambda A: f"{A[0]}*{A[1]}+"),
    ("safe_disjoint_seq", lambda A: f"{A[0]}+{A[1]}+{A[2]}+"),
    ("safe_disjoint_seq", lambda A: f"{A[0]}?{A[1]}+{A[2]}*"),
    ("safe_disjoint_seq", lambda A: f"{A[0]}{A[1]}*{A[2]}+"),
    # safe_disjoint_union family (Train)
    ("safe_disjoint_union", lambda A: f"{A[0]}|{A[1]}"),
    ("safe_disjoint_union", lambda A: f"{A[0]}|{A[1]}|{A[2]}"),
    ("safe_disjoint_union", lambda A: f"{A[0]}|{A[1]}|{A[2]}|{A[3]}"),
    # safe_literal family (Train)
    ("safe_literal", lambda A: f"{A[0]}{A[1]}{A[2]}"),
    ("safe_literal", lambda A: f"{A[0]}{A[1]}{A[0]}{A[2]}"),
    ("safe_literal", lambda A: f"{A[0]}{A[1]}{A[2]}{A[3]}"),
    # safe_bounded_loop family (Train)
    ("safe_bounded_loop", lambda A: f"{A[0]}({A[1]}|{A[2]})*{A[3]}"),
    ("safe_bounded_loop", lambda A: f"({A[0]}|{A[1]})*{A[2]}({A[0]}|{A[3]})*"),
    # token_separated_stars family (Train)
    ("token_separated_stars", lambda A: f"{A[0]}*{A[1]}{A[0]}*{A[1]}"),
    ("token_separated_stars", lambda A: f"({A[0]}*{A[1]})*{A[0]}*"),
    # safe_loop_exit family (Test)
    ("safe_loop_exit", lambda A: f"({A[0]}|{A[1]})*{A[0]}{A[1]}{A[1]}"),
    ("safe_loop_exit", lambda A: f"({A[0]}|{A[1]})*{A[2]}"),
    ("safe_loop_exit", lambda A: f"({A[0]}|{A[1]})*{A[0]}{A[0]}"),
    # safe_branching_dag family (Test)
    ("safe_branching_dag", lambda A: f"({A[0]}|{A[1]}){A[2]}({A[0]}|{A[3]})"),
    ("safe_branching_dag", lambda A: f"{A[0]}({A[1]}|{A[2]})({A[0]}|{A[3]}){A[2]}"),
    # disjoint_alternations_bounded family (Test)
    ("disjoint_alternations_bounded", lambda A: f"({A[0]}+|{A[0]}+)"),
    ("disjoint_alternations_bounded", lambda A: f"{A[1]}({A[0]}+|{A[0]}+){A[2]}"),
    ("disjoint_alternations_bounded", lambda A: f"({A[0]}*|{A[0]}*){A[1]}"),
]

# Family Split Partition (Train vs Test)
# Every family belongs strictly to EITHER Train OR Test.
TRAIN_FAMILIES = {
    # Exponential
    "nested_plus",
    "nested_star",
    "overlapping_union",
    "nested_concat_plus",
    "overlapping_stars_in_loop",
    # Polynomial
    "chained_stars_2",
    "chained_plus_2",
    "chained_stars_4",
    "interleaved_stars",
    # Linear
    "safe_disjoint_seq",
    "safe_disjoint_union",
    "safe_literal",
    "safe_bounded_loop",
    "token_separated_stars",
}

TEST_FAMILIES = {
    # Exponential
    "nested_plus_deep",
    "nested_star_deep",
    "overlapping_alternation",
    "nested_union_star",
    # Polynomial
    "chained_stars_3",
    "chained_plus_3",
    "overlapping_star_chain",
    "chained_prefixed_stars",
    # Linear
    "safe_loop_exit",
    "safe_branching_dag",
    "disjoint_alternations_bounded",
}

DATASET_FILE = os.path.join(os.path.dirname(__file__), "data", "grammar_dataset.json")


def generate_grammar_dataset(
    target_count: int = 3200, seed: int = 2026, force_rebuild: bool = False
) -> Dict[str, Any]:
    """
    Generates >= 3000 diverse regular expressions, labels each with the optimized
    Exact Ambiguity Analyzer, and splits by template family with zero overlap.
    Caches results to disk for fast subsequent training and testing.
    """
    if os.path.exists(DATASET_FILE) and not force_rebuild:
        try:
            with open(DATASET_FILE, "r") as f:
                cached = json.load(f)
                if len(cached.get("train", [])) + len(cached.get("test", [])) >= target_count:
                    return cached
        except Exception:
            pass

    rng = random.Random(seed)
    analyzer = AmbiguityAnalyzer(timeout_sec=2.0)

    train_data: List[Dict[str, Any]] = []
    test_data: List[Dict[str, Any]] = []
    seen_patterns: Set[str] = set()

    all_rules = EXP_RULES + POLY_RULES + LINEAR_RULES

    attempts = 0
    max_attempts = 15000

    while (len(train_data) + len(test_data) < target_count) and attempts < max_attempts:
        attempts += 1
        fam, rule_fn = rng.choice(all_rules)
        alph = rng.choice(ALPHABETS)
        shuffled = list(alph)
        rng.shuffle(shuffled)

        try:
            pat = rule_fn(shuffled)
        except Exception:
            continue

        if pat in seen_patterns:
            continue
        seen_patterns.add(pat)

        # Label with exact analyzer
        analysis = analyzer.analyze(pat)
        risk = analysis.risk_class.value
        tmpl = extract_canonical_template(pat)

        entry = {
            "pattern": pat,
            "family": fam,
            "template": tmpl,
            "risk_class": risk,
            "is_vulnerable": (risk != "linear"),
        }

        if fam in TRAIN_FAMILIES:
            train_data.append(entry)
        elif fam in TEST_FAMILIES:
            test_data.append(entry)

    # Verify no template overlap between train and test
    train_templates = {d["template"] for d in train_data}
    test_templates = {d["template"] for d in test_data}
    overlap = train_templates & test_templates

    # If any overlap exists across templates, remove ambiguous templates from test
    if overlap:
        test_data = [d for d in test_data if d["template"] not in overlap]

    os.makedirs(os.path.dirname(DATASET_FILE), exist_ok=True)
    dataset = {
        "total_count": len(train_data) + len(test_data),
        "train_count": len(train_data),
        "test_count": len(test_data),
        "train_families": sorted(list(TRAIN_FAMILIES)),
        "test_families": sorted(list(TEST_FAMILIES)),
        "train": train_data,
        "test": test_data,
    }

    with open(DATASET_FILE, "w") as f:
        json.dump(dataset, f, indent=2)

    return dataset

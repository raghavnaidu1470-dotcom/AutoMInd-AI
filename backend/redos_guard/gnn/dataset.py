"""
ReDoS Guard — Dataset Generator & Family-Stratified Split
=========================================================
Generates a curated, family-tagged dataset of regular expressions spanning
Linear (safe), Polynomial, and Exponential ambiguity classes.

Guarantees strict train/test splitting by regex FAMILY / TEMPLATE so that
no test regex or trivial variable rename of a test regex appears in training.
"""

from typing import List, Dict, Tuple, Any, Set
from backend.redos_guard.analyzer import AmbiguityAnalyzer, AmbiguityRisk
from backend.redos_guard.gnn.constants import RISK_CLASS_TO_IDX


def extract_regex_template(pattern: str) -> str:
    """
    Normalizes variable literal tokens into canonical positional variables (V0, V1, ...)
    while strictly preserving regex operators, groupings, and quantifiers:
    ()|*+?^$[]- and escape sequences.

    This ensures that structural templates (e.g. 'a*a*b' and 'c*c*d') map to the
    exact same canonical template 'V0*V0*V1', allowing automated detection of
    trivial variable renames across train/test splits.
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


# Training Set Families
TRAIN_FAMILIES_DATA: List[Dict[str, Any]] = [
    # Linear / Safe Families
    {"pattern": "a*b+", "family": "safe_disjoint_seq"},
    {"pattern": "x+y*z+", "family": "safe_disjoint_seq"},
    {"pattern": "a+b+c+", "family": "safe_disjoint_seq"},
    {"pattern": "1*0+", "family": "safe_disjoint_seq"},
    {"pattern": "a?b+c*", "family": "safe_disjoint_seq"},
    {"pattern": "ab*c+", "family": "safe_disjoint_seq"},
    {"pattern": "p*q+r*", "family": "safe_disjoint_seq"},
    {"pattern": "m+n*k+", "family": "safe_disjoint_seq"},
    {"pattern": "a|b", "family": "safe_disjoint_union"},
    {"pattern": "foo|bar", "family": "safe_disjoint_union"},
    {"pattern": "cat|dog|fish", "family": "safe_disjoint_union"},
    {"pattern": "red|green|blue", "family": "safe_disjoint_union"},
    {"pattern": "alpha|beta", "family": "safe_disjoint_union"},
    {"pattern": "left|right|up|down", "family": "safe_disjoint_union"},
    {"pattern": "a", "family": "safe_literal"},
    {"pattern": "ab", "family": "safe_literal"},
    {"pattern": "abc", "family": "safe_literal"},
    {"pattern": "hello", "family": "safe_literal"},
    {"pattern": "testing", "family": "safe_literal"},
    {"pattern": "world", "family": "safe_literal"},
    {"pattern": "(a|b)c(d|e)", "family": "safe_branching_dag"},
    {"pattern": "a(b|c)(d|e)f", "family": "safe_branching_dag"},
    {"pattern": "(0|1)x(2|3)y", "family": "safe_branching_dag"},
    {"pattern": "(x|y)z(u|v)w", "family": "safe_branching_dag"},

    # Polynomial (PDA) Families
    {"pattern": "a*a*b", "family": "chained_stars_2"},
    {"pattern": "x*x*y", "family": "chained_stars_2"},
    {"pattern": "0*0*1", "family": "chained_stars_2"},
    {"pattern": "c*c*d", "family": "chained_stars_2"},
    {"pattern": "m*m*n", "family": "chained_stars_2"},
    {"pattern": "p*p*q", "family": "chained_stars_2"},
    {"pattern": "s*s*t", "family": "chained_stars_2"},
    {"pattern": "w*w*v", "family": "chained_stars_2"},
    {"pattern": "u*u*z", "family": "chained_stars_2"},
    {"pattern": "a+a+b", "family": "chained_plus_2"},
    {"pattern": "x+x+y", "family": "chained_plus_2"},
    {"pattern": "1+1+0", "family": "chained_plus_2"},
    {"pattern": "m+m+n", "family": "chained_plus_2"},
    {"pattern": "p+p+q", "family": "chained_plus_2"},
    {"pattern": "c+c+d", "family": "chained_plus_2"},
    {"pattern": "(a|c)*(a|d)*b", "family": "overlapping_star_chain"},
    {"pattern": "(x|u)*(x|v)*w", "family": "overlapping_star_chain"},
    {"pattern": "(0|2)*(0|3)*1", "family": "overlapping_star_chain"},
    {"pattern": "(m|p)*(m|q)*n", "family": "overlapping_star_chain"},

    # Exponential (EDA) Families
    {"pattern": "(a+)+", "family": "nested_plus"},
    {"pattern": "(x+)+y", "family": "nested_plus"},
    {"pattern": "(1+)+0", "family": "nested_plus"},
    {"pattern": "(y+)+z", "family": "nested_plus"},
    {"pattern": "(m+)+n", "family": "nested_plus"},
    {"pattern": "(p+)+q", "family": "nested_plus"},
    {"pattern": "(a*)*", "family": "nested_star"},
    {"pattern": "(a*)*b", "family": "nested_star"},
    {"pattern": "((x*)*)*", "family": "nested_star"},
    {"pattern": "((a|b)*)*", "family": "nested_star"},
    {"pattern": "(c*)*d", "family": "nested_star"},
    {"pattern": "(a|b|ab)+", "family": "overlapping_union"},
    {"pattern": "(a|b|ab)+c", "family": "overlapping_union"},
    {"pattern": "(0|1|01)+", "family": "overlapping_union"},
    {"pattern": "(x|y|xy)+z", "family": "overlapping_union"},
    {"pattern": "(a|b*)+", "family": "nested_union_star"},
    {"pattern": "(a*|b*)*", "family": "nested_union_star"},
    {"pattern": "(a|a*)+", "family": "nested_union_star"},
    {"pattern": "(a*|a)*", "family": "nested_union_star"},
    {"pattern": "(x|y*)+z", "family": "nested_union_star"},
    {"pattern": "(a+a+)+", "family": "nested_concat_plus"},
    {"pattern": "(b+b+)+c", "family": "nested_concat_plus"},
    {"pattern": "(0+0+)+1", "family": "nested_concat_plus"},
    {"pattern": "(x+x+)+y", "family": "nested_concat_plus"},
]


# Held-out Test Set Families (Zero family overlap & zero template overlap with train)
TEST_FAMILIES_DATA: List[Dict[str, Any]] = [
    # Linear / Safe Families (Completely disjoint structures from train)
    {"pattern": "(a|b)*abb", "family": "safe_loop_exit"},
    {"pattern": "(0|1)*00", "family": "safe_loop_exit"},
    {"pattern": "(x|y)*z", "family": "safe_loop_exit"},
    {"pattern": "(0|1)+01", "family": "safe_loop_exit"},
    {"pattern": "a(b|c)*d", "family": "safe_bounded_loop"},
    {"pattern": "(p|q)*r(s|t)*", "family": "safe_bounded_loop"},
    {"pattern": r"^[a-z]+@[a-z]+\.[a-z]+$", "family": "safe_anchored"},
    {"pattern": r"^\d\d\d-\d\d\d\d$", "family": "safe_anchored"},
    {"pattern": "^user_[a-zA-Z0-9]+$", "family": "safe_anchored"},
    {"pattern": r"^[0-9]+$", "family": "safe_anchored"},
    {"pattern": r"^[0-9]+(\.[0-9]+)?$", "family": "safe_anchored"},

    # Polynomial (PDA) Families (Completely disjoint structures from train)
    {"pattern": "a*a*a*b", "family": "chained_stars_3"},
    {"pattern": "k*k*k*m", "family": "chained_stars_3"},
    {"pattern": "0*0*0*1", "family": "chained_stars_3"},
    {"pattern": "x*x*x*y", "family": "chained_stars_3"},
    {"pattern": "(a|b)*a*(a|b)*c", "family": "interleaved_stars"},
    {"pattern": "(x|y)*x*(x|y)*z", "family": "interleaved_stars"},
    {"pattern": "a*b*a*b*c", "family": "interleaved_stars"},
    {"pattern": "(p|q)*p*(p|q)*r", "family": "interleaved_stars"},
    {"pattern": r"\d*\d*$", "family": "chained_class_stars"},
    {"pattern": "[0-9]*[0-9]*x", "family": "chained_class_stars"},
    {"pattern": "[a-z]*[a-z]*!", "family": "chained_class_stars"},

    # Exponential (EDA) Families (Completely disjoint structures from train)
    {"pattern": "(a|aa)+", "family": "overlapping_alternation"},
    {"pattern": "(0|00)+1", "family": "overlapping_alternation"},
    {"pattern": "(x|xx)+y", "family": "overlapping_alternation"},
    {"pattern": "(b|bb)+", "family": "overlapping_alternation"},
    {"pattern": "(p|pp)+q", "family": "overlapping_alternation"},
    {"pattern": "(0|00)+", "family": "overlapping_alternation"},
    {"pattern": "((a+)+)+", "family": "nested_plus_deep"},
    {"pattern": "((0+)+)+", "family": "nested_plus_deep"},
    {"pattern": "((m+)+)+n", "family": "nested_plus_deep"},
    {"pattern": "([a-z]+)+", "family": "nested_class_plus"},
    {"pattern": r"(\d+)+", "family": "nested_class_plus"},
    {"pattern": "(a?a?)+$", "family": "optional_loop_anchored"},
]


def build_labeled_family_dataset(raw_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Labels a regex family dataset using the exact AmbiguityAnalyzer."""
    analyzer = AmbiguityAnalyzer(timeout_sec=2.0)
    dataset: List[Dict[str, Any]] = []

    for item in raw_list:
        pattern = item["pattern"]
        family = item["family"]
        try:
            res = analyzer.analyze(pattern)
            label = RISK_CLASS_TO_IDX[res.risk_class.value]
            dataset.append(
                {
                    "regex": pattern,
                    "family": family,
                    "template": extract_regex_template(pattern),
                    "label": label,
                    "risk_class": res.risk_class.value,
                    "offending_states": res.offending_states,
                }
            )
        except Exception:
            continue

    return dataset


def get_family_stratified_dataset(target_count: int = 3200) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns (train_dataset, test_dataset) strictly split by family from grammar-based generator.

    Guarantees:
      1. train_families.isdisjoint(test_families)
      2. train_templates.isdisjoint(test_templates)
      3. >= 3000 total regular expressions generated and labeled by exact analyzer.
    """
    from backend.redos_guard.gnn.generator import generate_grammar_dataset
    data = generate_grammar_dataset(target_count=target_count)

    train_data = []
    for item in data.get("train", []):
        pat = item.get("pattern") or item.get("regex")
        train_data.append(
            {
                "regex": pat,
                "pattern": pat,
                "family": item["family"],
                "template": item["template"],
                "label": RISK_CLASS_TO_IDX[item["risk_class"]],
                "risk_class": item["risk_class"],
                "is_vulnerable": item.get("is_vulnerable", item["risk_class"] != "linear"),
            }
        )

    test_data = []
    for item in data.get("test", []):
        pat = item.get("pattern") or item.get("regex")
        test_data.append(
            {
                "regex": pat,
                "pattern": pat,
                "family": item["family"],
                "template": item["template"],
                "label": RISK_CLASS_TO_IDX[item["risk_class"]],
                "risk_class": item["risk_class"],
                "is_vulnerable": item.get("is_vulnerable", item["risk_class"] != "linear"),
            }
        )

    train_families = {item["family"] for item in train_data}
    test_families = {item["family"] for item in test_data}
    assert train_families.isdisjoint(
        test_families
    ), f"Family overlap detected: {train_families & test_families}"

    train_templates = {item["template"] for item in train_data}
    test_templates = {item["template"] for item in test_data}
    assert train_templates.isdisjoint(
        test_templates
    ), f"Template overlap detected: {train_templates & test_templates}"

    return train_data, test_data


def build_redos_dataset(limit: int = 180) -> List[Dict[str, Any]]:
    """Backward compatibility wrapper returning balanced labeled dataset."""
    train_d, test_d = get_family_stratified_dataset()
    all_d = train_d + test_d
    by_label: Dict[int, List[Dict[str, Any]]] = {0: [], 1: [], 2: []}
    for item in all_d:
        by_label[item["label"]].append(item)

    interleaved: List[Dict[str, Any]] = []
    max_count = max(len(v) for v in by_label.values())
    for i in range(max_count):
        for c in [0, 1, 2]:
            if i < len(by_label[c]):
                interleaved.append(by_label[c][i])

    return interleaved[:limit]

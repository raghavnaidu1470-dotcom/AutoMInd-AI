"""
ReDoS Guard — Dataset Generator
===============================
Generates a balanced, curated and parametric dataset of regular expressions
spanning Linear (safe), Polynomial, and Exponential ambiguity classes.
Labels each regex using the exact Part 2 AmbiguityAnalyzer.
"""

from typing import List, Dict, Tuple, Any
from backend.redos_guard.analyzer import AmbiguityAnalyzer, AmbiguityRisk
from backend.redos_guard.gnn.constants import RISK_CLASS_TO_IDX


CURATED_LINEAR: List[str] = [
    "a", "ab", "abc", "a|b", "(a|b)", "(a|b)*", "(a|b)*abb",
    "a*b+", "a(b|c)*d", "(0|1)*00", "hello", "foo|bar",
    "a+b+", "a*b*c*", "(a|b)c(d|e)", "(x|y)*z", "1*0+",
    "(0|1)+01", "a?b+c*", "(a|b|c)d", "ab*c+", "x+y*z+",
    "(p|q)*r(s|t)*", "a(b|c)(d|e)f", "(1|0)*00(1|0)*",
]

CURATED_POLYNOMIAL: List[str] = [
    "a*a*b", "a+a+b", "x*x*y", "1*1*0", "p*p*q",
    "(a|b)*a*(a|b)*c", "(a|c)*(a|d)*b", "a*b*a*b*c",
    "x+x+y+", "(0|1)*0*(0|1)*1", "(a|b)*a+(a|b)*d",
    "m*m*n", "a*a*a*b", "(x|y)*x*(x|y)*z", "0*0*1",
    "c*c*d", "(a|b)+a+(a|b)+c", "s*s*t", "k*k*k*m",
    "(p|q)*p*(p|q)*r", "(1|2)*1*(1|2)*3", "w*w*v",
]

CURATED_EXPONENTIAL: List[str] = [
    "(a+)+", "(a*)*", "((a+)+)+", "(a+)*", "(a|aa)+",
    "(a|a+)+", "(a*|a)*", "(a*)*b", "(x+)+y", "(0|00)+1",
    "(a|b|ab)+c", "(a|b*)*c", "(a+)+$", "(1+)+0", "(x|xx)+",
    "((a|b)+)+", "(a+a+)+", "((0+)+)+", "(p|pp)+q",
    "((x*)*)*", "(b|bb)+", "(a|a*)+", "(0|00)+",
    "((a|b)*)*", "((1|11)+)+", "(y+)+z", "((m+)+)+n",
]

# Interleave curated so any slice has balanced representation
CURATED_REGEXES: List[str] = []
max_len = max(len(CURATED_LINEAR), len(CURATED_POLYNOMIAL), len(CURATED_EXPONENTIAL))
for i in range(max_len):
    if i < len(CURATED_LINEAR):
        CURATED_REGEXES.append(CURATED_LINEAR[i])
    if i < len(CURATED_POLYNOMIAL):
        CURATED_REGEXES.append(CURATED_POLYNOMIAL[i])
    if i < len(CURATED_EXPONENTIAL):
        CURATED_REGEXES.append(CURATED_EXPONENTIAL[i])


def generate_parametric_regexes() -> List[str]:
    """Generates parameterized regexes to diversify graph sizes and topologies."""
    generated: List[str] = []

    # Safe / Linear patterns
    for i in range(1, 15):
        generated.append(f"({'a' * i}|b)*c")
        generated.append(f"({'x' * (i % 3 + 1)})*y{'z' * (i % 2 + 1)}")
        generated.append(f"(a|b){'c' * (i % 3 + 1)}(d|e)")
        generated.append(f"({'0' * (i % 2 + 1)}|1)*0{'1' * (i % 3 + 1)}")

    # Polynomial patterns
    for sym in ["a", "b", "c", "x", "y", "0", "1"]:
        generated.append(f"{sym}*{sym}*z")
        generated.append(f"{sym}+{sym}+w")
        generated.append(f"({sym}|d)*{sym}*({sym}|d)*e")
        generated.append(f"{sym}*{sym}*{sym}*k")

    # Exponential patterns
    for sym in ["a", "b", "c", "x", "y", "0", "1"]:
        generated.append(f"({sym}+)+")
        generated.append(f"({sym}*)*z")
        generated.append(f"({sym}|{sym}{sym})+")
        generated.append(f"(({sym}+)+)+")
        generated.append(f"({sym}|{sym}+)+k")
        generated.append(f"({sym}+)*")

    return list(dict.fromkeys(generated))  # deduplicate preserving order


def build_redos_dataset(limit: int = 180) -> List[Dict[str, Any]]:
    """
    Builds and labels dataset using the exact AmbiguityAnalyzer.

    Returns:
        List of dicts: {'regex': str, 'label': int, 'risk_class': str}
    """
    all_patterns = list(dict.fromkeys(CURATED_REGEXES + generate_parametric_regexes()))
    analyzer = AmbiguityAnalyzer(timeout_sec=2.0)

    dataset: List[Dict[str, Any]] = []

    for pattern in all_patterns:
        if len(dataset) >= limit:
            break
        try:
            res = analyzer.analyze(pattern)
            label = RISK_CLASS_TO_IDX[res.risk_class.value]
            dataset.append(
                {
                    "regex": pattern,
                    "label": label,
                    "risk_class": res.risk_class.value,
                    "offending_states": res.offending_states,
                }
            )
        except Exception:
            continue

    return dataset

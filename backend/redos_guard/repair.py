"""
ReDoS Guard — Rule-Based Repair & Equivalence Verification (Part 6)
===================================================================
Suggests language-preserving rewrites for ambiguous regular expressions
(collapsing nested quantifiers, deduplicating overlapping alternations,
and merging chained repetitions) and rigorously verifies that:
  1. The repaired regex has an isomorphic / language-equivalent minimized DFA.
  2. The repaired regex is classified as strictly LINEAR (safe) by the AmbiguityAnalyzer.

Rejects unsupported non-regular features (lookaheads, lookbehinds, backreferences)
with informative diagnostic messages.
"""

import re
from typing import Dict, List, Tuple, Optional, Any, Set
from pydantic import BaseModel, Field

from backend.automata_engine.engine import AutomataEngine
from backend.automata_engine.models import Automaton
from backend.redos_guard.analyzer import AmbiguityAnalyzer, AmbiguityRisk


class ReDoSRepairResult(BaseModel):
    success: bool = Field(..., description="True if a safe language-equivalent repair was verified")
    original_regex: str = Field(..., description="Original input regex")
    repaired_regex: Optional[str] = Field(None, description="Repaired regular expression")
    equivalence_verified: bool = Field(False, description="True if minimized DFAs are verified language-equivalent")
    repair_technique: Optional[str] = Field(None, description="Name of rule-based rewrite applied")
    explanation: str = Field("", description="Diagnostic summary of repair or failure reason")
    error: Optional[str] = Field(None, description="Error detail if unsupported feature or invalid regex")


def check_unsupported_features(regex: str) -> Optional[str]:
    """
    Checks for non-regular constructs (lookaheads, lookbehinds, backreferences)
    that cannot be represented in finite automata.
    """
    # Backreferences: \1..\9 or (?P=name)
    if re.search(r"\\[1-9]", regex) or re.search(r"\(\?P=\w+\)", regex):
        return (
            "Unsupported regex feature: Backreferences are not regular languages "
            "and cannot be represented in finite automata or verified for DFA equivalence."
        )

    # Positive/negative lookahead: (?= or (?!
    if "(?=" in regex or "(?!" in regex:
        return (
            "Unsupported regex feature: Lookahead assertions are not supported by the "
            "formal automata theory engine."
        )

    # Positive/negative lookbehind: (?<= or (?<!
    if "(?<=" in regex or "(?<!" in regex:
        return (
            "Unsupported regex feature: Lookbehind assertions are not supported by the "
            "formal automata theory engine."
        )

    # Conditionals: (?(
    if "(?(" in regex:
        return "Unsupported regex feature: Conditional patterns are not supported."

    return None


def are_dfas_equivalent(dfa1: Automaton, dfa2: Automaton) -> Tuple[bool, Optional[str]]:
    """
    Verifies language equivalence between two DFAs using product graph exploration
    (symmetric difference emptiness check).
    """
    alphabet = sorted(list(set(dfa1.alphabet) | set(dfa2.alphabet)))

    delta1: Dict[Tuple[str, str], str] = {
        (t.from_state, t.symbol): t.to_state for t in dfa1.transitions
    }
    delta2: Dict[Tuple[str, str], str] = {
        (t.from_state, t.symbol): t.to_state for t in dfa2.transitions
    }
    accept1 = {s.id for s in dfa1.states if s.is_accepting}
    accept2 = {s.id for s in dfa2.states if s.is_accepting}

    visited: Set[Tuple[str, str]] = set()
    queue: List[Tuple[str, str, str]] = [(dfa1.start_state, dfa2.start_state, "")]

    while queue:
        s1, s2, path = queue.pop(0)
        pair = (s1, s2)
        if pair in visited:
            continue
        visited.add(pair)

        is_acc1 = (s1 in accept1) if s1 != "DEAD" else False
        is_acc2 = (s2 in accept2) if s2 != "DEAD" else False

        if is_acc1 != is_acc2:
            witness = f"'{path}'" if path else "empty string ε"
            return (
                False,
                f"Languages differ on input {witness}: accepted by {'original' if is_acc1 else 'repaired'}, rejected by {'repaired' if is_acc1 else 'original'}",
            )

        for sym in alphabet:
            n1 = delta1.get((s1, sym), "DEAD") if s1 != "DEAD" else "DEAD"
            n2 = delta2.get((s2, sym), "DEAD") if s2 != "DEAD" else "DEAD"
            if (n1, n2) not in visited:
                queue.append((n1, n2, path + sym))

    return True, None


class ReDoSRepairEngine:
    """
    Automated repair engine for ambiguous regular expressions.
    """

    def __init__(self):
        self._engine = AutomataEngine()
        self._analyzer = AmbiguityAnalyzer(timeout_sec=2.0)

    def repair(self, regex: str) -> ReDoSRepairResult:
        """
        Attempts to find a safe, language-equivalent repair for the input regex.
        """
        # 1. Validate supported syntax
        unsupported_err = check_unsupported_features(regex)
        if unsupported_err:
            return ReDoSRepairResult(
                success=False,
                original_regex=regex,
                error=unsupported_err,
                explanation=unsupported_err,
            )

        # 2. Check if original regex compiles
        try:
            orig_bundle = self._engine.build_all(regex)
            orig_min_dfa = orig_bundle["minimized_dfa"]
        except Exception as e:
            return ReDoSRepairResult(
                success=False,
                original_regex=regex,
                error=f"Regex syntax error in original pattern: {e}",
                explanation="Failed to parse regular expression into finite automaton.",
            )

        # 3. Check if already linear
        orig_analysis = self._analyzer.analyze(orig_bundle["nfa"])
        if orig_analysis.risk_class == AmbiguityRisk.LINEAR:
            return ReDoSRepairResult(
                success=True,
                original_regex=regex,
                repaired_regex=regex,
                equivalence_verified=True,
                repair_technique="no_op",
                explanation="Regex is already linear; no repair needed.",
            )

        # 4. Generate candidate rewrites
        candidates = self._generate_candidates(regex)

        # 5. Verify candidates for language equivalence and linear ambiguity
        for cand, technique in candidates:
            if cand == regex:
                continue
            try:
                cand_bundle = self._engine.build_all(cand)
                cand_min_dfa = cand_bundle["minimized_dfa"]

                # Language equivalence verification
                is_equiv, diff_reason = are_dfas_equivalent(orig_min_dfa, cand_min_dfa)
                if not is_equiv:
                    continue

                # Ambiguity verification: repaired regex must be LINEAR
                cand_analysis = self._analyzer.analyze(cand_bundle["nfa"])
                if cand_analysis.risk_class == AmbiguityRisk.LINEAR:
                    return ReDoSRepairResult(
                        success=True,
                        original_regex=regex,
                        repaired_regex=cand,
                        equivalence_verified=True,
                        repair_technique=technique,
                        explanation=(
                            f"Applied {technique}: rewrote '{regex}' to '{cand}'. "
                            f"Minimized DFA language equivalence mathematically verified; "
                            f"ambiguity reduced from {orig_analysis.risk_class.value.upper()} to LINEAR."
                        ),
                    )
            except Exception:
                continue

        return ReDoSRepairResult(
            success=False,
            original_regex=regex,
            repaired_regex=None,
            equivalence_verified=False,
            explanation=(
                f"No safe, language-equivalent repair could be automatically synthesized for '{regex}'. "
                f"Structural restructuring or possessive matching may be required."
            ),
        )

    def _generate_candidates(self, regex: str) -> List[Tuple[str, str]]:
        """Generates candidate rule-based rewrites."""
        candidates: List[Tuple[str, str]] = []

        # Rule 1: Collapse nested plus: (R+)+ -> R+ or (R)+
        # Handles patterns like (a+)+, ((a+)+)+, (a+)+$
        cand1 = re.sub(r"\(([a-zA-Z0-9_]+)\+\)\+", r"\1+", regex)
        if cand1 != regex:
            candidates.append((cand1, "collapse_nested_plus"))

        cand1_paren = re.sub(r"\((.+?)\+\)\+", r"(\1)+", regex)
        if cand1_paren != regex and cand1_paren != cand1:
            candidates.append((cand1_paren, "collapse_nested_plus"))

        # Rule 2: Collapse nested star: (R*)* -> R*
        cand2 = re.sub(r"\(([a-zA-Z0-9_]+)\*\)\*", r"\1*", regex)
        if cand2 != regex:
            candidates.append((cand2, "collapse_nested_star"))

        cand2_paren = re.sub(r"\((.+?)\*\)\*", r"(\1)*", regex)
        if cand2_paren != regex and cand2_paren != cand2:
            candidates.append((cand2_paren, "collapse_nested_star"))

        # Rule 3: Collapse star-plus mix: (R+)* -> R*, (R*)+ -> R*
        cand3a = re.sub(r"\(([a-zA-Z0-9_]+)\+\)\*", r"\1*", regex)
        if cand3a != regex:
            candidates.append((cand3a, "collapse_mixed_quantifier"))

        cand3b = re.sub(r"\(([a-zA-Z0-9_]+)\*\)\+", r"\1*", regex)
        if cand3b != regex:
            candidates.append((cand3b, "collapse_mixed_quantifier"))

        # Rule 4: Deduplicate overlapping alternations: (a|aa)+ -> a+ or (a|a)+ -> a+
        def _repl_overlapping_alt(m):
            branches = m.group(1).split("|")
            # If all branches are repeated sequences of the same base char (e.g. 'a', 'aa', 'aaa')
            chars = {c for b in branches for c in b}
            if len(chars) == 1:
                base_char = next(iter(chars))
                return f"{base_char}+"
            return m.group(0)

        cand4 = re.sub(r"\(([a-zA-Z0-9_|]+)\)\+", _repl_overlapping_alt, regex)
        if cand4 != regex:
            candidates.append((cand4, "dedupe_overlapping_alternation"))

        # Rule 5: Deduplicate overlapping alternations with star: (a|aa)* -> a*
        def _repl_overlapping_alt_star(m):
            branches = m.group(1).split("|")
            chars = {c for b in branches for c in b}
            if len(chars) == 1:
                base_char = next(iter(chars))
                return f"{base_char}*"
            return m.group(0)

        cand5 = re.sub(r"\(([a-zA-Z0-9_|]+)\)\*", _repl_overlapping_alt_star, regex)
        if cand5 != regex:
            candidates.append((cand5, "dedupe_overlapping_alternation"))

        # Rule 6: Merge chained repetitions: a*a*b -> a*b, x*x*y -> x*y
        cand6 = re.sub(r"([a-zA-Z0-9_])\*\1\*", r"\1*", regex)
        if cand6 != regex:
            candidates.append((cand6, "merge_chained_repetitions"))

        # Rule 7: Clean redundant duplicate alternations: (a|a) -> a
        def _repl_dup_alt(m):
            branches = list(dict.fromkeys(m.group(1).split("|")))
            return "|".join(branches)

        cand7 = re.sub(r"\(([a-zA-Z0-9_|]+)\)", _repl_dup_alt, regex)
        if cand7 != regex:
            candidates.append((cand7, "dedupe_identical_alternation"))

        return candidates

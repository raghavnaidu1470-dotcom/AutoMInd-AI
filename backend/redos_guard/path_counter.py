"""
Independent Path-Counting Ambiguity Checker
==========================================
Provides an independent ground-truth verification of NFA ambiguity for small NFAs
by counting the maximum number of accepting paths for all strings up to length N
via Dynamic Programming (DP), and fitting the empirical path growth curve
(Constant/Linear, Polynomial, Exponential).

Theory:
  Weber & Seidl (1991), "On the degree of ambiguity of finite automata":
  da_A(k) = max_{w in Sigma^k} amb_A(w).
  - da_A(k) is bounded by constant  => Linear / Finite ambiguity
  - da_A(k) = Theta(k^d), d >= 1     => Polynomial ambiguity of degree d
  - da_A(k) = 2^{Omega(k)}           => Exponential ambiguity
"""

from collections import defaultdict
from typing import List, Dict, Set, Tuple, Optional, Any
from backend.automata_engine.models import Automaton
from backend.automata_engine.engine import AutomataEngine
from backend.redos_guard.analyzer import AmbiguityRisk


def compute_max_accepting_paths(nfa: Automaton, max_len: int = 6) -> List[int]:
    """
    Computes M_k = max_{w in Sigma^k} paths(w) for k in [0..max_len]
    using dynamic programming over string prefixes.

    Args:
        nfa: Automaton instance under test.
        max_len: Maximum input length to evaluate (default 6).

    Returns:
        List[int] where index k is M_k.
    """
    states = [s.id for s in nfa.states]
    eps_adj: Dict[str, Set[str]] = defaultdict(set)
    sym_adj: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

    for t in nfa.transitions:
        if t.symbol in ("ε", ""):
            eps_adj[t.from_state].add(t.to_state)
        else:
            sym_adj[t.from_state][t.symbol].append(t.to_state)

    def get_eps_paths(src: str) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        counts[src] = 1
        stack = [(src, [src])]
        while stack:
            curr, path = stack.pop()
            for nxt in eps_adj.get(curr, set()):
                if nxt not in path:
                    counts[nxt] += 1
                    stack.append((nxt, path + [nxt]))
        return counts

    eps_map = {s: get_eps_paths(s) for s in states}
    accepts = {s.id for s in nfa.states if s.is_accepting}
    start = nfa.start_state
    alphabet = sorted(list(set(nfa.alphabet) - {"ε", ""}))

    if not alphabet:
        alphabet = ["a"]

    # Limit alphabet size to prevent combinatorial explosion on huge alphabets
    # for path-counting (take representatives)
    eval_alphabet = alphabet[:4]

    max_paths: List[int] = []
    curr_words: Dict[str, Dict[str, int]] = {"": eps_map[start]}

    k0_acc = sum(curr_words[""].get(acc, 0) for acc in accepts)
    max_paths.append(k0_acc)

    for k in range(1, max_len + 1):
        next_words: Dict[str, Dict[str, int]] = {}
        for w, s_counts in curr_words.items():
            for char in eval_alphabet:
                nw = w + char
                new_s: Dict[str, int] = defaultdict(int)
                for u, c in s_counts.items():
                    if c == 0:
                        continue
                    for t in sym_adj[u].get(char, []):
                        for dst, p_cnt in eps_map[t].items():
                            new_s[dst] += c * p_cnt
                if any(new_s.values()):
                    next_words[nw] = new_s

        curr_words = next_words
        if not curr_words:
            max_paths.append(0)
            continue

        k_max = max(
            sum(counts.get(acc, 0) for acc in accepts) for counts in curr_words.values()
        )
        max_paths.append(k_max)

    return max_paths


def fit_path_growth(max_paths: List[int]) -> AmbiguityRisk:
    """
    Fits constant, polynomial, or exponential growth curves to the sequence
    of maximum accepting path counts M_k across k=0..N.

    Args:
        max_paths: List of M_k values for k=0..N.

    Returns:
        AmbiguityRisk: LINEAR, POLYNOMIAL, or EXPONENTIAL.
    """
    non_zero = [v for v in max_paths if v > 0]
    if not non_zero:
        return AmbiguityRisk.LINEAR

    max_val = max(max_paths)
    if max_val <= 2:
        return AmbiguityRisk.LINEAR

    ratios: List[float] = []
    for i in range(1, len(max_paths)):
        if max_paths[i - 1] > 0 and max_paths[i] > 0:
            ratios.append(max_paths[i] / max_paths[i - 1])

    if len(ratios) >= 2 and ratios[-1] >= 1.55 and max_val >= 8:
        return AmbiguityRisk.EXPONENTIAL

    if max_val >= 3:
        return AmbiguityRisk.POLYNOMIAL

    return AmbiguityRisk.LINEAR

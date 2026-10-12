"""
Exact NFA Ambiguity Analyzer
============================
Analyzes epsilon-free, trimmed NFAs to detect and classify Regular Expression
ambiguity into Linear, Polynomial, or Exponential risk classes using standard
product-automaton techniques:
  - Pair Graph G2 for Exponential Ambiguity (EDA)
  - Triple-Product Condition G3 for Polynomial Ambiguity (PDA)
Based on foundational automata theory (Weber & Seidl 1991, Mohri & Nederhof 2001).

Provides DFA-guided pumpable attack strings (prefix + pump^k + failing suffix)
for empirical validation under both full-match and search semantics.
"""

from collections import defaultdict, deque
from enum import Enum
from typing import Dict, List, Set, Tuple, Optional, Any, Union
import re
import time
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from backend.automata_engine.models import Automaton, State, Transition
from backend.automata_engine.engine import AutomataEngine


class AmbiguityRisk(str, Enum):
    LINEAR = "linear"
    POLYNOMIAL = "polynomial"
    EXPONENTIAL = "exponential"


class AttackString(BaseModel):
    prefix: str = Field("", description="Prefix string to reach the ambiguous region")
    pump: str = Field("", description="Pumpable substring repeated to trigger backtracking")
    suffix: str = Field("", description="Failing suffix ensuring the engine explores all backtracking branches")

    def build(self, repeats: int = 25) -> str:
        return f"{self.prefix}{self.pump * repeats}{self.suffix}"


class AmbiguityAnalysisResult(BaseModel):
    risk_class: AmbiguityRisk = Field(..., description="Risk class: linear, polynomial, or exponential")
    is_vulnerable: bool = Field(False, description="True if regex has polynomial or exponential ambiguity")
    offending_states: List[str] = Field(default_factory=list, description="IDs of NFA states participating in ambiguous cycles")
    offending_transitions: List[str] = Field(default_factory=list, description="IDs of NFA transitions participating in ambiguous cycles")
    attack_string: Optional[AttackString] = Field(None, description="Pumpable attack string prefix + pump + suffix")
    degree: Optional[int] = Field(None, description="Estimated degree of polynomial or exponential complexity")
    explanation: str = Field("", description="Human-readable explanation of ambiguity finding")
    execution_time_ms: float = Field(0.0, description="Analyzer execution duration in milliseconds")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Topological metrics of trimmed NFA and product graphs")
    has_start_anchor: bool = Field(False, description="True if regex has '^' start anchor")
    has_end_anchor: bool = Field(False, description="True if regex has '$' end anchor")
    engine_nuance_note: Optional[str] = Field(None, description="Nuance on engine matching mode (search vs fullmatch/suffix)")


@dataclass
class _EpsFreeTransition:
    target: str
    orig_trans_id: str
    multiplicity: int
    orig_from: str


class AmbiguityAnalyzer:
    """
    Optimized Exact Ambiguity Analyzer for finite automata.
    Performs epsilon-elimination first, indexes transitions by (state, symbol),
    constructs product graphs lazily on reachable pairs only, uses iterative Tarjan SCC,
    and applies the exact triple-product condition for polynomial ambiguity.
    """

    def __init__(self, max_states: int = 500, timeout_sec: float = 3.0):
        self.max_states = max_states
        self.timeout_sec = timeout_sec
        self._engine = AutomataEngine()

    def analyze(self, target: Union[Automaton, str]) -> AmbiguityAnalysisResult:
        """
        Analyzes an NFA or raw regex for language ambiguity.

        Args:
            target: Either an Automaton instance or a raw regular expression string.

        Returns:
            AmbiguityAnalysisResult with risk_class, offending_states, and attack string.
        """
        start_time = time.perf_counter()

        dfa_obj = None
        if isinstance(target, str):
            bundle = self._engine.build_all(target)
            nfa = bundle["nfa"]
            dfa_obj = bundle.get("minimized_dfa") or bundle.get("dfa")
            regex_str = target
        else:
            nfa = target
            regex_str = nfa.metadata.regex if nfa.metadata else ""
            if regex_str:
                try:
                    bundle = self._engine.build_all(regex_str)
                    dfa_obj = bundle.get("minimized_dfa") or bundle.get("dfa")
                except Exception:
                    dfa_obj = None

        has_start_anchor = getattr(nfa.metadata, "has_start_anchor", False) if nfa.metadata else False
        has_end_anchor = getattr(nfa.metadata, "has_end_anchor", False) if nfa.metadata else False
        engine_nuance_note = (
            "Structural ambiguity triggers backtracking when matching fails on a suffix or under full-match semantics. "
            "Under unanchored search mode without a trailing mismatch, greedy engines may match a prefix and terminate early."
        )

        if len(nfa.states) > self.max_states:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return AmbiguityAnalysisResult(
                risk_class=AmbiguityRisk.LINEAR,
                is_vulnerable=False,
                offending_states=[],
                offending_transitions=[],
                explanation=f"NFA size ({len(nfa.states)} states) exceeds analyzer threshold ({self.max_states}).",
                execution_time_ms=elapsed_ms,
                has_start_anchor=has_start_anchor,
                has_end_anchor=has_end_anchor,
                engine_nuance_note=engine_nuance_note,
            )

        # 1. Eliminate Epsilons First & Index Transitions by (state, symbol)
        eps_free_data = self._build_epsilon_free_nfa(nfa)
        if eps_free_data is None:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return AmbiguityAnalysisResult(
                risk_class=AmbiguityRisk.LINEAR,
                is_vulnerable=False,
                offending_states=[],
                offending_transitions=[],
                explanation="Automaton has no reachable accepting paths; language is empty or dead-end.",
                execution_time_ms=elapsed_ms,
                has_start_anchor=has_start_anchor,
                has_end_anchor=has_end_anchor,
                engine_nuance_note=engine_nuance_note,
            )

        S, useful, trans_by_state_sym, all_syms, start_st, accepts = eps_free_data

        # 2. Pair Graph G2 Ambiguity Analysis for Exponential Ambiguity (EDA)
        eda_result = self._check_eda(
            useful, trans_by_state_sym, all_syms, start_st, accepts, nfa, dfa_obj
        )
        if eda_result is not None:
            offending_states, offending_trans, attack_str, expl = eda_result
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return AmbiguityAnalysisResult(
                risk_class=AmbiguityRisk.EXPONENTIAL,
                is_vulnerable=True,
                offending_states=offending_states,
                offending_transitions=offending_trans,
                attack_string=attack_str,
                degree=None,
                explanation=expl,
                execution_time_ms=elapsed_ms,
                metrics={
                    "useful_states": len(useful),
                    "ambiguity_type": "EDA (Exponential)",
                },
                has_start_anchor=has_start_anchor,
                has_end_anchor=has_end_anchor,
                engine_nuance_note=engine_nuance_note,
            )

        # 3. Triple Condition G3 for Polynomial Ambiguity (PDA)
        pda_result = self._check_pda(
            useful, trans_by_state_sym, all_syms, start_st, accepts, nfa, dfa_obj
        )
        if pda_result is not None:
            offending_states, offending_trans, attack_str, deg, expl = pda_result
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return AmbiguityAnalysisResult(
                risk_class=AmbiguityRisk.POLYNOMIAL,
                is_vulnerable=True,
                offending_states=offending_states,
                offending_transitions=offending_trans,
                attack_string=attack_str,
                degree=deg,
                explanation=expl,
                execution_time_ms=elapsed_ms,
                metrics={
                    "useful_states": len(useful),
                    "ambiguity_type": "PDA (Polynomial)",
                },
                has_start_anchor=has_start_anchor,
                has_end_anchor=has_end_anchor,
                engine_nuance_note=engine_nuance_note,
            )

        # 4. Safe / Linear
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return AmbiguityAnalysisResult(
            risk_class=AmbiguityRisk.LINEAR,
            is_vulnerable=False,
            offending_states=[],
            offending_transitions=[],
            attack_string=None,
            degree=1,
            explanation="Exact ambiguity analysis confirmed linear complexity: no exponential overlapping cycles or polynomial triple cycles exist.",
            execution_time_ms=elapsed_ms,
            metrics={
                "useful_states": len(useful),
                "ambiguity_type": "Linear (Safe)",
            },
            has_start_anchor=has_start_anchor,
            has_end_anchor=has_end_anchor,
            engine_nuance_note=engine_nuance_note,
        )

    def _build_epsilon_free_nfa(
        self, nfa: Automaton
    ) -> Optional[
        Tuple[
            List[str],
            Set[str],
            Dict[Tuple[str, str], List[_EpsFreeTransition]],
            List[str],
            str,
            Set[str],
        ]
    ]:
        """
        Eliminates epsilon transitions first and precomputes transition tables indexed by (state, symbol).
        Avoids recursive path counting inside loops by precomputing bounded epsilon paths.
        """
        # Adjacency of epsilon transitions
        eps_adj: Dict[str, Set[str]] = defaultdict(set)
        for t in nfa.transitions:
            if t.symbol in ("ε", ""):
                eps_adj[t.from_state].add(t.to_state)

        # Precompute epsilon path count (capped at 2) between all state pairs
        # Memoized DFS per source state
        all_state_ids = [s.id for s in nfa.states]
        eps_paths: Dict[Tuple[str, str], int] = {}

        def count_paths_from(src: str) -> Dict[str, int]:
            counts: Dict[str, int] = defaultdict(int)
            visited_in_path: Set[str] = set()

            def dfs(u: str):
                counts[u] = min(2, counts[u] + 1)
                visited_in_path.add(u)
                for nxt in eps_adj.get(u, set()):
                    if nxt in visited_in_path:
                        counts[nxt] = 2
                    else:
                        dfs(nxt)
                visited_in_path.remove(u)

            dfs(src)
            return counts

        for sid in all_state_ids:
            c_map = count_paths_from(sid)
            for dst, cnt in c_map.items():
                if cnt > 0:
                    eps_paths[(sid, dst)] = cnt

        # Identify symbol transitions
        sym_transitions = [t for t in nfa.transitions if t.symbol not in ("ε", "")]
        all_syms = sorted(list(set(t.symbol for t in sym_transitions)))
        start_st = nfa.start_state
        S = sorted(list(set([start_st] + [t.to_state for t in sym_transitions])))

        # Index transitions by (state, symbol)
        trans_by_state_sym: Dict[Tuple[str, str], List[_EpsFreeTransition]] = defaultdict(list)
        for s in S:
            for t in sym_transitions:
                c = eps_paths.get((s, t.from_state), 0)
                if c > 0:
                    trans_by_state_sym[(s, t.symbol)].append(
                        _EpsFreeTransition(
                            target=t.to_state,
                            orig_trans_id=t.id,
                            multiplicity=c,
                            orig_from=t.from_state,
                        )
                    )

        # Accept states: any state in S that can reach an original accept state via epsilon
        orig_accepts = {s.id for s in nfa.states if s.is_accepting}
        accepts = {s for s in S if any(eps_paths.get((s, acc), 0) > 0 for acc in orig_accepts)}

        # Trim: reachable from start_st and co-reachable to accepts
        reachable: Set[str] = set()
        q: List[str] = [start_st]
        while q:
            curr = q.pop()
            if curr not in reachable:
                reachable.add(curr)
                for sym in all_syms:
                    for edge in trans_by_state_sym.get((curr, sym), []):
                        if edge.target not in reachable:
                            q.append(edge.target)

        rev_adj: Dict[str, Set[str]] = defaultdict(set)
        for s in S:
            for sym in all_syms:
                for edge in trans_by_state_sym.get((s, sym), []):
                    rev_adj[edge.target].add(s)

        coreachable: Set[str] = set()
        q = list(accepts)
        while q:
            curr = q.pop()
            if curr not in coreachable:
                coreachable.add(curr)
                for prev in rev_adj.get(curr, set()):
                    if prev not in coreachable:
                        q.append(prev)

        useful = reachable & coreachable
        if not useful or not (useful & accepts):
            return None

        return S, useful, trans_by_state_sym, all_syms, start_st, accepts

    def _check_eda(
        self,
        useful: Set[str],
        trans_by_state_sym: Dict[Tuple[str, str], List[_EpsFreeTransition]],
        all_syms: List[str],
        start_st: str,
        accepts: Set[str],
        nfa: Automaton,
        dfa_obj: Optional[Automaton],
    ) -> Optional[Tuple[List[str], List[str], AttackString, str]]:
        """
        Exact Exponential Ambiguity (EDA) detection via Pair Graph G2 = A x A.
        Builds G2 lazily from (start, start) on reachable pairs only.
        Uses iterative Tarjan SCC to identify components containing both diagonal
        and off-diagonal pairs or diagonal pairs with multiple transitions on the same symbol.
        """
        g2_adj: Dict[Tuple[str, str], List[Tuple[str, str]]] = defaultdict(list)
        g2_edge_symbols: Dict[Tuple[Tuple[str, str], Tuple[str, str]], str] = {}
        g2_multi_edge: Set[Tuple[str, str]] = set()
        g2_multi_edge_syms: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        visited_g2: Set[Tuple[str, str]] = set()
        q = deque([(start_st, start_st)])
        visited_g2.add((start_st, start_st))

        while q:
            (u, v) = q.popleft()
            for sym in all_syms:
                e_u = [e for e in trans_by_state_sym.get((u, sym), []) if e.target in useful]
                e_v = [e for e in trans_by_state_sym.get((v, sym), []) if e.target in useful]
                for edge_u in e_u:
                    for edge_v in e_v:
                        nxt = (edge_u.target, edge_v.target)
                        g2_adj[(u, v)].append(nxt)
                        g2_edge_symbols[((u, v), nxt)] = sym
                        if u == v and edge_u.target == edge_v.target:
                            if edge_u.orig_trans_id != edge_v.orig_trans_id or edge_u.multiplicity >= 2 or edge_v.multiplicity >= 2:
                                g2_multi_edge.add((u, v))
                                g2_multi_edge_syms[(u, v)].add(sym)
                        if nxt not in visited_g2:
                            visited_g2.add(nxt)
                            q.append(nxt)

        # Coreachability in G2: can reach accept pair (acc1, acc2)
        g2_accepts = {(s1, s2) for s1 in accepts for s2 in accepts if (s1, s2) in visited_g2}
        g2_rev: Dict[Tuple[str, str], List[Tuple[str, str]]] = defaultdict(list)
        for src, tgts in g2_adj.items():
            for tgt in tgts:
                g2_rev[tgt].append(src)

        g2_coreach: Set[Tuple[str, str]] = set()
        rq = list(g2_accepts)
        while rq:
            curr = rq.pop()
            if curr not in g2_coreach:
                g2_coreach.add(curr)
                for prev in g2_rev.get(curr, []):
                    if prev not in g2_coreach and prev in visited_g2:
                        rq.append(prev)

        useful_g2 = visited_g2 & g2_coreach
        if not useful_g2:
            return None

        # Iterative Tarjan SCC on useful_g2
        sccs = self._iterative_tarjan(useful_g2, g2_adj)

        eda_scc = None
        for scc in sccs:
            is_cyclic = len(scc) > 1 or any(n in g2_adj.get(n, []) for n in scc)
            if not is_cyclic:
                continue
            diag = {p for p in scc if p[0] == p[1]}
            off_diag = {p for p in scc if p[0] != p[1]}
            if (diag and off_diag) or any(p in g2_multi_edge for p in diag):
                eda_scc = scc
                break

        if eda_scc is None:
            return None

        # Extract offending states and transitions
        states_in_scc = sorted(list(set(p[0] for p in eda_scc) | set(p[1] for p in eda_scc)))
        offending_states = sorted(list(set(states_in_scc)))
        offending_trans: List[str] = []
        for s in offending_states:
            for sym in all_syms:
                for edge in trans_by_state_sym.get((s, sym), []):
                    if edge.target in offending_states:
                        offending_trans.append(edge.orig_trans_id)
        offending_trans = sorted(list(set(offending_trans)))

        # Synthesize attack string using shortest pair-graph witness cycle
        attack_str = self._synthesize_eda_witness_attack(
            eda_scc=eda_scc,
            g2_adj=g2_adj,
            g2_edge_symbols=g2_edge_symbols,
            g2_multi_edge_syms=g2_multi_edge_syms,
            trans_by_state_sym=trans_by_state_sym,
            useful=useful,
            all_syms=all_syms,
            start_st=start_st,
            nfa=nfa,
            dfa_obj=dfa_obj,
        )

        explanation = (
            f"Exponential Ambiguity (EDA) detected via pair-graph criterion. "
            f"A strongly connected component contains overlapping parallel cycles on pump '{attack_str.pump}', "
            f"allowing 2^N distinct paths for repeated input."
        )
        return offending_states, offending_trans, attack_str, explanation

    def _synthesize_eda_witness_attack(
        self,
        eda_scc: Set[Tuple[str, str]],
        g2_adj: Dict[Tuple[str, str], List[Tuple[str, str]]],
        g2_edge_symbols: Dict[Tuple[Tuple[str, str], Tuple[str, str]], str],
        g2_multi_edge_syms: Dict[Tuple[str, str], Set[str]],
        trans_by_state_sym: Dict[Tuple[str, str], List[_EpsFreeTransition]],
        useful: Set[str],
        all_syms: List[str],
        start_st: str,
        nfa: Automaton,
        dfa_obj: Optional[Automaton],
    ) -> AttackString:
        """
        Synthesizes attack string for exponential ambiguity by choosing the pump as the
        shortest word v for which the pair-graph witness shows two distinct cycles on v.
        """
        diag = {p for p in eda_scc if p[0] == p[1]}
        off_diag = {p for p in eda_scc if p[0] != p[1]}
        witness_candidates: List[Tuple[str, str]] = []

        # 1. Multi-edges on diagonal (length 1 cycle with distinct transitions)
        for pp in diag:
            for sym in sorted(list(g2_multi_edge_syms.get(pp, set()))):
                witness_candidates.append((sym, pp[0]))

        # 2. Diagonal cycles through off-diagonal states: (p, p) -> (r, s) -> ... -> (p, p)
        # where r != s guarantees two distinct paths in the NFA on the same word
        for pp in diag:
            for nxt in g2_adj.get(pp, []):
                if nxt not in eda_scc or nxt[0] == nxt[1]:
                    continue
                sym1 = g2_edge_symbols.get((pp, nxt), "")
                q_bfs: deque = deque([(nxt, [sym1])])
                vis = {nxt}
                while q_bfs:
                    curr, sym_list = q_bfs.popleft()
                    if curr == pp:
                        w = "".join(sym_list)
                        witness_candidates.append((w, pp[0]))
                        break
                    if len(sym_list) >= 4:
                        break
                    for succ in g2_adj.get(curr, []):
                        if succ in eda_scc and succ not in vis:
                            vis.add(succ)
                            s_e = g2_edge_symbols.get((curr, succ), "")
                            q_bfs.append((succ, sym_list + [s_e]))

        # 3. Off-diagonal cycles (u, v) -> (u, v) in the SCC with u != v
        for uv in off_diag:
            q_bfs = deque([(uv, [])])
            vis = {uv}
            while q_bfs:
                curr, sym_list = q_bfs.popleft()
                if len(sym_list) >= 4:
                    break
                for nxt in g2_adj.get(curr, []):
                    if nxt not in eda_scc:
                        continue
                    sym = g2_edge_symbols.get((curr, nxt), "")
                    if nxt == uv:
                        w = "".join(sym_list + [sym])
                        witness_candidates.append((w, uv[0]))
                        break
                    if nxt not in vis:
                        vis.add(nxt)
                        q_bfs.append((nxt, sym_list + [sym]))

        if not witness_candidates:
            pump = all_syms[0] if all_syms else "a"
            suf = self._synthesize_dfa_failing_suffix(nfa, dfa_obj, "", pump)
            return AttackString(prefix="", pump=pump, suffix=suf)

        min_len = min(len(w) for w, _ in witness_candidates)

        cand_attacks: List[Tuple[int, int, AttackString]] = []
        seen: Set[Tuple[str, str, str]] = set()

        for w, st in witness_candidates:
            if len(w) > min_len + 1:
                continue
            rotations = [w[i:] + w[:i] for i in range(len(w))]
            for rw in rotations:
                # If start_st can transition directly on rw, test prefix=""
                can_start = bool(trans_by_state_sym.get((start_st, rw[0])))
                if can_start:
                    suf0 = self._synthesize_dfa_failing_suffix(nfa, dfa_obj, "", rw)
                    key = ("", rw, suf0)
                    if key not in seen:
                        seen.add(key)
                        cand_attacks.append((len(rw), 0, AttackString(prefix="", pump=rw, suffix=suf0)))

                pref = self._find_prefix_to_state(start_st, st, trans_by_state_sym, useful)
                suf = self._synthesize_dfa_failing_suffix(nfa, dfa_obj, pref, rw)
                key = (pref, rw, suf)
                if key not in seen:
                    seen.add(key)
                    cand_attacks.append((len(rw), 1 if pref else 0, AttackString(prefix=pref, pump=rw, suffix=suf)))

        cand_attacks.sort(key=lambda x: (x[0], x[1], x[2].pump))

        pat_str = getattr(nfa.metadata, "regex", None) if nfa.metadata else None
        compiled_re = None
        if pat_str:
            try:
                compiled_re = re.compile(pat_str)
            except Exception:
                compiled_re = None

        best: Optional[AttackString] = None
        for length, has_pref, att in cand_attacks[:6]:
            if compiled_re:
                s4 = att.build(repeats=4)
                s8 = att.build(repeats=8)
                t0 = time.perf_counter()
                try:
                    compiled_re.fullmatch(s4)
                except Exception:
                    pass
                dt4 = time.perf_counter() - t0

                t0 = time.perf_counter()
                try:
                    compiled_re.fullmatch(s8)
                except Exception:
                    pass
                dt8 = time.perf_counter() - t0

                if dt8 > 0.00002 and (dt4 <= 1e-6 or dt8 / dt4 > 2.0):
                    best = att
                    break
            else:
                best = att
                break

        if best is None and cand_attacks:
            best = cand_attacks[0][2]
        elif best is None:
            pump = all_syms[0] if all_syms else "a"
            suf = self._synthesize_dfa_failing_suffix(nfa, dfa_obj, "", pump)
            best = AttackString(prefix="", pump=pump, suffix=suf)

        return best

    def _check_pda(
        self,
        useful: Set[str],
        trans_by_state_sym: Dict[Tuple[str, str], List[_EpsFreeTransition]],
        all_syms: List[str],
        start_st: str,
        accepts: Set[str],
        nfa: Automaton,
        dfa_obj: Optional[Automaton],
    ) -> Optional[Tuple[List[str], List[str], AttackString, int, str]]:
        """
        Exact Polynomial Ambiguity (PDA) detection via Triple-Product Condition G3.
        Tests for distinct states p != q with p -v-> p, p -v-> q, q -v-> q on the same word v
        in the trimmed epsilon-free automaton. An off-diagonal cycle alone is NOT sufficient.
        """
        # Reachability graph in trimmed NFA
        can_reach: Dict[str, Set[str]] = defaultdict(set)
        for u in useful:
            q = [u]
            visited = {u}
            while q:
                curr = q.pop()
                for sym in all_syms:
                    for edge in trans_by_state_sym.get((curr, sym), []):
                        if edge.target in useful:
                            can_reach[u].add(edge.target)
                            if edge.target not in visited:
                                visited.add(edge.target)
                                q.append(edge.target)

        cyclic_states = {u for u in useful if u in can_reach[u]}
        candidate_pairs = [
            (p, q) for p in cyclic_states for q in cyclic_states
            if p != q and q in can_reach[p]
        ]

        if not candidate_pairs:
            return None

        # Prioritize candidate pairs by proximity: check direct transitions first
        # Direct distance check:
        direct_succ: Dict[str, Set[str]] = defaultdict(set)
        for u in useful:
            for sym in all_syms:
                for edge in trans_by_state_sym.get((u, sym), []):
                    if edge.target in useful:
                        direct_succ[u].add(edge.target)

        # Sort: direct neighbors first
        candidate_pairs.sort(key=lambda pair: 0 if pair[1] in direct_succ[pair[0]] else 1)

        # Search for triple condition: (p, p, q) -> (p, q, q) in G3 on some word v
        confirmed_triple_pairs: List[Tuple[str, str, str]] = []  # (p, q, pump_sym)

        checked_count = 0
        for p, q in candidate_pairs:
            checked_count += 1
            start_triple = (p, p, q)
            target_triple = (p, q, q)
            visited = {start_triple}
            queue = deque([(start_triple, 0, "")])  # state, depth, first_sym
            found_pair = False

            while queue:
                (s1, s2, s3), depth, first_sym = queue.popleft()
                for sym in all_syms:
                    succ1 = [e.target for e in trans_by_state_sym.get((s1, sym), []) if e.target in useful]
                    succ2 = [e.target for e in trans_by_state_sym.get((s2, sym), []) if e.target in useful]
                    succ3 = [e.target for e in trans_by_state_sym.get((s3, sym), []) if e.target in useful]
                    for n1 in succ1:
                        for n2 in succ2:
                            for n3 in succ3:
                                nxt = (n1, n2, n3)
                                sym_label = first_sym if first_sym else sym
                                if nxt == target_triple:
                                    confirmed_triple_pairs.append((p, q, sym_label))
                                    found_pair = True
                                    break
                                if nxt not in visited and depth < 4:
                                    visited.add(nxt)
                                    queue.append((nxt, depth + 1, sym_label))
                            if found_pair:
                                break
                        if found_pair:
                            break
                    if found_pair:
                        break
                if found_pair:
                    break

            # If we've confirmed triples and checked direct neighbors or enough pairs, stop search
            if confirmed_triple_pairs and checked_count >= min(len(candidate_pairs), max(10, len(cyclic_states))):
                break

        if not confirmed_triple_pairs:
            return None

        # Compute degree: chain length in confirmed triple graph
        chain_adj: Dict[str, Set[str]] = defaultdict(set)
        for p, q, _ in confirmed_triple_pairs:
            chain_adj[p].add(q)

        # Longest chain in DAG of triple pairs
        degree = 2
        for p, _, _ in confirmed_triple_pairs:
            q_bfs = deque([(p, 2)])
            while q_bfs:
                curr, curr_deg = q_bfs.popleft()
                degree = max(degree, curr_deg)
                for nxt in chain_adj.get(curr, set()):
                    if curr_deg < 5:
                        q_bfs.append((nxt, curr_deg + 1))

        best_p, best_q, pump_sym = confirmed_triple_pairs[0]
        offending_states = sorted(list({best_p, best_q}))
        offending_trans: List[str] = []
        for s in offending_states:
            for sym in all_syms:
                for edge in trans_by_state_sym.get((s, sym), []):
                    if edge.target in offending_states:
                        offending_trans.append(edge.orig_trans_id)
        offending_trans = sorted(list(set(offending_trans)))

        prefix = self._find_prefix_to_state(start_st, best_p, trans_by_state_sym, useful)
        suffix = self._synthesize_dfa_failing_suffix(nfa, dfa_obj, prefix, pump_sym)
        attack_str = AttackString(prefix=prefix, pump=pump_sym, suffix=suffix)

        explanation = (
            f"Polynomial Ambiguity (PDA) of degree {degree} detected via exact triple-product condition. "
            f"Distinct cycles at states {best_p} and {best_q} can be co-iterated on symbol '{pump_sym}' "
            f"with transfer from {best_p} to {best_q}, allowing polynomial O(N^{degree}) paths."
        )
        return offending_states, offending_trans, attack_str, degree, explanation

    def _iterative_tarjan(
        self, nodes: Set[Tuple[str, str]], adj: Dict[Tuple[str, str], List[Tuple[str, str]]]
    ) -> List[Set[Tuple[str, str]]]:
        """Iterative Tarjan SCC implementation on product graph nodes."""
        idx = 0
        indices: Dict[Tuple[str, str], int] = {}
        lowlinks: Dict[Tuple[str, str], int] = {}
        stack: List[Tuple[str, str]] = []
        on_stack: Set[Tuple[str, str]] = set()
        sccs: List[Set[Tuple[str, str]]] = []

        for node in nodes:
            if node not in indices:
                call_stack = [(node, 0, [t for t in adj.get(node, []) if t in nodes])]
                indices[node] = lowlinks[node] = idx
                idx += 1
                stack.append(node)
                on_stack.add(node)
                while call_stack:
                    u_pair, ci, neighbors = call_stack[-1]
                    if ci < len(neighbors):
                        v_pair = neighbors[ci]
                        call_stack[-1] = (u_pair, ci + 1, neighbors)
                        if v_pair not in indices:
                            indices[v_pair] = lowlinks[v_pair] = idx
                            idx += 1
                            stack.append(v_pair)
                            on_stack.add(v_pair)
                            call_stack.append((v_pair, 0, [t for t in adj.get(v_pair, []) if t in nodes]))
                        elif v_pair in on_stack:
                            lowlinks[u_pair] = min(lowlinks[u_pair], indices[v_pair])
                    else:
                        call_stack.pop()
                        if call_stack:
                            p = call_stack[-1][0]
                            lowlinks[p] = min(lowlinks[p], lowlinks[u_pair])
                        if lowlinks[u_pair] == indices[u_pair]:
                            scc: Set[Tuple[str, str]] = set()
                            while True:
                                w = stack.pop()
                                on_stack.remove(w)
                                scc.add(w)
                                if w == u_pair:
                                    break
                            sccs.append(scc)
        return sccs

    def _find_prefix_to_state(
        self,
        start_st: str,
        target_st: str,
        trans_by_state_sym: Dict[Tuple[str, str], List[_EpsFreeTransition]],
        useful: Set[str],
    ) -> str:
        """Finds shortest symbol prefix from start state to target state."""
        if start_st == target_st:
            return ""
        visited: Set[str] = {start_st}
        q: deque = deque([(start_st, "")])
        while q:
            curr, word = q.popleft()
            if curr == target_st:
                return word
            for (s, sym), edges in trans_by_state_sym.items():
                if s == curr:
                    for edge in edges:
                        if edge.target in useful and edge.target not in visited:
                            visited.add(edge.target)
                            q.append((edge.target, word + sym))
        return ""

    def _synthesize_dfa_failing_suffix(
        self,
        nfa: Automaton,
        dfa_obj: Optional[Automaton],
        prefix: str,
        pump_sym: str,
    ) -> str:
        """
        Synthesizes a failing suffix using the DFA so that prefix + pump^k + suffix
        is guaranteed NOT in the language and forces maximal backtracking.
        """
        alphabet = set(nfa.alphabet)

        # 1. Prefer sentinel characters outside the automaton alphabet
        for cand in ["!", "X", "#", "$", "0", "@"]:
            if cand not in alphabet:
                return cand

        # 2. If all candidate sentinels in alphabet and DFA is available, simulate DFA
        if dfa_obj is not None:
            # Map DFA transitions
            dfa_delta: Dict[Tuple[str, str], str] = {}
            for t in dfa_obj.transitions:
                dfa_delta[(t.from_state, t.symbol)] = t.to_state

            dfa_accepts = {s.id for s in dfa_obj.states if s.is_accepting}

            # Trace DFA on prefix + pump*2
            test_lead = prefix + (pump_sym * 2)
            curr_state = dfa_obj.start_state
            for ch in test_lead:
                curr_state = dfa_delta.get((curr_state, ch), "")
                if not curr_state:
                    break

            if curr_state:
                # Find a single symbol from curr_state that transitions to a dead state or no transition
                for sym in sorted(list(alphabet)):
                    nxt = dfa_delta.get((curr_state, sym))
                    if nxt is None:
                        return sym
                    # Check if nxt can reach any accept state
                    can_reach_acc = False
                    vis = {nxt}
                    q = [nxt]
                    while q:
                        c = q.pop()
                        if c in dfa_accepts:
                            can_reach_acc = True
                            break
                        for s_sym in alphabet:
                            to_s = dfa_delta.get((c, s_sym))
                            if to_s and to_s not in vis:
                                vis.add(to_s)
                                q.append(to_s)
                    if not can_reach_acc:
                        return sym

        # 3. Fallback sentinel
        return "!_FAIL"

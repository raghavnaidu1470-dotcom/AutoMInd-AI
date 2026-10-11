"""
ReDoS Guard — NFA Graph Feature Extractor
=========================================
Extracts canonical node and edge feature tensors from finite automata for GNN
severity classification and GNNExplainer attribution.
"""

from typing import Dict, List, Set, Tuple, Any
from collections import Counter
import torch

from backend.automata_engine.models import Automaton
from backend.redos_guard.gnn.constants import (
    REDOS_NODE_FEATURE_DIM,
    REDOS_EDGE_FEATURE_DIM,
)


def extract_nfa_graph_features(
    nfa: Automaton,
) -> Dict[str, Any]:
    """
    Transforms an Automaton into PyTorch geometric tensor structures with canonical
    node (dim 8) and edge (dim 4) features.

    Args:
        nfa: Automaton instance (NFA from Thompson's construction).

    Returns:
        Dict containing:
            - 'x': torch.Tensor of shape [num_nodes, 8]
            - 'edge_index': torch.Tensor of shape [2, num_edges]
            - 'edge_attr': torch.Tensor of shape [num_edges, 4]
            - 'node_to_idx': Dict[str, int]
            - 'idx_to_node': List[str]
            - 'edge_to_idx': Dict[str, int]
            - 'idx_to_edge': List[str]
    """
    states = nfa.states
    num_nodes = len(states)
    node_to_idx: Dict[str, int] = {s.id: i for i, s in enumerate(states)}
    idx_to_node: List[str] = [s.id for s in states]

    # Adjacency and degree maps
    adj: Dict[str, Set[str]] = {s.id: set() for s in states}
    in_degrees: Counter = Counter()
    out_degrees: Counter = Counter()
    self_loops: Counter = Counter()
    symbols_by_src: Dict[str, List[str]] = {s.id: [] for s in states}

    for t in nfa.transitions:
        adj[t.from_state].add(t.to_state)
        out_degrees[t.from_state] += 1
        in_degrees[t.to_state] += 1
        if t.from_state == t.to_state:
            self_loops[t.from_state] += 1
        sym = t.symbol if t.symbol not in ("ε", "") else "ε"
        symbols_by_src[t.from_state].append(sym)

    # Tarjan's SCC decomposition
    idx = 0
    indices: Dict[str, int] = {}
    lowlinks: Dict[str, int] = {}
    stack: List[str] = []
    on_stack: Set[str] = set()
    sccs: List[Set[str]] = []

    def strongconnect(v: str):
        nonlocal idx
        indices[v] = lowlinks[v] = idx
        idx += 1
        stack.append(v)
        on_stack.add(v)

        for w in adj.get(v, set()):
            if w not in indices:
                strongconnect(w)
                lowlinks[v] = min(lowlinks[v], lowlinks[w])
            elif w in on_stack:
                lowlinks[v] = min(lowlinks[v], indices[w])

        if lowlinks[v] == indices[v]:
            scc = set()
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.add(w)
                if w == v:
                    break
            sccs.append(scc)

    for s in states:
        if s.id not in indices:
            strongconnect(s.id)

    scc_map: Dict[str, int] = {}
    scc_sizes: Dict[str, int] = {}
    in_cycle: Dict[str, float] = {}

    for comp_idx, comp in enumerate(sccs):
        comp_size = len(comp)
        for nid in comp:
            scc_map[nid] = comp_idx
            scc_sizes[nid] = comp_size
            has_cycle = (comp_size > 1) or (self_loops[nid] > 0)
            in_cycle[nid] = 1.0 if has_cycle else 0.0

    # Build node feature matrix [num_nodes, 8]
    node_features = torch.zeros((num_nodes, REDOS_NODE_FEATURE_DIM), dtype=torch.float32)

    for i, s in enumerate(states):
        nid = s.id
        is_start = 1.0 if s.is_start else 0.0
        is_accepting = 1.0 if s.is_accepting else 0.0
        in_deg = float(in_degrees[nid]) / 5.0
        out_deg = float(out_degrees[nid]) / 5.0
        cyc = in_cycle[nid]
        s_size = float(scc_sizes.get(nid, 1)) / 10.0

        # Max count of outgoing transitions with identical symbol
        sym_counts = Counter(symbols_by_src.get(nid, []))
        shared_sym = (float(max(sym_counts.values())) / 5.0) if sym_counts else 0.0
        s_loops = float(self_loops[nid]) / 2.0

        node_features[i] = torch.tensor(
            [
                is_start,
                is_accepting,
                in_deg,
                out_deg,
                cyc,
                s_size,
                shared_sym,
                s_loops,
            ],
            dtype=torch.float32,
        )

    # Build edge list and edge feature matrix [num_edges, 4]
    edge_src: List[int] = []
    edge_dst: List[int] = []
    edge_features_list: List[List[float]] = []
    idx_to_edge: List[str] = []
    edge_to_idx: Dict[str, int] = {}

    for edge_i, t in enumerate(nfa.transitions):
        u_idx = node_to_idx.get(t.from_state, 0)
        v_idx = node_to_idx.get(t.to_state, 0)
        edge_src.append(u_idx)
        edge_dst.append(v_idx)
        idx_to_edge.append(t.id)
        edge_to_idx[t.id] = edge_i

        is_eps = 1.0 if t.symbol in ("ε", "") else 0.0
        src_scc = scc_map.get(t.from_state, -1)
        dst_scc = scc_map.get(t.to_state, -2)
        is_cyc_edge = (
            1.0
            if (src_scc == dst_scc and in_cycle.get(t.from_state, 0.0) == 1.0)
            else 0.0
        )
        src_scc_sz = float(scc_sizes.get(t.from_state, 1))
        dst_scc_sz = float(scc_sizes.get(t.to_state, 1))

        edge_features_list.append([is_eps, is_cyc_edge, src_scc_sz, dst_scc_sz])

    if edge_src:
        edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
        edge_attr = torch.tensor(edge_features_list, dtype=torch.float32)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0, REDOS_EDGE_FEATURE_DIM), dtype=torch.float32)

    return {
        "x": node_features,
        "edge_index": edge_index,
        "edge_attr": edge_attr,
        "node_to_idx": node_to_idx,
        "idx_to_node": idx_to_node,
        "edge_to_idx": edge_to_idx,
        "idx_to_edge": idx_to_edge,
    }

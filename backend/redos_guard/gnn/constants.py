"""
ReDoS Guard — GNN Feature Constants & Specifications
=====================================================
Defines canonical node and edge feature specifications, dimension constants,
and class mapping for the 3-class ReDoS severity GNN classifier.

Features focus on structural automata properties:
- in_cycle / cycle membership
- SCC size
- Shared-symbol out-degree (non-deterministic branching on identical symbols)
- Self-loop count
"""

from typing import List

# 8 Canonical node features for ReDoS severity screening
REDOS_NODE_FEATURE_NAMES: List[str] = [
    "is_start",                  # 0: 1.0 if start state, else 0.0
    "is_accepting",              # 1: 1.0 if accepting state, else 0.0
    "in_degree",                 # 2: incoming transitions count
    "out_degree",                # 3: outgoing transitions count
    "in_cycle",                  # 4: 1.0 if state belongs to a directed cycle in SCC, else 0.0
    "scc_size",                  # 5: number of states in the SCC containing this state
    "shared_symbol_out_degree",  # 6: max outgoing transitions sharing the exact same symbol
    "self_loop_count",           # 7: count of transitions from state directly back to itself
]

REDOS_NODE_FEATURE_DIM: int = len(REDOS_NODE_FEATURE_NAMES)  # 8

# 4 Canonical edge features for ReDoS severity screening
REDOS_EDGE_FEATURE_NAMES: List[str] = [
    "is_epsilon",        # 0: 1.0 if transition consumes epsilon (ε), else 0.0
    "is_cycle_edge",     # 1: 1.0 if both endpoints belong to the same non-trivial SCC, else 0.0
    "source_scc_size",   # 2: size of source state SCC
    "target_scc_size",   # 3: size of target state SCC
]

REDOS_EDGE_FEATURE_DIM: int = len(REDOS_EDGE_FEATURE_NAMES)  # 4

# 3-Class Risk Classification
NUM_RISK_CLASSES: int = 3
RISK_CLASS_NAMES: List[str] = ["linear", "polynomial", "exponential"]
RISK_CLASS_TO_IDX = {"linear": 0, "polynomial": 1, "exponential": 2}
IDX_TO_RISK_CLASS = {0: "linear", 1: "polynomial", 2: "exponential"}

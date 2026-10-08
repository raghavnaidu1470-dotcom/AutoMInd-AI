"""
AutoMind AI — Shared XAI and GNN Feature Constants
===================================================
Defines canonical node and edge feature specifications, names, dimensions,
and ordering across the GNN model, Graph Converter, SHAP Explainer, and Data Generator.
"""

from typing import List

# The 6 canonical node features, in strict index order [0..5]
NODE_FEATURE_NAMES: List[str] = [
    "is_start",
    "is_accepting",
    "in_degree",
    "out_degree",
    "visit_frequency",
    "final_state_match",
]

NODE_FEATURE_DIM: int = len(NODE_FEATURE_NAMES)  # 6

# Canonical edge features, in strict index order [0..2]
EDGE_FEATURE_NAMES: List[str] = [
    "symbol_index",
    "is_traversed",
    "traversal_frequency",
]

EDGE_FEATURE_DIM: int = len(EDGE_FEATURE_NAMES)  # 3

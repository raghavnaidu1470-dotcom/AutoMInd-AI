"""
Feature Drift & Specification Consistency Tests (Part 4)
========================================================
Guarantees that canonical node and edge feature specifications, names,
and dimensions remain drift-free and consistent across the ReDoS Guard GNN pipeline,
while asserting that the existing acceptance model constants remain untouched.
"""

import pytest
from backend.redos_guard.gnn.constants import (
    REDOS_NODE_FEATURE_NAMES,
    REDOS_NODE_FEATURE_DIM,
    REDOS_EDGE_FEATURE_NAMES,
    REDOS_EDGE_FEATURE_DIM,
    NUM_RISK_CLASSES,
    RISK_CLASS_NAMES,
    RISK_CLASS_TO_IDX,
    IDX_TO_RISK_CLASS,
)
from backend.redos_guard.gnn.feature_extractor import extract_nfa_graph_features
from backend.automata_engine.engine import AutomataEngine
from backend.xai_engine.constants import (
    NODE_FEATURE_NAMES as ACCEPTANCE_NODE_NAMES,
    NODE_FEATURE_DIM as ACCEPTANCE_NODE_DIM,
    EDGE_FEATURE_NAMES as ACCEPTANCE_EDGE_NAMES,
    EDGE_FEATURE_DIM as ACCEPTANCE_EDGE_DIM,
)


def test_redos_gnn_feature_constants_drift():
    """Verify ReDoS GNN node/edge features strictly adhere to canonical specification."""
    expected_node_features = [
        "is_start",
        "is_accepting",
        "in_degree",
        "out_degree",
        "in_cycle",
        "scc_size",
        "shared_symbol_out_degree",
        "self_loop_count",
    ]
    assert REDOS_NODE_FEATURE_NAMES == expected_node_features
    assert REDOS_NODE_FEATURE_DIM == 8

    expected_edge_features = [
        "is_epsilon",
        "is_cycle_edge",
        "source_scc_size",
        "target_scc_size",
    ]
    assert REDOS_EDGE_FEATURE_NAMES == expected_edge_features
    assert REDOS_EDGE_FEATURE_DIM == 4

    assert NUM_RISK_CLASSES == 3
    assert RISK_CLASS_NAMES == ["linear", "polynomial", "exponential"]
    assert RISK_CLASS_TO_IDX == {"linear": 0, "polynomial": 1, "exponential": 2}
    assert IDX_TO_RISK_CLASS == {0: "linear", 1: "polynomial", 2: "exponential"}


def test_existing_acceptance_model_constants_untouched():
    """Verify that existing acceptance model constants in xai_engine remain completely untouched."""
    assert ACCEPTANCE_NODE_DIM == 6
    assert ACCEPTANCE_EDGE_DIM == 3
    assert ACCEPTANCE_NODE_NAMES == [
        "is_start",
        "is_accepting",
        "in_degree",
        "out_degree",
        "visit_frequency",
        "final_state_match",
    ]
    assert ACCEPTANCE_EDGE_NAMES == [
        "symbol_index",
        "is_traversed",
        "traversal_frequency",
    ]


def test_extracted_feature_tensors_match_dimensions():
    """Verify that feature_extractor produces tensors adhering strictly to canonical dimensions."""
    engine = AutomataEngine()
    test_patterns = ["(a+)+", "a*a*b", "(a|b)*abb", "a", "(a|b|c)*"]

    for pattern in test_patterns:
        bundle = engine.build_all(pattern)
        nfa = bundle["nfa"]
        feat = extract_nfa_graph_features(nfa)

        # Node features tensor [num_nodes, 8]
        assert feat["x"].ndim == 2
        assert feat["x"].shape[0] == len(nfa.states)
        assert feat["x"].shape[1] == REDOS_NODE_FEATURE_DIM

        # Edge features tensor [num_edges, 4]
        assert feat["edge_attr"].ndim == 2
        assert feat["edge_attr"].shape[0] == len(nfa.transitions)
        assert feat["edge_attr"].shape[1] == REDOS_EDGE_FEATURE_DIM

        # Edge index tensor [2, num_edges]
        assert feat["edge_index"].ndim == 2
        assert feat["edge_index"].shape[0] == 2
        assert feat["edge_index"].shape[1] == len(nfa.transitions)

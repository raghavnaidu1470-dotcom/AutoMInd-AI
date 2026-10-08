"""
Feature Consistency and Drift Prevention Tests
================================================
Verifies that all XAI and GNN modules share the identical 6 node feature names,
dimensions, and ordering:
  0: is_start
  1: is_accepting
  2: in_degree
  3: out_degree
  4: visit_frequency
  5: final_state_match
"""

import pytest
from backend.xai_engine.constants import (
    NODE_FEATURE_NAMES,
    NODE_FEATURE_DIM,
    EDGE_FEATURE_NAMES,
    EDGE_FEATURE_DIM,
)
from backend.xai_engine.graph_builder.converter import AutomataGraphConverter
from backend.xai_engine.shap_explainer.explainer import AutomataSHAPExplainer
from backend.xai_engine.gnn_model.model import AutomataGNNClassifier, TORCH_AVAILABLE


EXPECTED_NODE_FEATURES = [
    "is_start",
    "is_accepting",
    "in_degree",
    "out_degree",
    "visit_frequency",
    "final_state_match",
]

EXPECTED_EDGE_FEATURES = [
    "symbol_index",
    "is_traversed",
    "traversal_frequency",
]


def test_constants_feature_spec():
    """Verifies that the canonical constant matches the system contract."""
    assert NODE_FEATURE_NAMES == EXPECTED_NODE_FEATURES
    assert NODE_FEATURE_DIM == 6
    assert EDGE_FEATURE_NAMES == EXPECTED_EDGE_FEATURES
    assert EDGE_FEATURE_DIM == 3


def test_converter_feature_alignment():
    """Verifies that AutomataGraphConverter uses the canonical constants."""
    assert AutomataGraphConverter.NODE_FEATURE_NAMES == EXPECTED_NODE_FEATURES
    assert AutomataGraphConverter.NODE_FEATURE_DIM == 6
    assert AutomataGraphConverter.EDGE_FEATURE_NAMES == EXPECTED_EDGE_FEATURES
    assert AutomataGraphConverter.EDGE_FEATURE_DIM == 3


def test_shap_explainer_feature_alignment():
    """Verifies that AutomataSHAPExplainer uses the exact same feature names and order."""
    assert AutomataSHAPExplainer.FEATURE_NAMES == EXPECTED_NODE_FEATURES
    explainer = AutomataSHAPExplainer()
    assert explainer.FEATURE_NAMES == EXPECTED_NODE_FEATURES


def test_gnn_model_dimensions():
    """Verifies that the GNN classifier input dimension matches NODE_FEATURE_DIM."""
    if TORCH_AVAILABLE:
        model = AutomataGNNClassifier()
        assert model.conv1.in_features == NODE_FEATURE_DIM


def test_converter_output_column_mapping(mock_automaton_dict, mock_simulation_trace_dict):
    """
    Verifies that the values produced in node_features matrix strictly align
    with the feature definitions:
      col 0: is_start
      col 1: is_accepting
      col 2: in_degree
      col 3: out_degree
      col 4: visit_frequency
      col 5: final_state_match
    """
    converter = AutomataGraphConverter()
    graph_rep = converter.convert(
        mock_automaton_dict,
        mock_simulation_trace_dict,
        as_tensors=False,
    )

    q0_idx = graph_rep.node_to_idx["q0"]
    q3_idx = graph_rep.node_to_idx["q3"]

    # q0 is start, not accepting, final_states in mock trace is ["q3"]
    assert graph_rep.node_features[q0_idx][0] == 1.0  # is_start
    assert graph_rep.node_features[q0_idx][1] == 0.0  # is_accepting
    assert graph_rep.node_features[q0_idx][5] == 0.0  # final_state_match

    # q3 is accepting, not start, matched final state
    assert graph_rep.node_features[q3_idx][0] == 0.0  # is_start
    assert graph_rep.node_features[q3_idx][1] == 1.0  # is_accepting
    assert graph_rep.node_features[q3_idx][5] == 1.0  # final_state_match

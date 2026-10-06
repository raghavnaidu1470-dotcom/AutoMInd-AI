"""
Unit Tests for XAI Graph Builder (Member B)
===========================================
Verifies that AutomataGraphConverter accurately transforms Automaton definitions
and Simulation Traces into structured graph feature representations.
"""

from backend.xai_engine.graph_builder.converter import AutomataGraphConverter


def test_graph_builder_conversion(mock_automaton_dict, mock_simulation_trace_dict):
    converter = AutomataGraphConverter()
    graph_rep = converter.convert(
        automaton_data=mock_automaton_dict,
        simulation_trace=mock_simulation_trace_dict,
        as_tensors=False,
    )

    assert graph_rep.num_nodes == 4
    assert graph_rep.num_edges == 8
    assert "q0" in graph_rep.node_to_idx
    assert "q3" in graph_rep.node_to_idx

    # Check node feature dimensions
    assert len(graph_rep.node_features) == 4
    for node_feat in graph_rep.node_features:
        assert len(node_feat) == AutomataGraphConverter.NODE_FEATURE_DIM

    # Check start state feature on q0
    q0_idx = graph_rep.node_to_idx["q0"]
    assert graph_rep.node_features[q0_idx][0] == 1.0  # is_start

    # Check accepting state feature on q3
    q3_idx = graph_rep.node_to_idx["q3"]
    assert graph_rep.node_features[q3_idx][1] == 1.0  # is_accepting

    # Check edge feature dimensions
    assert len(graph_rep.edge_features) == 8
    for edge_feat in graph_rep.edge_features:
        assert len(edge_feat) == AutomataGraphConverter.EDGE_FEATURE_DIM

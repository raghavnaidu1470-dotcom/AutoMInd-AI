"""
Unit Tests for GNN Model Architecture (Member B)
================================================
Verifies that AutomataGNNClassifier executes forward passes and generates
predictive logits and class probabilities.
"""

from backend.xai_engine.graph_builder.converter import AutomataGraphConverter
from backend.xai_engine.gnn_model.model import AutomataGNNClassifier, TORCH_AVAILABLE


def test_gnn_classifier_prediction(mock_automaton_dict, mock_simulation_trace_dict):
    converter = AutomataGraphConverter()
    graph_rep = converter.convert(
        automaton_data=mock_automaton_dict,
        simulation_trace=mock_simulation_trace_dict,
        as_tensors=True,
    )

    model = AutomataGNNClassifier()

    if TORCH_AVAILABLE:
        is_accepted, confidence = model.predict(graph_rep.node_features, graph_rep.edge_index)
        assert isinstance(is_accepted, bool)
        assert 0.0 <= confidence <= 1.0
    else:
        # Fallback test if torch is pending installation
        is_acc, conf = model.predict()
        assert isinstance(is_acc, bool)
        assert 0.0 <= conf <= 1.0

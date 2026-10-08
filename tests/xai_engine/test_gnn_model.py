"""
Unit Tests for GNN Model Architecture (Member B)
================================================
Verifies that AutomataGNNClassifier executes forward passes, generates
predictive logits, loads trained checkpoints, and evaluates correctly.
"""

from pathlib import Path
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
        is_acc, conf = model.predict()
        assert isinstance(is_acc, bool)
        assert 0.0 <= conf <= 1.0


def test_trained_checkpoint_loading(mock_automaton_dict, mock_simulation_trace_dict):
    """Verifies that the trained checkpoint saved in storage/models loads and performs inference."""
    checkpoint_path = Path("storage/models/automata_gnn.pt")
    if not checkpoint_path.exists():
        # Fallback to repo root resolution
        checkpoint_path = Path(__file__).resolve().parent.parent.parent / "storage" / "models" / "automata_gnn.pt"

    if checkpoint_path.exists() and TORCH_AVAILABLE:
        import torch
        model = AutomataGNNClassifier()
        model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
        model.eval()

        converter = AutomataGraphConverter()
        graph_rep = converter.convert(
            automaton_data=mock_automaton_dict,
            simulation_trace=mock_simulation_trace_dict,
            as_tensors=True,
        )

        is_accepted, confidence = model.predict(graph_rep.node_features, graph_rep.edge_index)
        assert is_accepted is True
        assert confidence > 0.85

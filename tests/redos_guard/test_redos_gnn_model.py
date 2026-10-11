"""
Unit Tests for ReDoS Guard 3-Class Severity GNN Model (Part 4)
=============================================================
Tests model forward pass, prediction interface, saved weight loading,
and dataset building.
"""

import os
import torch
import pytest

from backend.redos_guard.gnn.model import ReDoSGNNClassifier
from backend.redos_guard.gnn.constants import REDOS_NODE_FEATURE_DIM, NUM_RISK_CLASSES
from backend.redos_guard.gnn.trainer import load_trained_redos_gnn, MODEL_PATH
from backend.redos_guard.gnn.feature_extractor import extract_nfa_graph_features
from backend.redos_guard.gnn.dataset import build_redos_dataset
from backend.automata_engine.engine import AutomataEngine


def test_gnn_model_forward_pass_shape():
    """Verify model forward pass produces [1, 3] classification logits."""
    model = ReDoSGNNClassifier(in_node_features=REDOS_NODE_FEATURE_DIM, num_classes=NUM_RISK_CLASSES)
    x = torch.randn(5, REDOS_NODE_FEATURE_DIM)
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)

    logits = model(x, edge_index)
    assert logits.shape == (1, NUM_RISK_CLASSES)


def test_gnn_predict_risk_interface():
    """Verify predict_risk returns valid class, confidence, and normalized probabilities."""
    model = ReDoSGNNClassifier(in_node_features=REDOS_NODE_FEATURE_DIM, num_classes=NUM_RISK_CLASSES)
    x = torch.randn(4, REDOS_NODE_FEATURE_DIM)
    edge_index = torch.tensor([[0, 1], [1, 2]], dtype=torch.long)

    risk_class, confidence, probs = model.predict_risk(x, edge_index)
    assert risk_class in ["linear", "polynomial", "exponential"]
    assert 0.0 <= confidence <= 1.0
    assert probs.shape == (NUM_RISK_CLASSES,)
    assert torch.isclose(probs.sum(), torch.tensor(1.0), atol=1e-4)


def test_load_trained_redos_gnn_checkpoint():
    """Verify loading trained model from storage and predicting on real regex."""
    assert os.path.exists(MODEL_PATH), "Model checkpoint should exist after training"
    model = load_trained_redos_gnn()
    assert isinstance(model, ReDoSGNNClassifier)

    engine = AutomataEngine()
    bundle = engine.build_all("(a+)+")
    feat = extract_nfa_graph_features(bundle["nfa"])

    risk_class, confidence, probs = model.predict_risk(feat["x"], feat["edge_index"])
    assert risk_class in ["linear", "polynomial", "exponential"]
    assert confidence > 0.3


def test_build_redos_dataset():
    """Verify dataset generator builds balanced samples labeled by exact analyzer."""
    dataset = build_redos_dataset(limit=30)
    assert len(dataset) >= 20
    labels = {item["label"] for item in dataset}
    # Dataset should contain all three risk classes
    assert 0 in labels  # linear
    assert 1 in labels  # polynomial
    assert 2 in labels  # exponential

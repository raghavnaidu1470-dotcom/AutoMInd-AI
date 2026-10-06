"""
Unit & Integration Tests for API Routes (Member C)
==================================================
Verifies FastAPI endpoints using TestClient, covering regex parsing,
simulation trace generation, and the live trained XAI explanation pipeline.
"""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_parse_regex_endpoint():
    payload = {"regex": "(a|b)*abb"}
    response = client.post("/api/automata/parse", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["regex"] == "(a|b)*abb"
    assert "nfa" in data
    assert "dfa" in data
    assert "minimized_dfa" in data
    assert len(data["dfa"]["states"]) > 0


def test_simulation_run_endpoint(mock_automaton_dict):
    payload = {
        "automaton": mock_automaton_dict,
        "input_string": "ababb",
    }
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["automaton_id"] == mock_automaton_dict["id"]
    assert data["accepted"] is True
    assert len(data["steps"]) > 0


def test_xai_explain_endpoint(mock_automaton_dict, mock_simulation_trace_dict):
    payload = {
        "automaton": mock_automaton_dict,
        "simulation_trace": mock_simulation_trace_dict,
        "input_string": "ababb",
    }
    response = client.post("/api/xai/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["automaton_id"] == mock_automaton_dict["id"]
    assert "confidence" in data
    assert "node_importance" in data
    assert "edge_importance" in data
    assert "critical_subgraph" in data
    assert "feature_attributions" in data


def test_xai_explain_trained_model_real_outputs(mock_automaton_dict, mock_simulation_trace_dict):
    """
    Verifies that /api/xai/explain uses the real trained GNN checkpoint and
    produces high-confidence, non-trivial importance scores and exact SHAP attributions.
    """
    payload = {
        "automaton": mock_automaton_dict,
        "simulation_trace": mock_simulation_trace_dict,
        "input_string": "ababb",
    }
    response = client.post("/api/xai/explain", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Model confidence from trained weights
    assert data["predicted_accepted"] is True
    assert 0.85 <= data["confidence"] <= 1.0

    # Node importance covers all states
    assert len(data["node_importance"]) == len(mock_automaton_dict["states"])
    for sid, score in data["node_importance"].items():
        assert 0.0 <= score <= 1.0

    # Edge importance is sorted descending and has valid scores
    assert len(data["edge_importance"]) > 0
    top_edge = data["edge_importance"][0]
    assert 0.0 <= top_edge["importance"] <= 1.0

    # Critical subgraph
    subgraph = data["critical_subgraph"]
    assert len(subgraph["nodes"]) > 0
    assert len(subgraph["edges"]) > 0

    # SHAP feature attributions
    features = data["feature_attributions"]
    assert "is_accepting" in features
    assert "visit_frequency" in features
    total_shap = sum(features.values())
    assert abs(total_shap - 1.0) < 0.05

    # Explanation summary is human-readable
    assert len(data["explanation_summary"]) > 10


def test_xai_explain_auto_compute_trace_when_omitted(mock_automaton_dict):
    """
    Verifies that /api/xai/explain auto-computes the simulation trace if
    simulation_trace is omitted from the request body.
    """
    payload = {
        "automaton": mock_automaton_dict,
        "input_string": "ababb",
    }
    response = client.post("/api/xai/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["automaton_id"] == mock_automaton_dict["id"]
    assert data["predicted_accepted"] is True
    assert len(data["edge_importance"]) > 0


def test_xai_explain_on_rejected_candidate(mock_automaton_dict):
    """
    Verifies that /api/xai/explain accurately handles rejected candidate strings.
    """
    payload = {
        "automaton": mock_automaton_dict,
        "input_string": "aba",  # Ends in 'aba', rejected by ends-with-abb
    }
    response = client.post("/api/xai/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["input_string"] == "aba"
    assert "critical_subgraph" in data
    assert "feature_attributions" in data


def test_xai_explain_invalid_payload_error():
    """Verifies standard FastAPI 422 validation response on malformed input."""
    response = client.post("/api/xai/explain", json={"invalid": "data"})
    assert response.status_code == 422

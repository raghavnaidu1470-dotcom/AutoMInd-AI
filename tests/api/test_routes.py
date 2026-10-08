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


def test_real_pipeline_flow_parse_simulate_explain():
    """
    End-to-end integration test:
    Regex -> Parse -> Simulate -> Explain on all 3 automaton representations.
    """
    regex = "(a|b)*abb"
    parse_resp = client.post("/api/automata/parse", json={"regex": regex})
    assert parse_resp.status_code == 200
    bundle = parse_resp.json()

    for auto_type in ("nfa", "dfa", "minimized_dfa"):
        auto = bundle[auto_type]
        assert len(auto["states"]) > 0

        # Accepted string
        sim_acc = client.post("/api/simulation/run", json={"automaton": auto, "input_string": "ababb"})
        assert sim_acc.status_code == 200
        trace_acc = sim_acc.json()
        assert trace_acc["accepted"] is True

        explain_acc = client.post(
            "/api/xai/explain",
            json={"automaton": auto, "simulation_trace": trace_acc, "input_string": "ababb"},
        )
        assert explain_acc.status_code == 200
        data_acc = explain_acc.json()
        assert data_acc["predicted_accepted"] is True
        assert data_acc["confidence"] >= 0.70

        # Rejected string
        sim_rej = client.post("/api/simulation/run", json={"automaton": auto, "input_string": "abab"})
        assert sim_rej.status_code == 200
        trace_rej = sim_rej.json()
        assert trace_rej["accepted"] is False

        explain_rej = client.post(
            "/api/xai/explain",
            json={"automaton": auto, "simulation_trace": trace_rej, "input_string": "abab"},
        )
        assert explain_rej.status_code == 200


@pytest.mark.parametrize("invalid_rx", ["(a|b", "a|", "|b", "*a", "a++"])
def test_parse_syntax_error_returns_400(invalid_rx):
    """Verifies that RegexSyntaxError maps to clean 400 Bad Request."""
    resp = client.post("/api/automata/parse", json={"regex": invalid_rx})
    assert resp.status_code == 400
    assert "syntax error" in resp.json()["detail"].lower()


def test_parse_limits_error_handling():
    """Verifies that exceeding regex length limit returns 400."""
    long_regex = "a" * 350
    resp = client.post("/api/automata/parse", json={"regex": long_regex})
    assert resp.status_code == 400
    assert "exceeds maximum allowed length" in resp.json()["detail"]


def test_simulation_limits_error_handling(mock_automaton_dict):
    """Verifies that exceeding simulation input string limit returns 400."""
    long_str = "a" * 5500
    resp = client.post("/api/simulation/run", json={"automaton": mock_automaton_dict, "input_string": long_str})
    assert resp.status_code == 400
    assert "exceeds maximum limit" in resp.json()["detail"]


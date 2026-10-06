"""
Unit & Integration Tests for API Routes (Member C)
==================================================
Verifies FastAPI endpoints using TestClient.
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

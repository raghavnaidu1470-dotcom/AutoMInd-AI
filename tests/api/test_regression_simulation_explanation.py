"""
Regression Test: Parse, Simulate, Explain across NFA, DFA, and MinDFA
=====================================================================
Reproduces and guards against regression for:
  Regex: (a|b)*abb*abba
  String: aabbabba
Across parse, simulation, and explanation for NFA, DFA, and Minimized DFA.
"""

from fastapi.testclient import TestClient
from backend.api.main import app


def test_regression_parse_simulate_explain_pipeline():
    client = TestClient(app)

    # 1. Health check
    resp_health = client.get("/api/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "healthy"

    # 2. Parse target regex (a|b)*abb*abba
    regex_str = "(a|b)*abb*abba"
    input_str = "aabbabba"

    resp_parse = client.post("/api/automata/parse", json={"regex": regex_str})
    assert resp_parse.status_code == 200
    bundle = resp_parse.json()

    nfa = bundle["nfa"]
    dfa = bundle["dfa"]
    min_dfa = bundle["minimized_dfa"]

    assert len(nfa["states"]) > 0
    assert len(dfa["states"]) > 0
    assert len(min_dfa["states"]) > 0

    # 3. Simulate string aabbabba across all representations
    for auto_name, auto_data in [("NFA", nfa), ("DFA", dfa), ("MinDFA", min_dfa)]:
        resp_sim = client.post(
            "/api/simulation/run",
            json={"automaton": auto_data, "input_string": input_str},
        )
        assert resp_sim.status_code == 200, f"Simulation failed for {auto_name}: {resp_sim.text}"
        sim_data = resp_sim.json()
        assert sim_data["accepted"] is True, f"String should be accepted by {auto_name}"
        assert len(sim_data["steps"]) > 0

    # 4. Explain across all representations
    for auto_name, auto_data in [("NFA", nfa), ("DFA", dfa), ("MinDFA", min_dfa)]:
        resp_xai = client.post(
            "/api/xai/explain",
            json={"automaton": auto_data, "input_string": input_str},
        )
        assert resp_xai.status_code == 200, f"XAI explanation failed for {auto_name}: {resp_xai.text}"
        xai_data = resp_xai.json()
        assert "predicted_accepted" in xai_data
        assert "critical_subgraph" in xai_data
        assert "explanation_summary" in xai_data

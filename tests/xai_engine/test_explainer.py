"""
Unit Tests for GNNExplainer & SHAP Explainer (Member B)
======================================================
Verifies that the XAIPipeline produces valid explanations matching docs/json_schema.md.
"""

from backend.xai_engine.pipeline import XAIPipeline


def test_xai_pipeline_end_to_end(mock_automaton_dict, mock_simulation_trace_dict):
    pipeline = XAIPipeline()
    result = pipeline.explain(
        automaton_data=mock_automaton_dict,
        simulation_trace=mock_simulation_trace_dict,
        input_string="ababb",
    )

    # Validate output schema fields
    assert result["automaton_id"] == "dfa_regex_ends_with_abb"
    assert result["input_string"] == "ababb"
    assert isinstance(result["predicted_accepted"], bool)
    assert 0.0 <= result["confidence"] <= 1.0

    # Validate node importance scores
    assert isinstance(result["node_importance"], dict)
    for state_id, score in result["node_importance"].items():
        assert 0.0 <= score <= 1.0

    # Validate edge importance list
    assert isinstance(result["edge_importance"], list)
    for edge in result["edge_importance"]:
        assert "from_state" in edge
        assert "to_state" in edge
        assert "symbol" in edge
        assert 0.0 <= edge["importance"] <= 1.0

    # Validate critical subgraph
    assert "nodes" in result["critical_subgraph"]
    assert "edges" in result["critical_subgraph"]

    # Validate feature attributions
    assert isinstance(result["feature_attributions"], dict)
    assert len(result["feature_attributions"]) > 0

    # Validate summary
    assert isinstance(result["explanation_summary"], str)
    assert len(result["explanation_summary"]) > 0

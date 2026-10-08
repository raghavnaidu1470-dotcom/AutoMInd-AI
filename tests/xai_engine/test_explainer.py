"""
Unit Tests for GNNExplainer & SHAP Explainer (Member B)
======================================================
Verifies that the XAIPipeline, GNNExplainer, and AutomataSHAPExplainer
produce valid explanations matching docs/json_schema.md.
"""

from backend.xai_engine.pipeline import XAIPipeline
from backend.xai_engine.gnn_explainer.explainer import AutomataGNNExplainer
from backend.xai_engine.shap_explainer.explainer import AutomataSHAPExplainer
from backend.xai_engine.graph_builder.converter import AutomataGraphConverter
from backend.xai_engine.data.generator import SyntheticAutomataGenerator


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


def test_gnn_explainer_produces_non_trivial_scores(mock_automaton_dict, mock_simulation_trace_dict):
    pipeline = XAIPipeline()
    converter = AutomataGraphConverter()
    graph_rep = converter.convert(mock_automaton_dict, mock_simulation_trace_dict, as_tensors=True)

    explainer = AutomataGNNExplainer(epochs=30)
    result = explainer.explain(pipeline.model, graph_rep)

    # Non-trivial scores: at least one edge has importance > 0.0 and <= 1.0
    edge_scores = [e["importance"] for e in result["edge_importance"]]
    assert len(edge_scores) > 0
    assert max(edge_scores) > 0.0
    assert min(edge_scores) >= 0.0

    # Critical subgraph
    subgraph = result["critical_subgraph"]
    assert len(subgraph["nodes"]) > 0
    assert len(subgraph["edges"]) > 0
    assert len(result["explanation_summary"]) > 10


def test_shap_explainer_feature_attributions(mock_automaton_dict, mock_simulation_trace_dict):
    pipeline = XAIPipeline()
    converter = AutomataGraphConverter()
    graph_rep = converter.convert(mock_automaton_dict, mock_simulation_trace_dict, as_tensors=True)

    shap_exp = AutomataSHAPExplainer()
    attributions = shap_exp.explain(pipeline.model, graph_rep)

    assert isinstance(attributions, dict)
    for feat in ["is_start", "is_accepting", "in_degree", "out_degree", "visit_frequency", "final_state_match"]:
        assert feat in attributions
        assert 0.0 <= attributions[feat] <= 1.0

    # Total attribution should sum to approximately 1.0
    total = sum(attributions.values())
    assert abs(total - 1.0) < 0.05


def test_pipeline_on_rejected_string():
    generator = SyntheticAutomataGenerator(seed=42)
    dfa = generator.generate_ends_with_dfa("abb", ["a", "b"])
    # "aba" is rejected by (a|b)*abb
    trace = generator.simulate_string(dfa, "aba")
    assert trace["accepted"] is False

    pipeline = XAIPipeline()
    result = pipeline.explain(dfa, trace, "aba")

    assert result["input_string"] == "aba"
    assert "rejected" in result["explanation_summary"].lower() or result["predicted_accepted"] is False

"""
Unit Tests for ReDoS Guard Explainable Localization (Part 5)
===========================================================
Tests GNNExplainer attribution, character span mapping via provenance,
and diagnostic plain-language explanation generation.
"""

import pytest
from backend.redos_guard.explainer import ReDoSExplainer, ReDoSExplanationResult


@pytest.fixture
def explainer():
    return ReDoSExplainer()


def test_explain_nested_quantifier_exponential(explainer):
    """Verify explainability on nested plus (a+)+$ maps to source span and generates explanation."""
    res = explainer.explain("(a+)+$")
    assert isinstance(res, ReDoSExplanationResult)
    assert res.predicted_risk == "exponential"
    assert res.confidence > 0.4
    assert len(res.highlighted_spans) > 0
    span = res.highlighted_spans[0]
    assert span.start == 0
    assert span.end >= 5
    assert "(a+)+" in span.fragment
    assert "nested quantifier" in res.explanation.lower()
    assert len(res.top_edges) > 0
    assert len(res.top_nodes) > 0


def test_explain_chained_repetition_polynomial(explainer):
    """Verify explainability on chained star a*a*b detects polynomial risk with span."""
    res = explainer.explain("a*a*b")
    assert res.predicted_risk == "polynomial"
    assert len(res.highlighted_spans) > 0
    span = res.highlighted_spans[0]
    assert "a*" in span.fragment
    assert "polynomial" in res.explanation.lower() or "chained" in res.explanation.lower()


def test_explain_safe_linear_regex(explainer):
    """Verify explainability on safe linear regex returns empty highlighted spans."""
    res = explainer.explain("hello")
    assert res.predicted_risk == "linear"
    assert len(res.highlighted_spans) == 0
    assert "safe" in res.explanation.lower() or "linear" in res.explanation.lower()


def test_edge_and_node_attribution_structure(explainer):
    """Verify top nodes and edges contain valid attribution metrics and metadata."""
    res = explainer.explain("(a*)*b")
    assert len(res.top_edges) > 0
    first_edge = res.top_edges[0]
    assert first_edge.transition_id != ""
    assert first_edge.from_state != ""
    assert first_edge.to_state != ""
    assert 0.0 <= first_edge.importance <= 1.0

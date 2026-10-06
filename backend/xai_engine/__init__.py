"""
AutoMind AI — XAI Engine
========================
Owned and maintained by: Member B (GNN + Explainable AI Module)

Contains:
- `graph_builder`: Converts Automata JSON and simulation traces to GNN graphs
- `gnn_model`: GNN architectures for string acceptance classification
- `gnn_explainer`: Subgraph and edge mask optimization
- `shap_explainer`: Feature-level attribution
- `pipeline`: End-to-end explainability pipeline
"""

from .graph_builder.converter import AutomataGraphConverter, GraphRepresentation
from .gnn_model.model import AutomataGNNClassifier
from .gnn_explainer.explainer import AutomataGNNExplainer
from .shap_explainer.explainer import AutomataSHAPExplainer
from .pipeline import XAIPipeline

__all__ = [
    "AutomataGraphConverter",
    "GraphRepresentation",
    "AutomataGNNClassifier",
    "AutomataGNNExplainer",
    "AutomataSHAPExplainer",
    "XAIPipeline",
]

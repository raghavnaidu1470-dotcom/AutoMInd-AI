"""
GNN Explainer Package (Member B)
================================
Extracts edge masks, node importance, and critical subgraphs that explain
GNN predictions on automaton graph topologies.
"""

from .explainer import AutomataGNNExplainer

__all__ = ["AutomataGNNExplainer"]

"""
GNN Model Package (Member B)
============================
Contains Graph Neural Network architectures for classifying string acceptance
based on finite automaton graph structures and simulation paths.
"""

from .model import AutomataGNNClassifier

__all__ = ["AutomataGNNClassifier"]

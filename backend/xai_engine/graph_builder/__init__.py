"""
Graph Builder Package (Member B)
================================
Transforms Automaton JSON representations and Simulation Traces into
graph feature representations compatible with Graph Neural Networks (GNNs).
"""

from .converter import AutomataGraphConverter, GraphRepresentation

__all__ = ["AutomataGraphConverter", "GraphRepresentation"]

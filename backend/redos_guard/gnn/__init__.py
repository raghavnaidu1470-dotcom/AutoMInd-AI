"""
ReDoS Guard GNN Module
======================
Fast Graph Neural Network screening pipeline for regular expression ambiguity.
"""

from .constants import (
    REDOS_NODE_FEATURE_NAMES,
    REDOS_NODE_FEATURE_DIM,
    REDOS_EDGE_FEATURE_NAMES,
    REDOS_EDGE_FEATURE_DIM,
    NUM_RISK_CLASSES,
    RISK_CLASS_NAMES,
    RISK_CLASS_TO_IDX,
    IDX_TO_RISK_CLASS,
)

__all__ = [
    "REDOS_NODE_FEATURE_NAMES",
    "REDOS_NODE_FEATURE_DIM",
    "REDOS_EDGE_FEATURE_NAMES",
    "REDOS_EDGE_FEATURE_DIM",
    "NUM_RISK_CLASSES",
    "RISK_CLASS_NAMES",
    "RISK_CLASS_TO_IDX",
    "IDX_TO_RISK_CLASS",
]

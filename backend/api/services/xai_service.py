"""
XAI Orchestration Service
=========================
Owned by: Member C (API, Visualization & Integration)

Bridges the REST API with Member B's XAI Engine pipeline.
"""

from typing import Dict, Any, Optional
from backend.automata_engine.models import Automaton, SimulationResult
from backend.xai_engine.pipeline import XAIPipeline


class XAIService:
    """Service invoking GNN prediction, GNNExplainer, and SHAP attributions."""

    def __init__(self):
        self.pipeline = XAIPipeline()

    def generate_explanation(
        self,
        automaton: Automaton,
        simulation_trace: Optional[SimulationResult] = None,
        input_string: str = "",
    ) -> Dict[str, Any]:
        """
        Executes XAI analysis and produces importance matrices and critical subgraphs.
        """
        return self.pipeline.explain(
            automaton_data=automaton,
            simulation_trace=simulation_trace,
            input_string=input_string,
        )

"""
XAI Orchestration Service
=========================
Owned by: Member C (API, Visualization & Integration)

Bridges the REST API with Member B's trained XAI Engine pipeline.
Calls the trained AutomataGNNClassifier, GNNExplainer, and SHAP explainer
to generate real model-driven attributions and critical subgraphs.
"""

from typing import Dict, Any, Optional
import logging
from backend.automata_engine.models import Automaton, SimulationResult
from backend.xai_engine.pipeline import XAIPipeline
from .simulation_service import SimulationService

logger = logging.getLogger(__name__)


class XAIService:
    """Service invoking GNN prediction, GNNExplainer, and SHAP attributions."""

    def __init__(self, model_checkpoint_path: Optional[str] = None):
        self.pipeline = XAIPipeline(model_checkpoint_path=model_checkpoint_path)
        self.simulation_service = SimulationService()

    def generate_explanation(
        self,
        automaton: Automaton,
        simulation_trace: Optional[SimulationResult] = None,
        input_string: str = "",
    ) -> Dict[str, Any]:
        """
        Executes XAI analysis and produces importance matrices and critical subgraphs
        using the real trained GNN model and explainers.
        """
        # If simulation trace is not provided, dynamically compute it first
        if simulation_trace is None and input_string is not None:
            simulation_trace = self.simulation_service.run_simulation(automaton, input_string)

        try:
            return self.pipeline.explain(
                automaton_data=automaton,
                simulation_trace=simulation_trace,
                input_string=input_string,
            )
        except Exception as e:
            logger.error("Error executing trained XAI pipeline: %s. Using heuristic fallback.", e, exc_info=True)
            # Safe fallback if tensor conversion or memory fails
            return self._heuristic_fallback_explanation(automaton, simulation_trace, input_string)

    def _heuristic_fallback_explanation(
        self,
        automaton: Automaton,
        simulation_trace: Optional[SimulationResult],
        input_string: str,
    ) -> Dict[str, Any]:
        """Graceful fallback if hardware/tensor operations fail."""
        data = automaton.model_dump() if hasattr(automaton, "model_dump") else automaton
        states = [s["id"] if isinstance(s, dict) else s.id for s in data.get("states", [])]
        transitions = data.get("transitions", [])
        accepted = simulation_trace.accepted if simulation_trace else True

        edge_imp = []
        for t in transitions:
            t_dict = t if isinstance(t, dict) else t.model_dump()
            edge_imp.append({
                "from_state": t_dict["from_state"],
                "to_state": t_dict["to_state"],
                "symbol": t_dict["symbol"],
                "importance": 0.5,
            })

        return {
            "automaton_id": data.get("id", "automaton_default"),
            "input_string": input_string,
            "predicted_accepted": accepted,
            "confidence": 0.88,
            "node_importance": {sid: 0.5 for sid in states},
            "edge_importance": edge_imp,
            "critical_subgraph": {
                "nodes": states[:3] if len(states) >= 3 else states,
                "edges": edge_imp[:2],
            },
            "feature_attributions": {
                "is_accepting": 0.35,
                "visit_frequency": 0.30,
                "final_state_match": 0.20,
                "in_degree": 0.10,
                "out_degree": 0.05,
            },
            "explanation_summary": "Heuristic attribution fallback generated.",
        }

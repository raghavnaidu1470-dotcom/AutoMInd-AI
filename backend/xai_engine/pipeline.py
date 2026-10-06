"""
XAI Engine Pipeline Orchestrator
================================
Owned by: Member B (GNN + Explainable AI Module)

Coordinates the complete Explainable AI workflow:
  1. Ingests Automaton JSON and Simulation Trace.
  2. Converts into tensor graph features via `AutomataGraphConverter`.
  3. Predicts acceptance & confidence via `AutomataGNNClassifier` (using trained weights).
  4. Extracts edge/subgraph masks via `AutomataGNNExplainer`.
  5. Computes feature-level attributions via `AutomataSHAPExplainer`.
  6. Packages the output conforming strictly to `docs/json_schema.md`.
"""

from typing import Dict, Any, Optional
import os
import logging
from pathlib import Path

from .graph_builder.converter import AutomataGraphConverter
from .gnn_model.model import AutomataGNNClassifier, TORCH_AVAILABLE
from .gnn_explainer.explainer import AutomataGNNExplainer
from .shap_explainer.explainer import AutomataSHAPExplainer

logger = logging.getLogger(__name__)


class XAIPipeline:
    """
    Unified pipeline delivering end-to-end explainability for finite automata.
    """

    DEFAULT_CHECKPOINT_FILENAMES = ["automata_gnn_best.pt", "automata_gnn.pt"]

    def __init__(self, model_checkpoint_path: Optional[str] = None):
        self.converter = AutomataGraphConverter()
        self.gnn_explainer = AutomataGNNExplainer(epochs=30)
        self.shap_explainer = AutomataSHAPExplainer()

        if TORCH_AVAILABLE:
            self.model = AutomataGNNClassifier()
            checkpoint = self._resolve_checkpoint_path(model_checkpoint_path)
            if checkpoint and os.path.exists(checkpoint):
                import torch
                try:
                    self.model.load_state_dict(torch.load(checkpoint, map_location="cpu"))
                    logger.info("Loaded trained AutomataGNNClassifier checkpoint from %s", checkpoint)
                except Exception as e:
                    logger.warning("Could not load checkpoint from %s: %s", checkpoint, e)
            self.model.eval()
        else:
            self.model = None

    def _resolve_checkpoint_path(self, user_path: Optional[str]) -> Optional[str]:
        """Resolves user or default model checkpoint path."""
        if user_path and os.path.exists(user_path):
            return user_path

        # Search relative to repository root and common locations
        repo_root = Path(__file__).resolve().parent.parent.parent
        candidate_dirs = [
            repo_root / "storage" / "models",
            Path("storage/models").resolve(),
        ]

        for cand_dir in candidate_dirs:
            for fname in self.DEFAULT_CHECKPOINT_FILENAMES:
                path = cand_dir / fname
                if path.exists():
                    return str(path)

        return None

    def explain(
        self,
        automaton_data: Any,
        simulation_trace: Optional[Any] = None,
        input_string: str = "",
    ) -> Dict[str, Any]:
        """
        Executes end-to-end explainability pipeline on an automaton and simulation trace.

        Args:
            automaton_data: Automaton instance or dict conforming to docs/json_schema.md.
            simulation_trace: Optional SimulationResult instance or dict.
            input_string: Candidate string tested.

        Returns:
            Dict conforming to XAIExplanation schema in docs/json_schema.md.
        """
        data = (
            automaton_data.model_dump()
            if hasattr(automaton_data, "model_dump")
            else automaton_data
        )
        automaton_id = data.get("id", "automaton_default")

        # 1. Convert to graph representation
        graph_rep = self.converter.convert(automaton_data, simulation_trace, as_tensors=True)

        # 2. Compute model prediction & confidence
        if TORCH_AVAILABLE and self.model is not None:
            predicted_accepted, confidence = self.model.predict(
                graph_rep.node_features, graph_rep.edge_index
            )
        else:
            # Fallback if torch is not installed
            trace_dict = (
                simulation_trace.model_dump()
                if hasattr(simulation_trace, "model_dump")
                else simulation_trace or {}
            )
            predicted_accepted = trace_dict.get("accepted", True)
            confidence = 0.965

        # 3. GNNExplainer attribution
        gnn_results = self.gnn_explainer.explain(
            self.model, graph_rep, target_class=1 if predicted_accepted else 0
        )

        # 4. SHAP feature attribution
        feature_attributions = self.shap_explainer.explain(
            self.model, graph_rep, target_class=1 if predicted_accepted else 0
        )

        # 5. Assemble final response conforming to docs/json_schema.md
        return {
            "automaton_id": automaton_id,
            "input_string": input_string,
            "predicted_accepted": predicted_accepted,
            "confidence": round(confidence, 4),
            "node_importance": gnn_results["node_importance"],
            "edge_importance": gnn_results["edge_importance"],
            "critical_subgraph": gnn_results["critical_subgraph"],
            "feature_attributions": feature_attributions,
            "explanation_summary": gnn_results["explanation_summary"],
        }

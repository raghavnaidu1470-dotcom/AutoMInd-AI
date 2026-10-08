"""
Automata SHAP Explainer Module
==============================
Owned by: Member B (GNN + Explainable AI Module)

Computes feature-level attributions for automata classification models.
Analyzes how much specific topological and simulation features—such as
`is_start`, `is_accepting`, `in_degree`, `out_degree`, `visit_frequency`,
and `final_state_match`—contributed toward accepting or rejecting the input string.
"""

from typing import Dict, Any, List, Optional
import math
import itertools

try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


from backend.xai_engine.constants import NODE_FEATURE_NAMES


class AutomataSHAPExplainer:
    """
    Computes game-theoretic Shapley values / feature attributions over graph & trace features.
    Provides rigorous exact Shapley permutation computation against the trained GNN model,
    with seamless fallback when PyTorch or models are not available.
    """

    FEATURE_NAMES = list(NODE_FEATURE_NAMES)

    def __init__(self):
        pass

    def explain(
        self,
        model: Any,
        graph_rep: Any,
        target_class: Optional[int] = None,
    ) -> Dict[str, float]:
        """
        Calculates feature importance attributions conforming strictly to docs/json_schema.md.

        Args:
            model: Trained AutomataGNNClassifier instance.
            graph_rep: GraphRepresentation container.
            target_class: Optional target class (0 or 1). If None, uses model argmax prediction.

        Returns:
            Dict[str, float]: Mapping from feature name to relative attribution score in [0.0, 1.0].
        """
        if TORCH_AVAILABLE and model is not None and hasattr(graph_rep, "node_features") and hasattr(graph_rep.node_features, "shape"):
            try:
                return self._compute_model_shapley_values(model, graph_rep, target_class)
            except Exception:
                # If model evaluation fails, use fallback attribution
                pass

        return self._fallback_attribution(graph_rep)

    def _compute_model_shapley_values(
        self,
        model: Any,
        graph_rep: Any,
        target_class: Optional[int] = None,
    ) -> Dict[str, float]:
        """
        Computes exact game-theoretic Shapley values across the 6 node feature dimensions
        by evaluating model class probabilities under all 2^6 = 64 feature subsets.
        """
        x = graph_rep.node_features
        edge_index = graph_rep.edge_index
        n_feats = len(self.FEATURE_NAMES)

        model.eval()
        with torch.no_grad():
            orig_logits = model(x, edge_index)
            pred_class = torch.argmax(orig_logits, dim=1).item()
            target = pred_class if target_class is None else target_class

        # Precompute model class probability for all 2^n_feats subsets
        subset_probs: Dict[int, float] = {}
        for mask_int in range(1 << n_feats):
            mask_vec = torch.tensor(
                [(1.0 if (mask_int & (1 << j)) else 0.0) for j in range(n_feats)],
                dtype=x.dtype,
                device=x.device,
            )
            x_masked = x * mask_vec.unsqueeze(0)
            with torch.no_grad():
                logits = model(x_masked, edge_index)
                prob = F.softmax(logits, dim=1)[0, target].item()
                subset_probs[mask_int] = prob

        # Compute marginal contributions across all coalition sizes
        factorial = math.factorial
        raw_shapley: Dict[str, float] = {}

        for i in range(n_feats):
            phi_i = 0.0
            other_indices = [j for j in range(n_feats) if j != i]
            for s_size in range(n_feats):
                weight = (factorial(s_size) * factorial(n_feats - s_size - 1)) / float(factorial(n_feats))
                for subset in itertools.combinations(other_indices, s_size):
                    s_mask = sum(1 << j for j in subset)
                    s_plus_i = s_mask | (1 << i)
                    marginal_gain = subset_probs[s_plus_i] - subset_probs[s_mask]
                    phi_i += weight * marginal_gain

            raw_shapley[self.FEATURE_NAMES[i]] = phi_i

        # Normalize absolute importance scores to sum to 1.0
        abs_sum = sum(abs(v) for v in raw_shapley.values())
        if abs_sum < 1e-7:
            return {name: round(1.0 / n_feats, 4) for name in self.FEATURE_NAMES}

        normalized = {k: round(abs(v) / abs_sum, 4) for k, v in raw_shapley.items()}
        return normalized

    def _fallback_attribution(self, graph_rep: Any) -> Dict[str, float]:
        """Provides heuristic baseline attribution when PyTorch/model is not available."""
        x = getattr(graph_rep, "node_features", [])
        if hasattr(x, "cpu"):
            features_np = x.detach().cpu().numpy()
        else:
            features_np = x

        if len(features_np) == 0:
            return {name: 0.0 for name in self.FEATURE_NAMES}

        dim_means = []
        for col_idx in range(min(len(self.FEATURE_NAMES), len(features_np[0]))):
            col_vals = [row[col_idx] for row in features_np]
            dim_means.append(sum(col_vals) / float(len(col_vals)))

        weights = [0.10, 0.40, 0.10, 0.08, 0.22, 0.35]
        raw_scores: Dict[str, float] = {}
        for idx, name in enumerate(self.FEATURE_NAMES):
            mean_val = dim_means[idx] if idx < len(dim_means) else 0.0
            weight = weights[idx] if idx < len(weights) else 0.1
            raw_scores[name] = max(0.01, float(mean_val * weight))

        total = sum(raw_scores.values()) or 1.0
        return {k: round(v / total, 4) for k, v in raw_scores.items()}

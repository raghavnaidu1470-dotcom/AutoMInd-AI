"""
Automata GNNExplainer Module
============================
Owned by: Member B (GNN + Explainable AI Module)

Implements subgraph and edge attribution extraction for Automata GNNs.
Given a trained `AutomataGNNClassifier` and an automaton graph, this module
optimizes an edge mask M in [0, 1]^E that identifies the minimal subgraph
governing whether the input string is recognized or rejected.

Objective:
  max_M  P(Y = y_pred | G_masked) - lambda_1 * ||M||_1 - lambda_2 * Entropy(M)
"""

from typing import Dict, List, Any, Optional, Tuple
import math

try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class AutomataGNNExplainer:
    """
    Computes node and edge importance scores using an edge-mask optimization
    formulation inspired by GNNExplainer (Ying et al., NeurIPS 2019).
    """

    def __init__(
        self,
        epochs: int = 40,
        lr: float = 0.05,
        mask_entropy_weight: float = 0.01,
        mask_size_weight: float = 0.005,
    ):
        self.epochs = epochs
        self.lr = lr
        self.mask_entropy_weight = mask_entropy_weight
        self.mask_size_weight = mask_size_weight

    def explain(
        self,
        model: Any,
        graph_rep: Any,
        target_class: Optional[int] = None,
        top_k_edges: int = 5,
    ) -> Dict[str, Any]:
        """
        Extracts node and edge importance metrics.

        Args:
            model: Trained AutomataGNNClassifier instance.
            graph_rep: GraphRepresentation containing node_features, edge_index, edge_tuples.
            target_class: Target class index to explain (0 or 1). If None, uses model prediction.
            top_k_edges: Number of edges to include in the critical subgraph.

        Returns:
            Dictionary matching the XAI output schema:
              - node_importance: Dict[str, float]
              - edge_importance: List[Dict]
              - critical_subgraph: Dict
              - explanation_summary: str
        """
        if not TORCH_AVAILABLE:
            return self._fallback_explanation(graph_rep)

        x = graph_rep.node_features
        edge_index = graph_rep.edge_index
        num_edges = graph_rep.num_edges
        num_nodes = graph_rep.num_nodes
        node_ids = graph_rep.node_ids
        edge_tuples = graph_rep.edge_tuples

        if num_edges == 0:
            return {
                "node_importance": {nid: 1.0 for nid in node_ids},
                "edge_importance": [],
                "critical_subgraph": {"nodes": node_ids, "edges": []},
                "explanation_summary": "Graph has no transitions to explain.",
            }

        # Determine target class
        model.eval()
        with torch.no_grad():
            orig_logits = model(x, edge_index)
            pred_class = torch.argmax(orig_logits, dim=1).item()
        target = pred_class if target_class is None else target_class

        # Initialize learnable edge mask parameter
        edge_mask_param = torch.nn.Parameter(torch.randn(num_edges) * 0.1)
        optimizer = torch.optim.Adam([edge_mask_param], lr=self.lr)

        # Optimization loop
        for _ in range(self.epochs):
            optimizer.zero_grad()
            mask = torch.sigmoid(edge_mask_param)

            logits = model(x, edge_index, edge_weight=mask)
            prob = F.softmax(logits, dim=1)[0, target]

            # Cross entropy / log-prob loss
            pred_loss = -torch.log(prob + 1e-8)
            size_loss = torch.mean(mask)
            entropy = -mask * torch.log(mask + 1e-8) - (1 - mask) * torch.log(1 - mask + 1e-8)
            entropy_loss = torch.mean(entropy)

            loss = pred_loss + self.mask_size_weight * size_loss + self.mask_entropy_weight * entropy_loss
            loss.backward()
            optimizer.step()

        # Extract normalized edge importance
        with torch.no_grad():
            final_mask = torch.sigmoid(edge_mask_param).cpu().numpy().tolist()

        # Normalize edge importance into [0.0, 1.0]
        max_m = max(final_mask) if final_mask else 1.0
        min_m = min(final_mask) if final_mask else 0.0
        rng = (max_m - min_m) if (max_m - min_m) > 1e-6 else 1.0
        norm_edge_scores = [(s - min_m) / rng for s in final_mask]

        # Aggregate node importance from incident edge importance + node features
        node_importance_dict: Dict[str, float] = {nid: 0.05 for nid in node_ids}
        edge_importance_list: List[Dict[str, Any]] = []

        for idx, (u, v, sym) in enumerate(edge_tuples):
            score = round(float(norm_edge_scores[idx]), 4)
            edge_importance_list.append({
                "from_state": u,
                "to_state": v,
                "symbol": sym,
                "importance": score,
            })
            # Accumulate on endpoint nodes
            node_importance_dict[u] = max(node_importance_dict.get(u, 0.0), score * 0.9)
            node_importance_dict[v] = max(node_importance_dict.get(v, 0.0), score)

        # Sort edges by descending importance
        edge_importance_list.sort(key=lambda item: item["importance"], reverse=True)

        # Top critical subgraph
        critical_edges = edge_importance_list[:top_k_edges]
        critical_node_set = set()
        for ce in critical_edges:
            critical_node_set.add(ce["from_state"])
            critical_node_set.add(ce["to_state"])

        critical_subgraph = {
            "nodes": sorted(list(critical_node_set)),
            "edges": [
                {"from_state": e["from_state"], "to_state": e["to_state"], "symbol": e["symbol"]}
                for e in critical_edges
            ],
        }

        # Build natural language summary
        if critical_edges:
            top_e = critical_edges[0]
            action = "accepted" if target == 1 else "rejected"
            summary = (
                f"Transition {top_e['from_state']} --'{top_e['symbol']}'--> {top_e['to_state']} "
                f"was the most influential factor (importance: {top_e['importance']:.2f}) in classifying "
                f"the string as {action}."
            )
        else:
            summary = "No decisive transition subgraph identified."

        return {
            "node_importance": {k: round(v, 4) for k, v in node_importance_dict.items()},
            "edge_importance": edge_importance_list,
            "critical_subgraph": critical_subgraph,
            "explanation_summary": summary,
        }

    def _fallback_explanation(self, graph_rep: Any) -> Dict[str, Any]:
        """Provides heuristic fallback attribution when PyTorch is unavailable."""
        node_ids = graph_rep.node_ids
        edge_tuples = graph_rep.edge_tuples

        edge_list = []
        for u, v, sym in edge_tuples:
            edge_list.append({
                "from_state": u,
                "to_state": v,
                "symbol": sym,
                "importance": 0.5,
            })

        return {
            "node_importance": {nid: 0.5 for nid in node_ids},
            "edge_importance": edge_list,
            "critical_subgraph": {
                "nodes": node_ids[:3] if len(node_ids) >= 3 else node_ids,
                "edges": [{"from_state": e["from_state"], "to_state": e["to_state"], "symbol": e["symbol"]} for e in edge_list[:2]],
            },
            "explanation_summary": "Heuristic fallback attribution generated.",
        }

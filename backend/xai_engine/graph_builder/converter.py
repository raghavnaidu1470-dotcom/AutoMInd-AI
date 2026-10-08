"""
Automata Graph Converter
========================
Owned by: Member B (GNN + Explainable AI Module)

Converts Automaton definitions and Execution Traces into tensor-based graph
representations suitable for GNN ingestion (e.g. PyTorch / PyTorch Geometric).

Node Features Matrix X (shape [N, num_node_features]):
  0: is_start (0.0 or 1.0)
  1: is_accepting (0.0 or 1.0)
  2: in_degree (normalized)
  3: out_degree (normalized)
  4: visit_frequency (frequency of state visits in simulation trace)
  5: final_state_match (1.0 if state was active at the end of simulation)

Edge Index E (shape [2, num_edges]):
  Directed edge source and target node indices.

Edge Features Matrix E_attr (shape [num_edges, num_edge_features]):
  0: symbol_index (normalized integer encoding of alphabet character)
  1: is_traversed (1.0 if this edge was traversed in the simulation trace, else 0.0)
  2: traversal_frequency (normalized count of times traversed)
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import math

from backend.xai_engine.constants import (
    NODE_FEATURE_NAMES,
    NODE_FEATURE_DIM,
    EDGE_FEATURE_NAMES,
    EDGE_FEATURE_DIM,
)

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@dataclass
class GraphRepresentation:
    """Standardized graph container used across the GNN & XAI modules."""
    node_ids: List[str]
    node_to_idx: Dict[str, int]
    idx_to_node: Dict[int, str]
    node_features: Any                 # List[List[float]] or torch.FloatTensor [N, F_node]
    edge_index: Any                    # List[List[int]] or torch.LongTensor [2, M]
    edge_features: Any                 # List[List[float]] or torch.FloatTensor [M, F_edge]
    edge_tuples: List[Tuple[str, str, str]]  # [(from_state, to_state, symbol), ...]
    num_nodes: int
    num_edges: int

    def to_pyg_data(self):
        """Converts to a PyTorch Geometric Data object if torch_geometric is installed."""
        try:
            from torch_geometric.data import Data
            import torch
            return Data(
                x=torch.as_tensor(self.node_features, dtype=torch.float32),
                edge_index=torch.as_tensor(self.edge_index, dtype=torch.long),
                edge_attr=torch.as_tensor(self.edge_features, dtype=torch.float32),
                num_nodes=self.num_nodes,
            )
        except ImportError:
            raise ImportError("torch_geometric is not installed in the environment.")


class AutomataGraphConverter:
    """
    Transforms canonical Automaton and Simulation Trace JSON/objects into
    tensor graph feature representations.
    """

    NODE_FEATURE_DIM = NODE_FEATURE_DIM
    EDGE_FEATURE_DIM = EDGE_FEATURE_DIM
    NODE_FEATURE_NAMES = NODE_FEATURE_NAMES
    EDGE_FEATURE_NAMES = EDGE_FEATURE_NAMES

    def __init__(self):
        pass

    def convert(
        self,
        automaton_data: Any,
        simulation_trace: Optional[Any] = None,
        as_tensors: bool = True,
    ) -> GraphRepresentation:
        """
        Converts an automaton and optional simulation trace into a GraphRepresentation.

        Args:
            automaton_data: Automaton instance or dictionary conforming to docs/json_schema.md.
            simulation_trace: Optional SimulationResult instance or dictionary.
            as_tensors: If True, wraps features in torch tensors if torch is available.

        Returns:
            GraphRepresentation containing node indices, edge indices, and feature matrices.
        """
        data = automaton_data.model_dump() if hasattr(automaton_data, "model_dump") else automaton_data
        states = data.get("states", [])
        transitions = data.get("transitions", [])
        alphabet = sorted(list(set(data.get("alphabet", []))))

        # Build symbol encoding mapping (1-indexed, 0 reserved for epsilon/unknown)
        symbol_map = {sym: (i + 1) for i, sym in enumerate(alphabet)}
        symbol_map["ε"] = 0
        symbol_map[""] = 0

        # State ID index mapping
        node_ids = [s["id"] for s in states]
        node_to_idx = {sid: idx for idx, sid in enumerate(node_ids)}
        idx_to_node = {idx: sid for idx, sid in enumerate(node_ids)}
        num_nodes = len(node_ids)

        # Parse trace information if provided
        trace_data = None
        if simulation_trace is not None:
            trace_data = (
                simulation_trace.model_dump()
                if hasattr(simulation_trace, "model_dump")
                else simulation_trace
            )

        node_visit_counts: Dict[str, int] = {sid: 0 for sid in node_ids}
        edge_traversal_counts: Dict[Tuple[str, str, str], int] = {}
        final_states_set = set()

        if trace_data:
            final_states_set = set(trace_data.get("final_states", []))
            for step in trace_data.get("steps", []):
                for cur_s in step.get("current_states", []):
                    if cur_s in node_visit_counts:
                        node_visit_counts[cur_s] += 1
                trans = step.get("transition_taken")
                if trans:
                    key = (trans.get("from_state"), trans.get("to_state"), trans.get("symbol"))
                    edge_traversal_counts[key] = edge_traversal_counts.get(key, 0) + 1

        # Calculate degrees
        in_degrees: Dict[str, int] = {sid: 0 for sid in node_ids}
        out_degrees: Dict[str, int] = {sid: 0 for sid in node_ids}
        for t in transitions:
            u, v = t.get("from_state"), t.get("to_state")
            if u in out_degrees:
                out_degrees[u] += 1
            if v in in_degrees:
                in_degrees[v] += 1

        max_in = max(in_degrees.values()) if in_degrees else 1
        max_out = max(out_degrees.values()) if out_degrees else 1
        max_visits = max(node_visit_counts.values()) if node_visit_counts else 1
        max_in = max(max_in, 1)
        max_out = max(max_out, 1)
        max_visits = max(max_visits, 1)

        # Build Node Features Matrix
        node_features: List[List[float]] = []
        for s in states:
            sid = s["id"]
            is_start = 1.0 if s.get("is_start", False) else 0.0
            is_accept = 1.0 if s.get("is_accepting", False) else 0.0
            in_deg_norm = in_degrees.get(sid, 0) / float(max_in)
            out_deg_norm = out_degrees.get(sid, 0) / float(max_out)
            visit_norm = node_visit_counts.get(sid, 0) / float(max_visits)
            is_final = 1.0 if sid in final_states_set else 0.0

            node_features.append([
                is_start,
                is_accept,
                in_deg_norm,
                out_deg_norm,
                visit_norm,
                is_final,
            ])

        # Build Edge Index and Edge Features
        src_indices: List[int] = []
        dst_indices: List[int] = []
        edge_features: List[List[float]] = []
        edge_tuples: List[Tuple[str, str, str]] = []

        max_edge_traversals = max(edge_traversal_counts.values()) if edge_traversal_counts else 1
        max_edge_traversals = max(max_edge_traversals, 1)
        alphabet_size = max(len(alphabet), 1)

        for t in transitions:
            u, v, sym = t.get("from_state"), t.get("to_state"), t.get("symbol", "")
            if u not in node_to_idx or v not in node_to_idx:
                continue

            src_idx = node_to_idx[u]
            dst_idx = node_to_idx[v]
            src_indices.append(src_idx)
            dst_indices.append(dst_idx)

            key = (u, v, sym)
            edge_tuples.append(key)

            sym_encoded = symbol_map.get(sym, 0) / float(alphabet_size + 1)
            t_count = edge_traversal_counts.get(key, 0)
            is_traversed = 1.0 if t_count > 0 else 0.0
            traversal_norm = t_count / float(max_edge_traversals)

            edge_features.append([sym_encoded, is_traversed, traversal_norm])

        num_edges = len(src_indices)
        edge_index = [src_indices, dst_indices]

        # Wrap in PyTorch tensors if available and requested
        if as_tensors and TORCH_AVAILABLE:
            node_features_tensor = torch.tensor(node_features, dtype=torch.float32)
            edge_index_tensor = torch.tensor(edge_index, dtype=torch.long)
            edge_features_tensor = torch.tensor(edge_features, dtype=torch.float32) if num_edges > 0 else torch.zeros((0, self.EDGE_FEATURE_DIM), dtype=torch.float32)
            return GraphRepresentation(
                node_ids=node_ids,
                node_to_idx=node_to_idx,
                idx_to_node=idx_to_node,
                node_features=node_features_tensor,
                edge_index=edge_index_tensor,
                edge_features=edge_features_tensor,
                edge_tuples=edge_tuples,
                num_nodes=num_nodes,
                num_edges=num_edges,
            )

        return GraphRepresentation(
            node_ids=node_ids,
            node_to_idx=node_to_idx,
            idx_to_node=idx_to_node,
            node_features=node_features,
            edge_index=edge_index,
            edge_features=edge_features,
            edge_tuples=edge_tuples,
            num_nodes=num_nodes,
            num_edges=num_edges,
        )

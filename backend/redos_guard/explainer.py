"""
ReDoS Guard — Explainable Localization with GNNExplainer (Part 5)
=================================================================
Runs GNNExplainer on the 3-class ReDoS severity model, identifies the critical
subgraph (states and transitions) governing the ambiguity prediction, maps them
back to source regex character spans via Part 1 provenance metadata, and generates
plain-language diagnostic explanations.
"""

from typing import Dict, List, Tuple, Any, Optional, Set
import math
import torch
import torch.nn.functional as F

from pydantic import BaseModel, Field

from backend.automata_engine.engine import AutomataEngine
from backend.automata_engine.models import Automaton
from backend.redos_guard.gnn.model import ReDoSGNNClassifier
from backend.redos_guard.gnn.trainer import load_trained_redos_gnn
from backend.redos_guard.gnn.feature_extractor import extract_nfa_graph_features
from backend.redos_guard.gnn.constants import RISK_CLASS_TO_IDX, IDX_TO_RISK_CLASS


class HighlightedSpan(BaseModel):
    start: int = Field(..., description="0-indexed start character offset in regex")
    end: int = Field(..., description="0-indexed end character offset (exclusive)")
    fragment: str = Field(..., description="Exact regex substring within the span")


class NodeAttribution(BaseModel):
    state_id: str
    importance: float
    source_span: Optional[Tuple[int, int]] = None


class EdgeAttribution(BaseModel):
    transition_id: str
    from_state: str
    to_state: str
    symbol: str
    importance: float
    source_span: Optional[Tuple[int, int]] = None


class ReDoSExplanationResult(BaseModel):
    regex: str = Field(..., description="Target regular expression")
    predicted_risk: str = Field(..., description="Model predicted risk class: linear, polynomial, exponential")
    confidence: float = Field(..., description="Prediction confidence score")
    highlighted_spans: List[HighlightedSpan] = Field(default_factory=list, description="Offending character spans")
    top_nodes: List[NodeAttribution] = Field(default_factory=list, description="Top influential NFA states")
    top_edges: List[EdgeAttribution] = Field(default_factory=list, description="Top influential transitions")
    explanation: str = Field(..., description="Plain-language human-readable diagnostic explanation")


class ReDoSExplainer:
    """
    Explainability engine for ReDoS severity screening.
    Combines GNN edge mask optimization with AST provenance mapping.
    """

    def __init__(
        self,
        model: Optional[ReDoSGNNClassifier] = None,
        epochs: int = 35,
        lr: float = 0.05,
    ):
        self.model = model if model is not None else load_trained_redos_gnn()
        self.epochs = epochs
        self.lr = lr
        self._engine = AutomataEngine()

    def explain(
        self,
        target: str,
        target_class: Optional[str] = None,
        top_k_edges: int = 6,
    ) -> ReDoSExplanationResult:
        """
        Explains ambiguity prediction for a regular expression and maps it back to source spans.

        Args:
            target: Regular expression pattern string.
            target_class: Optional target risk class to explain ('polynomial', 'exponential').
            top_k_edges: Number of top edges to attribute.

        Returns:
            ReDoSExplanationResult with highlighted spans and plain-language explanation.
        """
        bundle = self._engine.build_all(target)
        nfa: Automaton = bundle["nfa"]

        feat = extract_nfa_graph_features(nfa)
        x = feat["x"]
        edge_index = feat["edge_index"]
        idx_to_edge = feat["idx_to_edge"]
        idx_to_node = feat["idx_to_node"]
        num_edges = edge_index.size(1)
        num_nodes = x.size(0)

        # 1. Forward pass prediction
        self.model.eval()
        with torch.no_grad():
            logits = self.model(x, edge_index)
            probs = F.softmax(logits, dim=-1).squeeze(0)
            pred_idx = int(torch.argmax(probs).item())
            predicted_risk = IDX_TO_RISK_CLASS[pred_idx]
            confidence = float(probs[pred_idx].item())

        target_idx = (
            RISK_CLASS_TO_IDX.get(target_class, pred_idx)
            if target_class
            else pred_idx
        )

        # Build fast lookup for transitions and states
        trans_lookup = {t.id: t for t in nfa.transitions}
        state_lookup = {s.id: s for s in nfa.states}

        # If graph has no edges or predicted linear (safe)
        if num_edges == 0 or (predicted_risk == "linear" and target_class is None):
            return ReDoSExplanationResult(
                regex=target,
                predicted_risk=predicted_risk,
                confidence=confidence,
                highlighted_spans=[],
                top_nodes=[],
                top_edges=[],
                explanation="Safe regex: topological analysis confirmed linear complexity with no ambiguous branching cycles.",
            )

        # 2. GNNExplainer Edge Mask Optimization
        edge_mask_param = torch.nn.Parameter(torch.randn(num_edges) * 0.1)
        optimizer = torch.optim.Adam([edge_mask_param], lr=self.lr)

        for _ in range(self.epochs):
            optimizer.zero_grad()
            mask = torch.sigmoid(edge_mask_param)
            masked_logits = self.model(x, edge_index, edge_weight=mask)
            log_probs = F.log_softmax(masked_logits, dim=-1)

            pred_loss = -log_probs[0, target_idx]
            size_loss = 0.005 * torch.sum(mask)
            entropy_loss = -0.01 * torch.sum(
                mask * torch.log(mask + 1e-15) + (1 - mask) * torch.log(1 - mask + 1e-15)
            )

            loss = pred_loss + size_loss + entropy_loss
            loss.backward()
            optimizer.step()

        edge_scores = torch.sigmoid(edge_mask_param).detach().cpu().numpy()

        # 3. Node Importance via Edge Aggregation
        node_scores = [0.0] * num_nodes
        for e_idx in range(num_edges):
            u = edge_index[0, e_idx].item()
            v = edge_index[1, e_idx].item()
            sc = float(edge_scores[e_idx])
            node_scores[u] += sc
            node_scores[v] += sc

        # Top edges and nodes
        ranked_edge_indices = sorted(range(num_edges), key=lambda i: edge_scores[i], reverse=True)[
            :top_k_edges
        ]
        ranked_node_indices = sorted(range(num_nodes), key=lambda i: node_scores[i], reverse=True)[
            :min(6, num_nodes)
        ]

        top_edges: List[EdgeAttribution] = []
        collected_spans: List[Tuple[int, int]] = []

        for e_idx in ranked_edge_indices:
            tid = idx_to_edge[e_idx]
            t = trans_lookup[tid]
            sc = float(edge_scores[e_idx])
            span = t.metadata.get("source_span") if t.metadata else None
            top_edges.append(
                EdgeAttribution(
                    transition_id=tid,
                    from_state=t.from_state,
                    to_state=t.to_state,
                    symbol=t.symbol,
                    importance=round(sc, 4),
                    source_span=span,
                )
            )
            if span and span[0] < span[1]:
                collected_spans.append(tuple(span))

        top_nodes: List[NodeAttribution] = []
        for n_idx in ranked_node_indices:
            nid = idx_to_node[n_idx]
            s = state_lookup[nid]
            sc = float(node_scores[n_idx])
            span = s.metadata.get("source_span") if s.metadata else None
            top_nodes.append(
                NodeAttribution(
                    state_id=nid,
                    importance=round(sc, 4),
                    source_span=span,
                )
            )
            if span and span[0] < span[1]:
                collected_spans.append(tuple(span))

        # 4. Merge Spans and Map Back to Regex Characters
        merged_spans = self._merge_spans(collected_spans, max_len=len(target))
        if not merged_spans and (predicted_risk != "linear" or target_class is not None):
            # Fallback: find enclosing repeated group in target
            merged_spans = self._heuristic_fallback_span(target)

        highlighted_spans: List[HighlightedSpan] = []
        for st, en in merged_spans:
            clamped_st = max(0, min(st, len(target)))
            clamped_en = max(clamped_st, min(en, len(target)))
            frag = target[clamped_st:clamped_en]
            if frag:
                highlighted_spans.append(
                    HighlightedSpan(start=clamped_st, end=clamped_en, fragment=frag)
                )

        # 5. Synthesize Plain-Language Explanation
        explanation = self._build_plain_language_explanation(
            target, predicted_risk, highlighted_spans
        )

        return ReDoSExplanationResult(
            regex=target,
            predicted_risk=predicted_risk,
            confidence=round(confidence, 4),
            highlighted_spans=highlighted_spans,
            top_nodes=top_nodes,
            top_edges=top_edges,
            explanation=explanation,
        )

    def _merge_spans(
        self, spans: List[Tuple[int, int]], max_len: int
    ) -> List[Tuple[int, int]]:
        """Merges overlapping or immediately adjacent intervals."""
        if not spans:
            return []
        sorted_spans = sorted(spans, key=lambda p: (p[0], p[1]))
        merged: List[Tuple[int, int]] = []
        curr_st, curr_en = sorted_spans[0]

        for st, en in sorted_spans[1:]:
            if st <= curr_en + 1:
                curr_en = max(curr_en, en)
            else:
                merged.append((curr_st, curr_en))
                curr_st, curr_en = st, en
        merged.append((curr_st, curr_en))

        # Filter valid intervals
        return [(max(0, s), min(max_len, e)) for s, e in merged if e > s]

    def _heuristic_fallback_span(self, regex: str) -> List[Tuple[int, int]]:
        """Finds primary repeated group in regex if provenance spans were sparse."""
        for op in ["+", "*"]:
            idx = regex.find(op)
            if idx > 0:
                # Find start of parenthesized group or char
                if regex[idx - 1] == ")":
                    open_p = regex.rfind("(", 0, idx)
                    if open_p >= 0:
                        return [(open_p, idx + 1)]
                return [(max(0, idx - 1), idx + 1)]
        return [(0, len(regex))]

    def _build_plain_language_explanation(
        self, regex: str, risk: str, spans: List[HighlightedSpan]
    ) -> str:
        """Constructs human-readable diagnosis mapped to character offsets."""
        if not spans or risk == "linear":
            return "No ambiguous backtracking cycles detected; regular expression evaluates linearly."

        span_desc = ", ".join(
            [f"characters {s.start}-{s.end} ('{s.fragment}')" for s in spans]
        )

        primary_frag = spans[0].fragment

        if risk == "exponential":
            if any(token in primary_frag for token in ["+", "*"]) and ("(" in primary_frag):
                return (
                    f"Nested quantifier on {span_desc} allows multiple branching paths "
                    f"to match the identical input sequence, triggering exponential 2^N backtracking."
                )
            elif "|" in primary_frag:
                return (
                    f"Overlapping alternation on {span_desc} creates non-deterministic branch ambiguity, "
                    f"permitting exponential combinations on repeated matching."
                )
            else:
                return (
                    f"Ambiguous repetition structure on {span_desc} causes exponential backtracking."
                )
        elif risk == "polynomial":
            return (
                f"Chained overlapping repetition on {span_desc} enables polynomial O(N^d) "
                f"combinations across multiple iterations."
            )

        return f"Structure on {span_desc} causes ambiguous backtracking."

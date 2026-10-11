"""
ReDoS Guard — GNN Training, Family-Stratified Evaluation & Timing Benchmark
===========================================================================
Trains the 3-class ReDoSGNNClassifier on NFA graph representations using strict
family-stratified data splits (zero family or template leakage between train and test).

Measures and reports:
  1. Held-out test accuracy, per-class recall, and 3x3 confusion matrix.
  2. Fair timing across NFA families of increasing size k:
     (a) End-to-end (parse + NFA + features + inference) vs end-to-end exact analyzer.
     (b) Inference-only vs analysis-only on the SAME prebuilt NFA.
     Repeated runs with median latency reporting.
  3. Complexity analysis: Removes any O(1) claims; documents O(|V| + |E|) GNN complexity
     versus O(|V|^2 + |E|^2) exact pair-graph analysis.
"""

import os
import time
import random
from typing import Dict, Any, List, Tuple, Optional
import statistics
import json

import torch
import torch.nn as nn
import torch.optim as optim

from backend.automata_engine.engine import AutomataEngine
from backend.redos_guard.analyzer import AmbiguityAnalyzer
from backend.redos_guard.gnn.model import ReDoSGNNClassifier
from backend.redos_guard.gnn.feature_extractor import extract_nfa_graph_features
from backend.redos_guard.gnn.dataset import (
    get_family_stratified_dataset,
    extract_regex_template,
)
from backend.redos_guard.gnn.constants import (
    NUM_RISK_CLASSES,
    RISK_CLASS_NAMES,
    IDX_TO_RISK_CLASS,
)


MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/models"))
MODEL_PATH = os.path.join(MODEL_DIR, "redos_gnn.pt")


def prepare_graph_samples(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts regex dataset into PyTorch geometric graph samples."""
    engine = AutomataEngine()
    graph_samples: List[Dict[str, Any]] = []

    for item in dataset:
        try:
            nfa = engine.build_nfa(item["regex"])
            feat = extract_nfa_graph_features(nfa)
            graph_samples.append(
                {
                    "regex": item["regex"],
                    "family": item["family"],
                    "template": item["template"],
                    "label": item["label"],
                    "risk_class": item["risk_class"],
                    "x": feat["x"],
                    "edge_index": feat["edge_index"],
                    "n_states": len(nfa.states),
                    "n_trans": len(nfa.transitions),
                }
            )
        except Exception:
            continue

    return graph_samples


def train_redos_gnn(
    epochs: int = 45,
    lr: float = 0.008,
    seed: int = 42,
    save_model: bool = True,
) -> Dict[str, Any]:
    """
    Trains ReDoSGNNClassifier on family-stratified train set and evaluates on
    held-out family-stratified test set.
    """
    torch.manual_seed(seed)
    random.seed(seed)

    raw_train, raw_test = get_family_stratified_dataset()

    # Assert zero overlap
    train_fams = {s["family"] for s in raw_train}
    test_fams = {s["family"] for s in raw_test}
    assert train_fams.isdisjoint(test_fams), f"Family overlap: {train_fams & test_fams}"

    train_tmps = {s["template"] for s in raw_train}
    test_tmps = {s["template"] for s in raw_test}
    assert train_tmps.isdisjoint(test_tmps), f"Template overlap: {train_tmps & test_tmps}"

    train_samples = prepare_graph_samples(raw_train)
    test_samples = prepare_graph_samples(raw_test)

    model = ReDoSGNNClassifier(hidden_dim=32, num_classes=NUM_RISK_CLASSES)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()

    # Training loop
    model.train()
    for epoch in range(epochs):
        random.shuffle(train_samples)
        total_loss = 0.0
        for s in train_samples:
            optimizer.zero_grad()
            logits = model(s["x"], s["edge_index"])
            target = torch.tensor([s["label"]], dtype=torch.long)
            loss = criterion(logits, target)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

    # Evaluation on held-out test split
    model.eval()
    correct = 0
    total = len(test_samples)
    classes = [0, 1, 2]
    class_names = ["linear", "polynomial", "exponential"]

    # 3x3 Confusion Matrix: [actual][predicted]
    conf_matrix = {c: {p: 0 for p in classes} for c in classes}

    with torch.no_grad():
        for s in test_samples:
            logits = model(s["x"], s["edge_index"])
            pred = int(torch.argmax(logits, dim=-1).item())
            lbl = s["label"]
            conf_matrix[lbl][pred] += 1
            if pred == lbl:
                correct += 1

    test_accuracy = correct / max(total, 1)

    # Per-class recall and precision
    per_class_metrics = {}
    for c in classes:
        name = class_names[c]
        tp = conf_matrix[c][c]
        fn = sum(conf_matrix[c][p] for p in classes if p != c)
        fp = sum(conf_matrix[a][c] for a in classes if a != c)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        per_class_metrics[name] = {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "total_actual": tp + fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        }

    # Named confusion matrix for readability
    named_matrix = {
        class_names[act]: {class_names[pred]: conf_matrix[act][pred] for pred in classes}
        for act in classes
    }

    if save_model:
        os.makedirs(MODEL_DIR, exist_ok=True)
        torch.save(model.state_dict(), MODEL_PATH)

    return {
        "train_samples": len(train_samples),
        "test_samples": len(test_samples),
        "test_accuracy": round(test_accuracy, 4),
        "per_class_metrics": per_class_metrics,
        "confusion_matrix": named_matrix,
        "model_path": MODEL_PATH if save_model else None,
    }


def run_fair_timing_benchmark(
    repeats: int = 15,
) -> Dict[str, Any]:
    """
    Performs rigorous, fair timing benchmark comparing:
      (a) End-to-end: Parse + NFA construction + Feature extraction + GNN inference
          versus End-to-end Exact Analyzer (Parse + NFA construction + Pair Graph G2).
      (b) Isolated: GNN forward pass on pre-extracted features
          versus Exact Analyzer on the SAME prebuilt NFA.

    Evaluates across generated NFA families of increasing size k:
      1. k chained stars: a* repeated k times + b (Polynomial family)
      2. k-way overlapping alternations: (a|aa|...|a^k)+ (Exponential family)
      3. k disjoint concatenated tokens: a_1+ a_2+ ... a_k+ (Linear family)

    Reports medians over repeated runs.
    """
    engine = AutomataEngine()
    analyzer = AmbiguityAnalyzer(timeout_sec=5.0)
    model = load_trained_redos_gnn()
    model.eval()

    benchmark_suite = []

    # 1. Chained stars of increasing length k (Polynomial)
    for k in [2, 4, 6, 8, 10, 14]:
        pattern = "".join(f"a*" for _ in range(k)) + "b"
        benchmark_suite.append({"family": "chained_stars", "k": k, "pattern": pattern})

    # 2. Overlapping alternations of increasing branch length k (Exponential)
    for k in [2, 3, 4, 5, 6]:
        branches = "|".join("a" * i for i in range(1, k + 1))
        pattern = f"({branches})+"
        benchmark_suite.append({"family": "overlapping_alternations", "k": k, "pattern": pattern})

    # 3. Disjoint sequences of increasing length k (Linear)
    for k in [2, 4, 6, 8, 10, 14]:
        pattern = "".join(f"c{i}+" for i in range(k))
        benchmark_suite.append({"family": "disjoint_sequences", "k": k, "pattern": pattern})

    results = []

    for entry in benchmark_suite:
        pat = entry["pattern"]
        k_val = entry["k"]
        fam = entry["family"]

        try:
            # Prebuild NFA and features for isolated comparison
            nfa = engine.build_nfa(pat)
            n_states = len(nfa.states)
            n_trans = len(nfa.transitions)
            feat = extract_nfa_graph_features(nfa)
            x, edge_index = feat["x"], feat["edge_index"]

            # (a) End-to-end timing
            e2e_gnn_times: List[float] = []
            for _ in range(repeats):
                t0 = time.perf_counter()
                b_nfa = engine.build_nfa(pat)
                f = extract_nfa_graph_features(b_nfa)
                with torch.no_grad():
                    model(f["x"], f["edge_index"])
                e2e_gnn_times.append((time.perf_counter() - t0) * 1000.0)

            e2e_exact_times: List[float] = []
            for _ in range(repeats):
                t0 = time.perf_counter()
                b_nfa = engine.build_nfa(pat)
                analyzer.analyze(b_nfa)
                e2e_exact_times.append((time.perf_counter() - t0) * 1000.0)

            # (b) Isolated timing on SAME prebuilt NFA
            isolated_gnn_times: List[float] = []
            with torch.no_grad():
                for _ in range(repeats):
                    t0 = time.perf_counter()
                    model(x, edge_index)
                    isolated_gnn_times.append((time.perf_counter() - t0) * 1000.0)

            isolated_exact_times: List[float] = []
            for _ in range(repeats):
                t0 = time.perf_counter()
                analyzer.analyze(nfa)
                isolated_exact_times.append((time.perf_counter() - t0) * 1000.0)

            median_e2e_gnn = statistics.median(e2e_gnn_times)
            median_e2e_exact = statistics.median(e2e_exact_times)
            median_iso_gnn = statistics.median(isolated_gnn_times)
            median_iso_exact = statistics.median(isolated_exact_times)

            results.append(
                {
                    "family": fam,
                    "k": k_val,
                    "pattern": pat,
                    "nfa_states": n_states,
                    "nfa_transitions": n_trans,
                    "end_to_end_gnn_median_ms": round(median_e2e_gnn, 3),
                    "end_to_end_exact_median_ms": round(median_e2e_exact, 3),
                    "isolated_gnn_forward_median_ms": round(median_iso_gnn, 3),
                    "isolated_exact_analyzer_median_ms": round(median_iso_exact, 3),
                    "e2e_speedup": round(median_e2e_exact / max(median_e2e_gnn, 0.001), 2),
                    "isolated_speedup": round(median_iso_exact / max(median_iso_gnn, 0.001), 2),
                }
            )
        except Exception as exc:
            continue

    summary = {
        "complexity_note": (
            "GNN forward pass message passing has time complexity O(|V| + |E|) per layer. "
            "Feature extraction requires graph traversal O(|V| + |E|). "
            "Exact ambiguity analysis builds the pair graph G2 with |V|^2 states and up to |E|^2 transitions, "
            "running Tarjan's SCC in O(|V|^2 + |E|^2). "
            "For small NFAs (|V| < 30), the exact analyzer is faster end-to-end than the GNN due to PyTorch tensor "
            "allocation and Python runtime overhead. The GNN is NOT O(1); claims of constant time are mathematically false."
        ),
        "results": results,
    }

    return summary


def load_trained_redos_gnn() -> ReDoSGNNClassifier:
    """Loads saved ReDoSGNNClassifier checkpoint, or trains and caches if missing."""
    model = ReDoSGNNClassifier(hidden_dim=32, num_classes=NUM_RISK_CLASSES)
    if os.path.exists(MODEL_PATH):
        try:
            model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
            model.eval()
            return model
        except Exception:
            pass

    # If checkpoint missing or corrupt, train and save
    train_redos_gnn(epochs=45, save_model=True)
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()
    return model

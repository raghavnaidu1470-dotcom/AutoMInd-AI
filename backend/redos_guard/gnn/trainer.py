"""
ReDoS Guard — GNN Training & Evaluation Pipeline
================================================
Trains the 3-class ReDoSGNNClassifier on NFA graph representations, evaluates
generalization on held-out test regexes and larger NFAs, benchmarks runtime speed
against the exact analyzer, and saves the trained model weights.
"""

import os
import time
import random
from typing import Dict, Any, List, Tuple
import torch
import torch.nn as nn
import torch.optim as optim

from backend.automata_engine.engine import AutomataEngine
from backend.redos_guard.analyzer import AmbiguityAnalyzer
from backend.redos_guard.gnn.model import ReDoSGNNClassifier
from backend.redos_guard.gnn.feature_extractor import extract_nfa_graph_features
from backend.redos_guard.gnn.dataset import build_redos_dataset
from backend.redos_guard.gnn.constants import (
    NUM_RISK_CLASSES,
    RISK_CLASS_NAMES,
    IDX_TO_RISK_CLASS,
)


MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/models"))
MODEL_PATH = os.path.join(MODEL_DIR, "redos_gnn.pt")


def prepare_graph_data(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts regex dataset into PyTorch geometric graph samples."""
    engine = AutomataEngine()
    graph_samples: List[Dict[str, Any]] = []

    for item in dataset:
        try:
            bundle = engine.build_all(item["regex"])
            nfa = bundle["nfa"]
            feat = extract_nfa_graph_features(nfa)
            graph_samples.append(
                {
                    "regex": item["regex"],
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
    epochs: int = 50,
    lr: float = 0.005,
    seed: int = 42,
    save_model: bool = True,
) -> Dict[str, Any]:
    """
    Trains and evaluates the 3-class ReDoS severity GNN classifier.

    Returns:
        Dict with train/test accuracy, per-class metrics, speed comparison,
        and evaluation on larger NFAs.
    """
    torch.manual_seed(seed)
    random.seed(seed)

    raw_data = build_redos_dataset(limit=220)
    samples = prepare_graph_data(raw_data)

    random.shuffle(samples)
    split_idx = int(0.8 * len(samples))
    train_samples = samples[:split_idx]
    test_samples = samples[split_idx:]

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
    per_class_total = {0: 0, 1: 0, 2: 0}
    per_class_correct = {0: 0, 1: 0, 2: 0}

    with torch.no_grad():
        for s in test_samples:
            logits = model(s["x"], s["edge_index"])
            pred = int(torch.argmax(logits, dim=-1).item())
            lbl = s["label"]
            per_class_total[lbl] += 1
            if pred == lbl:
                correct += 1
                per_class_correct[lbl] += 1

    test_accuracy = correct / max(len(test_samples), 1)

    # Evaluation on larger NFAs (generalization test)
    larger_regexes = [
        "((a|b)*c*)*d*",
        "(a|b|c|d|e)*foo(a|b|c)*",
        "(x|y|z)+(x|y|z)+w+",
        "((a+)+b+)+c+",
        "((0|1)+)+((0|1)+)+$",
    ]
    larger_eval = []
    analyzer = AmbiguityAnalyzer()
    engine = AutomataEngine()

    for r in larger_regexes:
        try:
            exact_res = analyzer.analyze(r)
            b = engine.build_all(r)
            feat = extract_nfa_graph_features(b["nfa"])
            pred_class, conf, _ = model.predict_risk(feat["x"], feat["edge_index"])
            larger_eval.append(
                {
                    "regex": r,
                    "nfa_states": len(b["nfa"].states),
                    "exact_class": exact_res.risk_class.value,
                    "gnn_predicted": pred_class,
                    "confidence": round(conf, 4),
                    "match": exact_res.risk_class.value == pred_class,
                }
            )
        except Exception as e:
            continue

    # Speed Benchmark: GNN screening latency vs Exact Analyzer as NFA size grows
    benchmark_patterns = [
        "(a|b)*abb",
        "(a+)+",
        "a*a*b",
        "(a|b|c|d|e)*foo*",
        "((a|b)*c*)*",
        "((a+)+b+)+c+",
    ]
    speed_comparison = []

    for pat in benchmark_patterns:
        try:
            b = engine.build_all(pat)
            feat = extract_nfa_graph_features(b["nfa"])

            # Measure exact analyzer
            t0 = time.perf_counter()
            for _ in range(10):
                analyzer.analyze(b["nfa"])
            exact_ms = ((time.perf_counter() - t0) / 10.0) * 1000.0

            # Measure GNN forward pass
            t0 = time.perf_counter()
            with torch.no_grad():
                for _ in range(10):
                    model(feat["x"], feat["edge_index"])
            gnn_ms = ((time.perf_counter() - t0) / 10.0) * 1000.0

            speed_comparison.append(
                {
                    "regex": pat,
                    "states": len(b["nfa"].states),
                    "exact_analyzer_ms": round(exact_ms, 3),
                    "gnn_ms": round(gnn_ms, 3),
                    "speedup": round(exact_ms / max(gnn_ms, 0.001), 1),
                }
            )
        except Exception:
            continue

    if save_model:
        os.makedirs(MODEL_DIR, exist_ok=True)
        torch.save(model.state_dict(), MODEL_PATH)

    return {
        "total_samples": len(samples),
        "train_samples": len(train_samples),
        "test_samples": len(test_samples),
        "test_accuracy": round(test_accuracy, 4),
        "per_class_accuracy": {
            IDX_TO_RISK_CLASS[k]: round(
                per_class_correct[k] / max(per_class_total[k], 1), 4
            )
            for k in per_class_total
        },
        "larger_nfa_eval": larger_eval,
        "speed_comparison": speed_comparison,
        "model_path": MODEL_PATH if save_model else None,
    }


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
    train_redos_gnn(epochs=35, save_model=True)
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()
    return model

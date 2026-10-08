"""
GNN Model Training Pipeline
===========================
Owned by: Member B (GNN + Explainable AI Module) & Member A (Real Automata Integration)

Trains the AutomataGNNClassifier on a combined dataset of synthetic automata
and REAL regular expression automata (NFAs, DFAs, and Minimized DFAs)
constructed by Member A's Automata Engine.
Evaluates both on a validation split and on held-out regular expressions not seen during training.
Saves model checkpoints to storage/models/.

Usage:
    python -m backend.xai_engine.train --epochs 40 --lr 0.005
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

# Ensure project root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.xai_engine.data.generator import SyntheticAutomataGenerator
from backend.xai_engine.graph_builder.converter import AutomataGraphConverter
from backend.xai_engine.gnn_model.model import AutomataGNNClassifier


def prepare_dataset(
    num_automata: int = 30,
    samples_per_automaton: int = 10,
    seed: int = 42,
) -> Tuple[List[Any], List[Any], List[Any]]:
    """
    Generates combined dataset (synthetic families + real regex NFAs/DFAs)
    and an unseen held-out regex dataset.
    Returns (train_data, val_data, held_out_data).
    """
    generator = SyntheticAutomataGenerator(seed=seed)

    # 1. Combined training & validation pool
    raw_combined = generator.generate_combined_dataset(
        num_synthetic_automata=num_automata,
        samples_per_automaton=samples_per_automaton,
    )

    # 2. Held-out test pool from unseen regex patterns
    raw_held_out = generator.generate_held_out_dataset(
        samples_per_automaton=samples_per_automaton,
    )

    converter = AutomataGraphConverter()

    def _process_samples(raw_list):
        processed = []
        for item in raw_list:
            automaton = item["automaton"]
            trace = item["simulation_trace"]
            label = 1 if item["accepted"] else 0

            graph_rep = converter.convert(automaton, trace, as_tensors=True)
            processed.append({
                "graph_rep": graph_rep,
                "label": label,
                "input_string": item["input_string"],
                "automaton_id": automaton.get("id", "auto"),
            })
        return processed

    all_combined = _process_samples(raw_combined)
    held_out_data = _process_samples(raw_held_out)

    # Shuffle and split 80% train, 20% val
    random.seed(seed)
    random.shuffle(all_combined)
    split_idx = int(len(all_combined) * 0.8)
    train_data = all_combined[:split_idx]
    val_data = all_combined[split_idx:]

    return train_data, val_data, held_out_data


def evaluate(model: nn.Module, dataset: List[Dict[str, Any]]) -> Tuple[float, float]:
    """
    Evaluates model on dataset and returns (loss, accuracy).
    """
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0.0
    correct = 0

    with torch.no_grad():
        for item in dataset:
            graph_rep = item["graph_rep"]
            target = torch.tensor([item["label"]], dtype=torch.long)
            logits = model(graph_rep.node_features, graph_rep.edge_index)
            loss = criterion(logits, target)
            total_loss += loss.item()

            pred = torch.argmax(logits, dim=1).item()
            if pred == item["label"]:
                correct += 1

    avg_loss = total_loss / max(len(dataset), 1)
    acc = correct / max(len(dataset), 1)
    return avg_loss, acc


def train(
    epochs: int = 40,
    lr: float = 0.005,
    num_automata: int = 30,
    samples_per_automaton: int = 10,
    checkpoint_dir: str = "storage/models",
    model_name: str = "automata_gnn.pt",
    seed: int = 42,
) -> str:
    """
    Main training routine for AutomataGNNClassifier with real regex integration.
    """
    torch.manual_seed(seed)
    random.seed(seed)

    print(f"[*] Preparing combined dataset (synthetic families + real regex NFAs/DFAs)...")
    train_data, val_data, held_out_data = prepare_dataset(
        num_automata=num_automata,
        samples_per_automaton=samples_per_automaton,
        seed=seed,
    )
    print(f"[+] Total samples: {len(train_data)} train, {len(val_data)} validation, {len(held_out_data)} held-out")

    # Initialize model
    model = AutomataGNNClassifier(
        node_in_dim=6,
        edge_in_dim=3,
        hidden_dim=32,
        num_classes=2,
        dropout=0.1,
    )

    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()

    best_val_acc = 0.0
    out_dir = Path(checkpoint_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    save_path = out_dir / model_name
    best_save_path = out_dir / "automata_gnn_best.pt"

    print(f"[*] Starting training for {epochs} epochs...")
    history = []

    for epoch in range(1, epochs + 1):
        model.train()
        total_train_loss = 0.0
        train_correct = 0

        # Shuffle training set each epoch
        random.shuffle(train_data)

        optimizer.zero_grad()
        for idx, item in enumerate(train_data):
            graph_rep = item["graph_rep"]
            target = torch.tensor([item["label"]], dtype=torch.long)

            logits = model(graph_rep.node_features, graph_rep.edge_index)
            loss = criterion(logits, target)
            loss.backward()

            total_train_loss += loss.item()
            pred = torch.argmax(logits, dim=1).item()
            if pred == item["label"]:
                train_correct += 1

            # Step optimizer every 8 samples (mini-batch accumulation) or at end
            if (idx + 1) % 8 == 0 or (idx + 1) == len(train_data):
                optimizer.step()
                optimizer.zero_grad()

        train_loss = total_train_loss / len(train_data)
        train_acc = train_correct / len(train_data)

        # Validation evaluation
        val_loss, val_acc = evaluate(model, val_data)

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 4),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc, 4),
        })

        if epoch % 5 == 0 or epoch == epochs or val_acc > best_val_acc:
            print(
                f"  Epoch [{epoch:02d}/{epochs:02d}] "
                f"Loss: {train_loss:.4f} | Acc: {train_acc*100:.1f}% || "
                f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc*100:.1f}%"
            )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), str(best_save_path))

    # Save final model checkpoint
    torch.save(model.state_dict(), str(save_path))

    # Evaluate best model on held-out unseen regex dataset
    model.load_state_dict(torch.load(str(best_save_path)))
    held_out_loss, held_out_acc = evaluate(model, held_out_data)

    print(f"[+] Final model checkpoint saved to: {save_path}")
    print(f"[+] Best validation accuracy checkpoint: {best_save_path} ({best_val_acc*100:.1f}%)")
    print(f"[+] Held-out Unseen Regex Test Accuracy: {held_out_acc*100:.1f}% (Loss: {held_out_loss:.4f})")

    # Save training metadata
    meta_path = out_dir / "training_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "epochs": epochs,
                "learning_rate": lr,
                "num_train_samples": len(train_data),
                "num_val_samples": len(val_data),
                "num_held_out_samples": len(held_out_data),
                "final_train_acc": train_acc,
                "final_val_acc": val_acc,
                "best_val_acc": best_val_acc,
                "held_out_acc": held_out_acc,
                "history": history,
            },
            f,
            indent=2,
        )

    return str(save_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train AutomataGNNClassifier on real + synthetic automata.")
    parser.add_argument("--epochs", type=int, default=40, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=0.005, help="Learning rate")
    parser.add_argument("--num-automata", type=int, default=30, help="Number of distinct synthetic automata")
    parser.add_argument("--samples-per-automaton", type=int, default=10, help="Samples per automaton")
    parser.add_argument("--checkpoint-dir", type=str, default="storage/models", help="Checkpoint output directory")
    parser.add_argument("--model-name", type=str, default="automata_gnn.pt", help="Saved checkpoint filename")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    train(
        epochs=args.epochs,
        lr=args.lr,
        num_automata=args.num_automata,
        samples_per_automaton=args.samples_per_automaton,
        checkpoint_dir=args.checkpoint_dir,
        model_name=args.model_name,
        seed=args.seed,
    )

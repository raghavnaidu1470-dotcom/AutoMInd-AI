"""
Storage Service
===============
Owned by: Member C (API, Visualization & Integration)

Handles persistence, retrieval of sample automata, model weights, and query runs.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..config import SAMPLES_DIR, HISTORY_DIR, MODELS_DIR


class StorageService:
    """Service for filesystem-based persistence of automata and history."""

    def __init__(self):
        SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

    def list_samples(self) -> List[str]:
        """Returns filenames of all available sample automata."""
        return [f.name for f in SAMPLES_DIR.glob("*.json")]

    def load_sample(self, filename: str) -> Optional[Dict[str, Any]]:
        """Loads a sample automaton by filename."""
        filepath = SAMPLES_DIR / filename
        if not filepath.exists():
            # Check with .json appended
            filepath = SAMPLES_DIR / f"{filename}.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def save_run(self, run_id: str, payload: Dict[str, Any]) -> str:
        """Saves a simulation / explanation run record."""
        target_path = HISTORY_DIR / f"{run_id}.json"
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return str(target_path)

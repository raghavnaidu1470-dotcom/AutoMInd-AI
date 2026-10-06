# AutoMind AI — Storage Layer

This directory stores persistent assets and runtime history for the system, managed primarily by **Member C**.

## Subdirectories

- **`samples/`**: Canonical automaton JSON files used for development, unit testing, and benchmarking.
- **`models/`**: Checkpoints and serialized weights for trained Graph Neural Network (GNN) models.
- **`history/`**: Cached simulation runs, parsed automata outputs, and explanation results.

## File Retention & Git Policy
- Sample automata in `samples/` are committed to version control.
- Large binary model weights (`*.pt`, `*.pth`) and dynamic history files in `history/` are ignored via `.gitignore`.

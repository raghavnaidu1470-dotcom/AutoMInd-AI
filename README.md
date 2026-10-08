# AutoMind AI

> **Explainable Formal Language Recognition and Automata Analysis System**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React: 18](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5+-646CFF.svg)](https://vitejs.dev/)

---

## 🌟 Project Overview

**AutoMind AI** is an AI-powered system that simplifies the analysis, conversion, and visualization of Formal Languages and Finite Automata. It bridges theoretical computer science with state-of-the-art Explainable Artificial Intelligence (XAI).

The platform transforms user-defined Regular Expressions into Non-Deterministic Finite Automata (NFA) via **Thompson's Construction**, converts them to Deterministic Finite Automata (DFA) via **Subset Construction**, optimizes states via **Hopcroft's DFA Minimization**, and validates candidate input strings with full state-by-state execution trace logging.

Leveraging **Graph Neural Networks (GNNs)** and XAI techniques—specifically **GNNExplainer** and **SHAP**—AutoMind AI identifies the critical states, transitions, and structural features responsible for accepting or rejecting a given string.

All generated automata are rendered through an interactive, visual state-transition interface featuring step-by-step playback and explainability heatmap overlays.

---

## 🚀 Core Functionality

1. **Pure-Python Automata Theory Engine (No Mocks):**
   - **Regex Parser:** Lexical tokenizer + recursive-descent parser producing clean ASTs with strict `RegexSyntaxError` handling.
   - **Thompson's Construction:** Converts ASTs into NFAs with deterministic state naming (`q0`, `q1`, ...) and single start/accept invariants.
   - **Subset Construction:** Transforms NFAs into equivalent DFAs over the full alphabet with optional explicit dead/trap states.
   - **Hopcroft's Minimization:** Prunes unreachable states and refines partitions to yield the minimal canonical DFA.
   - **Simulation Engine:** Step-by-step execution traces for both NFAs (epsilon-closure tracking) and DFAs.
2. **Explainable AI (GNN + GNNExplainer + SHAP):**
   - **Graph Representation:** Automata graphs encoded into tensor feature matrices with 6 unified node features and 3 edge features.
   - **GNN Classifier:** Graph Convolutional Network predicting string acceptance directly from graph topology and execution traces.
   - **GNNExplainer:** Extracts critical subgraphs and transition masks explaining the decision path.
   - **SHAP Attributions:** Game-theoretic feature attributions quantifying topological and simulation influence.
3. **Interactive Visual Dashboard:**
   - Real-time diagrams with tabs for **NFA**, **DFA**, and **Minimized DFA**.
   - Step-by-step string playback and active transition animation.
   - XAI importance heatmap overlays with color-coded critical transitions.
   - Inline syntax error highlighting for malformed regular expressions.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│  Layer 1: Frontend / UI Layer (React, SVG/Canvas)      │
│  - Regex & string inputs, diagram viewer, trace runner │
└───────────────────────────▲────────────────────────────┘
                            │ REST / JSON
┌───────────────────────────▼────────────────────────────┐
│  Layer 2: Backend API / Orchestrator (FastAPI)         │
│  - Routes requests, coordinates engines, aggregates XAI│
└─────────────▲────────────────────────────▲─────────────┘
              │                            │
┌─────────────▼────────────┐ ┌─────────────▼────────────┐
│ Layer 3: Automata Engine │ │ Layer 4: XAI Engine       │
│ - Pure Python Parser     │ │ - Graph Builder (PyG)     │
│ - Thompson NFA Builder   │ │ - GNN Classifier          │
│ - Subset DFA Converter   │ │ - GNNExplainer Subgraphs  │
│ - Hopcroft Minimizer     │ │ - SHAP Attributions       │
│ - Simulation Trace Logger│ │                           │
└─────────────▲────────────┘ └─────────────▲────────────┘
              │                            │
┌─────────────▼────────────────────────────▼─────────────┐
│  Layer 5: Storage Layer                                │
│  - Sample automata, trained model checkpoints, history │
└────────────────────────────────────────────────────────┘
```

For complete technical specifications, see [`docs/architecture.md`](docs/architecture.md) and [`docs/automata_engine.md`](docs/automata_engine.md).

---

## 💡 Example Regexes to Try

Try these patterns in the dashboard or via the API:

| Regular Expression | Description | Example Accepted | Example Rejected |
| :--- | :--- | :--- | :--- |
| `(a\|b)*abb` | Strings ending with `abb` | `ababb`, `abb`, `babb` | `abab`, `bba`, `a` |
| `a*b+` | Zero or more `a` followed by $\ge 1$ `b` | `b`, `ab`, `aaabbb` | `a`, `ba`, `""` |
| `(ab)+` | Alternating non-empty pairs of `ab` | `ab`, `abab`, `ababab` | `a`, `aba`, `b` |
| `a(b\|c)*d` | Starts with `a`, ends with `d`, internal `b` or `c` | `ad`, `abd`, `abccbd` | `abc`, `d`, `abdq` |
| `(01)*101` | Binary sequence ending in `101` | `101`, `01101`, `0101101` | `0101`, `111`, `0` |
| `(a\|b)*a(a\|b)` | Second-to-last symbol is `a` | `bab`, `aa`, `ba` | `b`, `bb`, `baba` |

---

## ⚡ Getting Started

### Prerequisites
- **Python:** 3.9+ installed
- **Node.js:** v18+ and `npm` installed

### 1. Clone the Repository
```bash
git clone https://github.com/raghavnaidu1470-dotcom/AutoMInd-AI.git
cd AutoMInd-AI
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv backend/venv
source backend/venv/bin/activate       # On Windows: backend\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server
python -m uvicorn backend.api.main:app --reload --port 8000
```
Interactive Swagger documentation will be available at:
👉 **`http://localhost:8000/docs`**

### 3. Frontend Setup
```bash
# In a new terminal window:
cd frontend

# Install dependencies and start development server
npm install
npm run dev
```
The web dashboard will be available at:
👉 **`http://localhost:5173`**

### 4. Running Model Retraining
To retrain the GNN on real automata generated by the engine mixed with synthetic language families:
```bash
source backend/venv/bin/activate
python -m backend.xai_engine.train --epochs 40 --lr 0.005
```
*Current retrained model validation accuracy: **100.0%**; held-out unseen regex accuracy: **99.3%**.*

### 5. Running Tests
```bash
# Run backend unit, API, and correctness tests (89 passing tests)
backend/venv/bin/pytest tests/

# Verify frontend production build
npm --prefix frontend run build
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

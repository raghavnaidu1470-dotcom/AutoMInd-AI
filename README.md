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

## 🛡️ ReDoS Guard: Explainable Ambiguity Screening & Verified Repair

AutoMind-AI now includes **ReDoS Guard**, an end-to-end module for diagnosing and repairing Regular Expression Denial of Service vulnerabilities:

1. **Exact Ambiguity Analysis:** Implements Weber & Seidl (1991) product-automaton criteria over trimmed $\epsilon$-free NFAs: lazy Pair Graph ($G_2$) reachability for Exponential Ambiguity (EDA), and exact Triple-Product Condition ($G_3$) state transfer for Polynomial Ambiguity (PDA).
2. **Empirical Sandboxed Validation:** Executes compiled Python regex matching in isolated subprocesses with hard timeouts across increasing pump lengths. Synthesizes attack strings ($prefix + pump^k + suffix$) with DFA-computed failing suffixes forcing maximal backtracking under both `fullmatch` and `search` semantics (**92.19%** empirical agreement, 19/22 exponential confirmed, 18/20 polynomial confirmed, 22/22 linear confirmed safe).
3. **3-Class Severity GNN Screening:** Neural risk screening (Linear, Polynomial, Exponential) via graph message-passing on NFA graphs. Evaluated on **3,200** grammar-generated regexes across 20+ structural families strictly partitioned with zero template overlap (**85.43%** test accuracy, 95% CI [83.45%, 87.41%]). Safe linear false positives (14.4%) are honestly documented, positioning the GNN as an experimental explanation and screening aid.
4. **Fair Timing Study:** Documents empirical crossover at $|V| \approx 18$ states: on small typical regexes, the optimized Exact Analyzer is faster end-to-end (0.34 ms vs. 0.36 ms), while the GNN scales $\mathcal{O}(|V| + |E|)$ on large graphs.
5. **GNNExplainer Source Provenance Localization:** Maps critical edge and node attributions back to exact regex character spans via AST metadata provenance.
6. **Language-Preserving Repair:** Rule-based algebraic rewrites mathematically verified for 100% language equivalence using Hopcroft Minimized DFA isomorphism.

### Demo Vulnerable vs. Safe Regexes

| Regular Expression | Risk Class | Status | Offending Span | Attack String Template | Verified Repaired Regex |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `(a+)+$` | **Exponential (EDA)** | Confirmed by Measurement (`fullmatch`) | `0-6: (a+)+$` | `(a)^k + !` | `a+$` (Verified Equivalent) |
| `(a\|aa)+$` | **Exponential (EDA)** | Confirmed by Measurement (`fullmatch`) | `0-8: (a\|aa)+$` | `(a)^k + !` | `a+$` (Verified Equivalent) |
| `(a*)*b` | **Exponential (EDA)** | Confirmed by Measurement (`fullmatch`) | `0-6: (a*)*b` | `(a)^k + !` | `a*b` (Verified Equivalent) |
| `a*a*b` | **Polynomial (PDA)** | Confirmed by Measurement (`search`) | `0-5: a*a*b` | `(a)^k + !` | `a*b` (Verified Equivalent) |
| `(a\|b)*abb` | **Linear (Safe)** | Confirmed Safe | None | None | None (Already Safe) |

### Quick Demo Commands

```bash
# Analyze ReDoS ambiguity via API
curl -X POST http://localhost:8000/api/redos/analyze \
  -H "Content-Type: application/json" \
  -d '{"regex": "(a+)+$", "run_empirical": true}'

# Suggest and verify language-equivalent repair
curl -X POST http://localhost:8000/api/redos/repair \
  -H "Content-Type: application/json" \
  -d '{"regex": "(a+)+$", "benchmark_before_after": true}'
```

*For comprehensive evaluation metrics, detection tables, and theoretical proofs, see [`docs/redos_guard.md`](docs/redos_guard.md) and [`docs/design_rationale.md`](docs/design_rationale.md).*

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

# Install dependencies (or use backend/requirements-pinned.txt for exact versions)
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

### 4. Running Model Retraining & Evaluation Suites
```bash
source backend/venv/bin/activate

# 1. Run full 64-regex ReDoS independent evaluation suite
python -c "from backend.redos_guard.evaluation import run_comprehensive_evaluation; run_comprehensive_evaluation('docs/evaluation_results.json')"

# 2. Retrain GNN on family-stratified splits & run fair timing benchmark
python -c "from backend.redos_guard.gnn.trainer import train_redos_gnn, run_fair_timing_benchmark; train_redos_gnn(); run_fair_timing_benchmark()"
```

### 5. Running Tests
```bash
# Run backend unit, API, and correctness tests (152 passing tests)
backend/venv/bin/pytest tests/

# Verify frontend production build
npm --prefix frontend run build
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

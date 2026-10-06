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

The platform automatically transforms user-defined Regular Expressions into Non-Deterministic Finite Automata (NFA) and Deterministic Finite Automata (DFA), optimizes states via DFA minimization, and validates candidate input strings with full state-by-state execution trace logging. Leveraging **Graph Neural Networks (GNNs)** and XAI techniques—specifically **GNNExplainer** and **SHAP**—AutoMind AI identifies the critical states, transitions, and structural features responsible for accepting or rejecting a given string.

All generated automata are rendered through an interactive, visual state-transition interface featuring step-by-step playback and explainability heatmap overlays.

### 🎯 Primary Goal
Improve the understanding, education, and analysis of finite automata by enabling intelligent language recognition, mathematically rigorous automata construction, and explainable decision execution through AI-driven graph analytics.

---

## 🚀 Core Functionality

1. **Regex Parsing → AST:** Lexical analysis and AST generation for standard regular expression operations (concatenation, alternation, Kleene star, grouped subexpressions).
2. **Thompson's Construction (Regex AST → NFA):** Algorithmic translation of AST syntax nodes into an equivalent NFA with epsilon transitions.
3. **Subset Construction (NFA → DFA):** Power-set construction converting non-deterministic transition graphs into deterministic state machines.
4. **DFA Minimization:** Equivalence-partition reduction using Hopcroft's / Myhill-Nerode algorithms to generate the minimal canonical DFA.
5. **String Simulation & Trace Logging:** Validates candidate strings against the automaton, generating an execution trace of current states, consumed symbols, and transitions taken.
6. **Graph Representation Transformation:** Converts automata into formal graph representations where states form nodes with attributes and transitions form directed edges with symbol encodings.
7. **GNN Acceptance Classifier:** Graph Neural Network (GCN/GAT) trained to classify language acceptance from the automaton graph topology and traversal paths.
8. **GNNExplainer Integration:** Extracts influential subgraphs and identifies key transition paths behind acceptance or rejection decisions.
9. **SHAP Feature Attribution:** Calculates feature-level attributions across state and structural properties (e.g. accepting status, traversal density, in-degree).
10. **Interactive Visual Dashboard:** A React frontend offering regex and string inputs, NFA/DFA/minimized-DFA diagrams, step-by-step trace stepper, and visual importance highlighting.

---

## 🏗️ Architecture

AutoMind AI is designed around a clean 6-layer architecture:

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
│ (Member A)               │ │ (Member B)                │
│ - Regex Parser & AST     │ │ - Graph Builder (PyG)     │
│ - Thompson NFA Builder   │ │ - GNN Classifier          │
│ - Subset DFA Converter   │ │ - GNNExplainer Subgraphs  │
│ - DFA Minimizer          │ │ - SHAP Attributions       │
│ - Simulation Trace Logger│ │                           │
└─────────────▲────────────┘ └─────────────▲────────────┘
              │                            │
┌─────────────▼────────────────────────────▼─────────────┐
│  Layer 5: Storage Layer (Member C)                     │
│  - Sample automata, trained model checkpoints, history │
└────────────────────────────────────────────────────────┘
                            ▲
┌───────────────────────────┴────────────────────────────┐
│  Layer 6: Visualization Output Loop                    │
│  - Formats XAI node/edge importance for UI heatmap     │
└────────────────────────────────────────────────────────┘
```

For complete technical specifications, see [`docs/architecture.md`](docs/architecture.md).

---

## 👥 Team Structure & Roles (3 Members)

| Member | Domain | Module & Directory | Scope |
| :--- | :--- | :--- | :--- |
| **Member A** | Automata Theory Engine | `backend/automata_engine/` | Regex parser, Thompson's NFA construction, subset DFA conversion, Hopcroft DFA minimization, step-by-step string simulation engine, and shared JSON schema generation. |
| **Member B** | GNN & Explainable AI | `backend/xai_engine/` | Graph builder (converts automata JSON to GNN graphs), GNN model architecture & training for string acceptance, GNNExplainer subgraph extraction, SHAP feature attributions, explanation payload generation. |
| **Member C** | API, Integration & UI | `backend/api/`, `frontend/`, `storage/` | FastAPI orchestration endpoints, interactive React frontend, state-transition diagram viewer, step-by-step animation controls, XAI heatmap highlights, storage management, and integration tests. |

---

## 📂 Repository Structure

```
AutoMind-AI/
├── README.md                      # Full project overview, architecture, and setup
├── LICENSE                        # MIT License
├── .gitignore                     # Python, PyTorch, Node.js, and OS ignores
├── CONTRIBUTING.md                # Role split, branching model, and PR guidelines
├── backend/
│   ├── automata_engine/           # [Member A] Automata theory logic & placeholders
│   │   ├── regex_parser/          # Regex string to AST parser
│   │   ├── nfa_builder/           # Thompson's construction (AST -> NFA)
│   │   ├── dfa_converter/         # Subset construction (NFA -> DFA)
│   │   ├── dfa_minimizer/         # Hopcroft's / Myhill-Nerode minimization
│   │   ├── simulator/             # Execution engine with state-by-state trace logging
│   │   ├── models.py              # Pydantic data models for automata contracts
│   │   └── __init__.py
│   ├── xai_engine/                # [Member B] Graph AI and Explainability module
│   │   ├── graph_builder/         # Automaton JSON -> PyG graph structure converter
│   │   ├── gnn_model/             # GNN classifier (acceptance prediction)
│   │   ├── gnn_explainer/         # GNNExplainer implementation (edge/subgraph masks)
│   │   ├── shap_explainer/        # SHAP feature attribution module
│   │   ├── pipeline.py            # Unified XAI execution pipeline
│   │   └── __init__.py
│   └── api/                       # [Member C] Backend API and orchestration
│       ├── routes/                # FastAPI endpoint routers (automata, xai, simulation)
│       ├── services/              # Orchestration services and mock fallbacks
│       ├── config.py              # Application settings
│       ├── main.py                # FastAPI app entrypoint
│       └── requirements.txt       # Python dependencies
├── frontend/                      # [Member C] Modern interactive React interface
│   ├── public/                    # Static assets
│   ├── src/
│   │   ├── components/            # State diagram visualizer, trace stepper, XAI heatmap
│   │   ├── pages/                 # Main Dashboard view
│   │   ├── services/              # API client communicating with backend
│   │   ├── mock/                  # Standalone mock data for offline preview
│   │   ├── App.jsx                # Application root component
│   │   ├── index.css              # Glassmorphic dark theme design system
│   │   └── main.jsx               # React entrypoint
│   ├── package.json               # Node dependencies & scripts
│   └── vite.config.js             # Vite configuration
├── storage/                       # [Member C] Persistent storage & cached assets
│   ├── samples/                   # Canonical reference automata JSON files
│   ├── models/                    # Trained GNN model weights (.pt/.pth)
│   ├── history/                   # Cached queries and simulation runs
│   └── README.md
├── docs/
│   ├── architecture.md            # Detailed architecture and flow diagrams
│   └── json_schema.md             # Shared JSON schema contract (Automaton, Trace, XAI)
└── tests/
    ├── automata_engine/           # Unit tests for automata theory modules
    ├── xai_engine/                # Unit tests for graph builder, GNN, and explainers
    ├── api/                       # API integration tests using FastAPI TestClient
    └── fixtures/                  # Mock automaton, simulation trace, and XAI fixtures
```

---

## 📜 Shared JSON Schema Contract

To enable decoupled development between Member A, Member B, and Member C, all components conform to the shared schemas defined in [`docs/json_schema.md`](docs/json_schema.md):

- **Automaton Object:** States with IDs and start/accept flags, alphabet list, and directed transition tuples.
- **Simulation Trace:** Ordered execution steps recording current active states, consumed characters, and next states.
- **XAI Explanation:** Subgraph edge masks, node importance scores, SHAP attributions, and human-readable explanation summaries.

Reference fixtures are available in [`tests/fixtures/`](tests/fixtures/).

---

## ⚡ Getting Started

### Prerequisites
- **Python:** 3.9+ installed
- **Node.js:** v18+ and `npm` installed

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/your-username/AutoMind-AI.git
cd AutoMind-AI/backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r api/requirements.txt

# Start the FastAPI server
uvicorn api.main:app --reload --port 8000
```
The API documentation (Interactive Swagger UI) will be available at:
👉 **`http://localhost:8000/docs`**

### 2. Frontend Setup
```bash
# In a new terminal window:
cd AutoMind-AI/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
The web dashboard will be available at:
👉 **`http://localhost:5173`**

### 3. Running Tests
```bash
cd AutoMind-AI
pytest tests/
```

---

## 🤝 Branching & Collaboration Guidelines

We follow the branching conventions outlined in [`CONTRIBUTING.md`](CONTRIBUTING.md):
- `feat/member-a/*` for Automata Engine development
- `feat/member-b/*` for GNN & XAI Engine development
- `feat/member-c/*` for API, Storage & Frontend development

All pull requests require testing, schema validation against `docs/json_schema.md`, and code review before merging into `develop`.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

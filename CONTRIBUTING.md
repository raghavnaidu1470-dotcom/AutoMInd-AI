# Contributing to AutoMind AI

Welcome to the **AutoMind AI** project repository! This guide outlines our team responsibilities, Git branching strategy, coding standards, and pull request workflow.

---

## 1. Team Role Allocation (3-Member Split)

| Team Member | Module Focus | Primary Directory Ownership | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| **Member A** | Automata Theory Engine | `backend/automata_engine/` | • Regex lexing & AST parsing<br/>• Thompson's NFA construction<br/>• Subset DFA construction<br/>• Hopcroft / Myhill-Nerode minimization<br/>• State-by-state execution simulator & trace generator<br/>• Adherence to `docs/json_schema.md` |
| **Member B** | GNN & Explainable AI | `backend/xai_engine/` | • Graph feature builder (converts automaton + trace to PyG graph)<br/>• GNN classifier design & training (acceptance prediction)<br/>• GNNExplainer integration (subgraph/edge importance extraction)<br/>• SHAP feature attribution integration<br/>• Packaging normalized scores for frontend display |
| **Member C** | API, Integration & UI | `backend/api/`, `frontend/`, `storage/` | • FastAPI orchestrator & REST endpoints<br/>• React frontend & interactive SVG/Canvas state diagrams<br/>• Step-by-step trace animation controls<br/>• Explainability heatmap overlay rendering<br/>• Storage caching, integration testing, CI/CD pipeline |

---

## 2. Git Branching Convention

We follow a structured Git flow:

- **`main`**: Production-ready, stable code. Direct commits are restricted.
- **`develop`**: Primary integration branch where verified features are merged.
- **Feature Branches**:
  - `feat/member-a/<feature-name>` — Work on automata parser, NFA/DFA, minimization, simulation.
  - `feat/member-b/<feature-name>` — Work on GNN architecture, PyG graphs, GNNExplainer, SHAP.
  - `feat/member-c/<feature-name>` — Work on FastAPI routes, React components, visualizer.
  - `fix/<issue-name>` — Bug fixes across any module.

### Example:
```bash
git checkout develop
git pull origin develop
git checkout -b feat/member-b/gnn-explainer-pipeline
```

---

## 3. Commit Message Standards

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat(automata): implement Hopcroft DFA minimization algorithm`
- `feat(xai): add PyG edge mask extraction in GNNExplainer`
- `feat(api): expose /api/xai/explain endpoint with validation`
- `fix(frontend): resolve active node glow on step backwards`
- `test(xai): add unit test for graph feature builder`
- `docs(schema): document epsilon transition representation in JSON`

---

## 4. Contract-First Development (JSON Schema)

Before modifying the data exchange shape between modules:
1. Review [`docs/json_schema.md`](docs/json_schema.md).
2. Ensure any change is backwards-compatible or discussed with other team members.
3. Validate payloads against Pydantic models in `backend/automata_engine/models.py`.

---

## 5. Local Setup & Testing

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r api/requirements.txt
pytest ../tests/
```

### Running the API Server
```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

### Running the Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 6. Pull Request Checklist

Before submitting a PR to `develop`:
- [ ] Code passes formatting and lint checks.
- [ ] Relevant unit tests in `tests/` pass.
- [ ] Output complies with the schema in `docs/json_schema.md`.
- [ ] All public classes and functions have docstrings explaining parameters and return types.
- [ ] PR description specifies which member role and ticket/issue it fulfills.
- [ ] At least one other team member has reviewed and approved the PR.

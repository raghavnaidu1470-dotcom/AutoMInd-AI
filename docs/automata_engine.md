# AutoMind AI — Automata Engine Technical Specification

**Author / Maintainer:** Member A (Automata Theory Engine)  
**Consuming Systems:** API & Live Dashboard (Member C), Graph Neural Network & Explainable AI Engine (Member B)

---

## 1. Overview & System Role

The **Automata Engine** (`backend/automata_engine/`) is the formal theoretical core of AutoMind AI. It implements a complete, pure-Python pipeline transforming regular expressions into deterministic and non-deterministic finite state automata without external automata libraries.

```
                  ┌──────────────────────┐
                  │ Regular Expression   │
                  └──────────┬───────────┘
                             │  RegexParser (Recursive Descent)
                             ▼
                  ┌──────────────────────┐
                  │         AST          │
                  └──────────┬───────────┘
                             │  NFABuilder (Thompson's Construction)
                             ▼
                  ┌──────────────────────┐
                  │         NFA          │
                  └──────────┬───────────┘
                             │  DFAConverter (Subset Construction)
                             ▼
                  ┌──────────────────────┐
                  │         DFA          │
                  └──────────┬───────────┘
                             │  DFAMinimizer (Hopcroft's Algorithm)
                             ▼
                  ┌──────────────────────┐
                  │    Minimized DFA     │
                  └──────────────────────┘
```

Both the intermediate and minimized automata adhere strictly to the shared JSON Schema specified in `docs/json_schema.md`.

---

## 2. Algorithms & Subsystem Design

### 2.1 Regex Parser (`backend/automata_engine/regex_parser/`)

- **Grammar & Precedence (Lowest to Highest):**
  1. Alternation / Union (`|`): `a|b`
  2. Concatenation (Implicit): `ab` $\rightarrow$ `a . b`
  3. Unary Postfix Repetition (`*` Kleene Star, `+` Positive Closure, `?` Optional)
  4. Primary Atoms: Literals, Escaped Characters (`\*`, `\\`), Epsilon (`ε` or `()`), Grouped Expressions `(...)`

- **Error Handling (`RegexSyntaxError`):**
  Implements strict syntax validation with 0-indexed character positions and explicit error messages:
  - Unbalanced parentheses (e.g. `(a|b`)
  - Dangling operators without targets (e.g. `*a`, `+b`)
  - Multiple stacked repeat operators (e.g. `a++`, `a**`)
  - Empty alternation branches (e.g. `|a`, `a|`, `a||b`, `(|)`)
  - Trailing escape backslashes (e.g. `\`)

### 2.2 NFA Builder — Thompson's Construction (`backend/automata_engine/nfa_builder/`)

- **Fragment Invariants:**
  Every sub-automaton fragment has **exactly one initial state** and **exactly one accepting state**.
- **State Naming:**
  States are generated deterministically as `q0, q1, q2, ...`. By construction, `q0` is guaranteed to be the overall start state of the resulting NFA.
- **Constructions:**
  - *Literal / Epsilon:* Fresh `start` and `accept` connected via transition on symbol or `"ε"`.
  - *Concatenation (`left . right`):* Fragment 1 accept state connects to Fragment 2 start state via `"ε"`. Overall start is `f1.start`, overall accept is `f2.accept`.
  - *Alternation (`left | right`):* New `start` branches to `f1.start` and `f2.start` on `"ε"`; `f1.accept` and `f2.accept` branch to new `accept` on `"ε"`.
  - *Kleene Star (`child*`):* New `start` branches to `child.start` and new `accept` (empty bypass) on `"ε"`; `child.accept` loops back to `child.start` and to new `accept` on `"ε"`.
  - *Plus (`child+`):* Similar to star, but omitting the start-to-accept bypass.
  - *Question (`child?`):* New `start` branches to `child.start` and new `accept` on `"ε"`; `child.accept` connects to new `accept` on `"ε"`.

### 2.3 DFA Converter — Subset Construction (`backend/automata_engine/dfa_converter/`)

- **Epsilon Closure:**
  Computes the reflexive-transitive closure of reachable NFA states over `"ε"` transitions using iterative depth-first traversal.
- **Subset Construction (Powerset):**
  - Start DFA state $S_0 = \text{epsilon\_closure}(\{nfa.start\_state\})$, mapped to `"q0"`.
  - For each active subset $S$ and alphabet symbol $a \in \Sigma$:
    $$S' = \text{epsilon\_closure}(\text{move}(S, a))$$
  - Subsets are visited in breadth-first search (BFS) order over sorted alphabet symbols, ensuring strict output stability across runs.
- **Explicit Dead/Trap State Policy:**
  Formal DFA definitions require a total transition function $\delta: Q \times \Sigma \to Q$. If any state lacks an outgoing transition for an alphabet symbol $a$, an explicit non-accepting dead state (e.g. `q_trap` or highest-index `qN`) is generated with self-loops on all symbols. If the transition graph is already complete (e.g. `(a|b)*abb`), no dead state is added.
- **Metadata:**
  Each DFA state includes `metadata.nfa_subset` recording the constituent NFA state IDs.

### 2.4 DFA Minimizer — Hopcroft's Algorithm (`backend/automata_engine/dfa_minimizer/`)

- **Step 1: Reachability Pruning:**
  Traverses the DFA via BFS starting from `dfa.start_state`. Any state unreachable from the start state is pruned before partitioning.
- **Step 2: Hopcroft's Partition Refinement:**
  - Initial partition $P = \{ F, Q \setminus F \}$ (accepting vs non-accepting states).
  - Worklist $W$ initialized with $\min(F, Q \setminus F)$.
  - In each iteration, extracts block $A \in W$, computes pre-images $X = \delta^{-1}(A, c)$ for each symbol $c \in \Sigma$, and splits blocks $Y \in P$ into $Y_1 = Y \cap X$ and $Y_2 = Y \setminus X$.
- **Step 3: Canonical State Synthesis:**
  - The block containing `dfa.start_state` is synthesized as minimal state `"q0"`.
  - Remaining blocks are ordered according to BFS traversal from `"q0"`, producing strictly deterministic identifiers `q0, q1, ...`.
  - Idempotent: minimizing an already minimal DFA produces an isomorphic automaton with identical state IDs and transitions.

### 2.5 Simulator (`backend/automata_engine/simulator/`)

- **DFA Simulation:**
  Follows unique transition $(q_{current}, \text{char}) \to q_{next}$. Halts immediately with rejected status if an undefined transition or out-of-alphabet symbol is read.
- **NFA Simulation:**
  Tracks the active set of concurrent states, starting with $\text{epsilon\_closure}(\{start\_state\})$. For each character, transitions to the union of target states followed by their epsilon closure.
- **Trace Output:**
  Produces structured `SimulationResult` containing step 0 (initial configuration) and sequential `SimulationStep` records with `current_states`, `symbol_read`, `transition_taken`, and `next_states`.

---

## 3. State Naming & Determinism Conventions

| Automaton Type | Start State | State IDs | Transition Sorting Order |
|---|---|---|---|
| **NFA** | `q0` | `q0`, `q1`, ..., `q_{N-1}` | `(from_state_idx, symbol, to_state_idx)` |
| **DFA** | `q0` | `q0`, `q1`, ..., `q_{N-1}` | `(from_state_idx, symbol, to_state_idx)` |
| **MINIMIZED_DFA** | `q0` | `q0`, `q1`, ..., `q_{M-1}` | `(from_state_idx, symbol, to_state_idx)` |

---

## 4. Facade API

```python
from backend.automata_engine.engine import build_all

bundle = build_all("(a|b)*abb")
# Returns:
# {
#     "nfa": Automaton,
#     "dfa": Automaton,
#     "minimized_dfa": Automaton,
#     "alphabet": ["a", "b"]
# }
```

Safety limits enforced at service level:
- `MAX_REGEX_LENGTH`: 300 characters
- `MAX_DFA_STATES`: 1,000 states
- `MAX_INPUT_STRING_LENGTH`: 5,000 characters

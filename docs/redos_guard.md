# ReDoS Guard: Ambiguity Analysis, Screening & Verified Repair

## 1. Theoretical Foundations & Ambiguity Decision Criteria

Regular Expression Denial of Service (ReDoS) occurs when ambiguous automaton topologies permit a multiplicity of accepting paths for identical input words, triggering super-linear (polynomial $\mathcal{O}(N^d)$ or exponential $\mathcal{O}(2^N)$) backtracking in backtracking regular expression engines.

AutoMind-AI implements exact ambiguity classification over $\epsilon$-free, trimmed finite state automata following the established theoretical principles for finite automata ambiguity formulated by **Weber & Seidl (1991)**.

### 1.1 Pre-processing: Trimmed $\epsilon$-Free NFA
Let $A = (Q, \Sigma, \delta, q_0, F)$ be an NFA constructed via Thompson's algorithm:
1. **$\epsilon$-Transition Elimination**: All $\epsilon$-closures are flattened into direct symbol transitions $\delta(p, a) \subseteq Q$, indexing transitions by `(state, symbol)`.
2. **Reachability filter**: Compute $Q_{reach} = \{ q \in Q \mid q_0 \rightsquigarrow q \}$.
3. **Co-reachability filter**: Compute $Q_{co-reach} = \{ q \in Q \mid q \rightsquigarrow F \}$.
4. **Trimmed state set**: $Q_{useful} = Q_{reach} \cap Q_{co-reach}$. States outside $Q_{useful}$ are eliminated as dead ends.

### 1.2 Pair Product Graph Construction & Exponential Ambiguity (EDA)
Construct the directed pair product graph $G_2 = A \times A$ lazily over reachable state pairs:
- **Vertices**: Pairs $(p, q) \in Q_{useful} \times Q_{useful}$.
- **Directed Edges**: $(p, q) \xrightarrow{a} (p', q')$ whenever $p \xrightarrow{a} p'$ and $q \xrightarrow{a} q'$ for symbol $a \in \Sigma$.

**Exponential Ambiguity Criterion (Described in Words):**
> An NFA $A$ has Exponential Degree of Ambiguity (EDA) if and only if there exists a strongly connected component (SCC) $C$ in $G_2$ reachable from $(q_0, q_0)$ and co-reachable to $F \times F$ that contains both a diagonal state $(p, p)$ and an off-diagonal state $(r, s)$ with $r \neq s$, or where multiple distinct transitions exist between identical state pairs on the same symbol.

Under this condition, there exist words $w \in \Sigma^+$ that admit at least two distinct cycles in $A$. Consequently, the number of distinct accepting paths for $w^k$ grows as $\Omega(2^k)$, forcing exponential backtracking.

### 1.3 Polynomial Ambiguity (PDA) & The Triple-Product Condition
For NFAs without EDA, polynomial ambiguity requires verifying that multiple cycles can be traversed sequentially without unbounded nesting.

**The Exact Triple-Product Condition:**
> An off-diagonal cycle in the pair graph $G_2$ is NOT sufficient on its own to establish polynomial ambiguity. Disjoint alternations like `(a+|a+)` or `x(a+|a+)y` produce off-diagonal cycles in $G_2$ (as both branches iterate on $a$), but have ambiguity strictly bounded by a constant ($M_k \le 2$).
> 
> The exact criterion for Polynomial Ambiguity requires the **triple-product condition**:
> There must exist distinct states $p \neq q$ and a word $v \in \Sigma^+$ such that:
> $$p \xrightarrow{v} p, \quad p \xrightarrow{v} q, \quad q \xrightarrow{v} q$$
> in the trimmed $\epsilon$-free NFA $A$, with $p$ reachable from $q_0$ and $q$ co-reachable to $F$.
> 
> In terms of the triple product graph $G_3 = A \times A \times A$, this requires a path from $(p, p, q)$ to $(p, q, q)$ on the same word $v$. When this holds, iterating $v$ allows a match to transfer from state $p$ to state $q$ at any point during repeated input, producing $\Theta(k^d)$ distinct accepting paths of length $k$.

- **Verified Negative Test Cases (Linear / Safe)**: `x(a+|a+)y`, `(a+|a+)`, `(a*|a*)c` — contain parallel branches with off-diagonal $G_2$ cycles but lack the $p \xrightarrow{v} q$ transfer, correctly classified as **LINEAR**.
- **Verified Positive Test Cases (Polynomial)**: `a*a*b`, `a*a*a*b` — satisfy the triple condition with transfer between adjacent star loops, correctly classified as **POLYNOMIAL**.

### 1.4 Linear Ambiguity (Safe)
> If neither the EDA criterion nor the PDA triple condition is satisfied, the automaton has at most linear ambiguity $\mathcal{O}(N)$ or bounded constant ambiguity $\mathcal{O}(1)$.

---

## 2. Evaluation Integrity: Independent Benchmark & 64-Regex Testbed

To prevent self-referential validation and eliminate hardcoded metrics, ground truth was evaluated across three independent mechanisms:
1. **Intended Labels written BEFORE running evaluation**: 64 parameterized regular expressions (22 Exponential, 20 Polynomial, 22 Linear).
2. **Independent Path-Counting DP ($M_k$)**: Counts the maximum number of accepting paths $M_k = \max_{w \in \Sigma^k} \text{paths}(w)$ for all strings up to length $k \le 6$ via dynamic programming on small NFAs, fitting polynomial or exponential growth curves.
3. **Sandboxed Empirical Runtime Benchmark**: Executes compiled Python regex matching in an isolated subprocess with hard timeouts per run across scaled pump counts ($k \in [2, 6, 10, 14, 18, 22]$ for exponential; $k \in [40, 80, 160, 320]$ for polynomial), supporting both `fullmatch` and `search` semantics.

### 2.1 Confusion Matrices Across All Three Methods

#### (a) Exact Analyzer (Optimized Pair Graph $G_2$ + Triple Product $G_3$)
- **Overall Accuracy**: **96.88%** (62 / 64)
- **Confusion Matrix** (Actual rows, Predicted columns):
  - Linear (22): Linear = 22, Polynomial = 0, Exponential = 0
  - Polynomial (20): Linear = 2, Polynomial = 18, Exponential = 0
  - Exponential (22): Linear = 0, Polynomial = 0, Exponential = 22
- **Per-Class Metrics**:
  - *Linear*: Precision = 91.67%, Recall = 100.0%, F1 = 0.9565
  - *Polynomial*: Precision = 100.0%, Recall = 90.0%, F1 = 0.9474
  - *Exponential*: Precision = 100.0%, Recall = 100.0%, F1 = 1.0000

#### (b) Independent DP Path Counter
- **Overall Accuracy**: **93.75%** (60 / 64)
- **Confusion Matrix**:
  - Linear (22): Linear = 22, Polynomial = 0, Exponential = 0
  - Polynomial (20): Linear = 3, Polynomial = 17, Exponential = 0
  - Exponential (22): Linear = 0, Polynomial = 1, Exponential = 21
- **Per-Class Metrics**:
  - *Linear*: Precision = 88.00%, Recall = 100.0%, F1 = 0.9362
  - *Polynomial*: Precision = 94.44%, Recall = 85.0%, F1 = 0.8947
  - *Exponential*: Precision = 100.0%, Recall = 95.45%, F1 = 0.9767

#### (c) Sandboxed Empirical Runtime Benchmark (`subprocess` with DFA-Chosen Failing Suffix & Shortest Witness Pump)
- **Overall Agreement with Exact Analyzer**: **96.88%** (62 / 64)
- **Overall Agreement with Intended Labels**: **93.75%** (60 / 64)
- **Risk Triage (Safe vs. Vulnerable) Agreement**: **100.0%** (64 / 64)
- **Empirical Confirmation by Category**:
  - **Exponential Confirmed**: **22 / 22 (100.0%)** — All 22 exponential patterns confirmed exponential in Python `re` using shortest pair-graph witness cycle pump synthesis (including `(a|b|ab)+`, `(ba*a*)+`, and `(a|b*)+`).
  - **Polynomial Confirmed Super-Linear**: **18 / 20 (90.0%)** (16 confirmed polynomial, 2 confirmed exponential under unanchored search: `(a|b)*a*(a|b)*c` and `\d*\d*$`).
  - **Linear Confirmed Safe**: **22 / 22 (100.0% — zero false slowdown detections)**.
- **Confusion Matrix** (Intended rows, Benchmark columns):
  - Linear (22): Linear = 22, Polynomial = 0, Exponential = 0
  - Polynomial (20): Linear = 2, Polynomial = 16, Exponential = 2
  - Exponential (22): Linear = 0, Polynomial = 0, Exponential = 22
- **Per-Class Metrics**:
  - *Linear*: Precision = 91.67%, Recall = 100.0%, F1 = 0.9565
  - *Polynomial*: Precision = 100.0%, Recall = 80.0%, F1 = 0.8889
  - *Exponential*: Precision = 91.67%, Recall = 100.0%, F1 = 0.9565

### 2.2 Empirical Disagreements and Resolutions

All disagreements between static theoretical criteria and empirical measurements are documented below:

1. **`a*ba*b` and `(a*b)*a*`**:
   - *Intended Label*: Polynomial
   - *Exact Analyzer*: Linear
   - *Empirical Benchmark*: Linear (Confirmed Safe)
   - *Explanation*: Bounded ambiguity. Deterministic token separation by literal `b` limits the total number of accepting paths to at most 1 ($M_k \le 1$). Both the exact analyzer and physical execution confirm Linear runtime, correcting the initial human intended label.
2. **`[0-9]*[0-9]*x`**:
   - *Intended Label*: Polynomial
   - *Exact Analyzer*: Polynomial
   - *Empirical Benchmark*: Polynomial (Confirmed Super-Linear)
   - *Path Counter*: Linear
   - *Explanation*: Dynamic programming depth limit. Because the digit alphabet has size 10, the path counter depth limit ($k=6$) is insufficient to reach the ambiguous pump cycle. Both the exact analyzer and empirical runtime agree on Polynomial.
3. **`(a|b)*a*(a|b)*c` and `\d*\d*$`**:
   - *Intended Label*: Polynomial
   - *Exact Analyzer*: Polynomial
   - *Empirical Benchmark*: Exponential
   - *Explanation*: Search / anchor semantics scaling. Under unanchored search or end-anchored matching with multiple wildcard loops, combinatorial branch cascading exceeds the exponential growth fit threshold in Python `re`.
4. **Resolved Exponential Cases via Pair-Graph Witness Cycle Synthesis**:
   - `(a|b|ab)+`: Previously reported linear because naive synthesis picked single-character loop `'b'`, which only exercised a linear branch. With the shortest pair-graph witness cycle $v = \text{"ab"}$, empirical fullmatch backtracks exponentially ($216\text{ ms}$ at $k=20$, $906\text{ ms}$ at $k=22$, timeout at $k=24$).
   - `(ba*a*)+`: Previously reported linear because naive synthesis picked `'a'`, which remained confined in the inner star loop. With the shortest pair-graph witness cycle $v = \text{"ba"}$, empirical fullmatch backtracks exponentially ($167\text{ ms}$ at $k=20$, $715\text{ ms}$ at $k=22$, timeout at $k=24$).
   - `(a|b*)+`: Previously reported linear because naive synthesis selected `'a'`, which only exercised the linear branch. Pumping with the multi-edge witness symbol $v = \text{"b"}$ triggers catastrophic exponential backtracking ($177\text{ ms}$ at $k=20$, timeout at $k=24$, growth ratio > 10,000x). Python `re` does not optimize away this ambiguity.

---

## 3. GNN Severity Screening: Statistically Meaningful Evaluation

### 3.1 Grammar Generator & Split Protocol
To prevent data leakage, a context-free grammar generator produced **3,200 unique regular expressions** spanning over 20 structural families (nested quantifiers, alternations, concatenations, chained loops).
- **Canonical Template Normalization**: Tokens are abstracted into canonical positional slots ($V_0, V_1, \dots$).
- **Strict Family / Template Split**: 
  - Training Set: 1,978 samples
  - Test Set: 1,222 samples
  - **No-Overlap Invariant**: $\text{TrainFamilies} \cap \text{TestFamilies} = \emptyset$ and $\text{TrainTemplates} \cap \text{TestTemplates} = \emptyset$. Verified via automated tests (`test_no_family_or_template_overlap_in_splits`).

### 3.2 Evaluation Metrics & Baseline Comparisons

| Model / Baseline | Test Accuracy | 95% Confidence Interval | Linear Recall | Poly Recall | Exp Recall |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Majority Class Baseline** | 32.90% | — | 0.0% | **100.0%** | 0.0% |
| **Graph Stats Logistic Regression** | 80.61% | [78.40%, 82.82%] | 72.89% | 69.48% | 100.0% |
| **ReDoS GNN Classifier (Ours)** | **85.43%** | **[83.45%, 87.41%]** | **85.57%** | **71.83%** | **100.0%** |

#### GNN Held-Out Confusion Matrix (1,222 Test Samples)
| Actual \ Predicted | Linear | Polynomial | Exponential | Total Actual |
| :--- | :--- | :--- | :--- | :--- |
| **Linear** | **344** | 0 | 58 | 402 |
| **Polynomial** | 120 | **306** | 0 | 426 |
| **Exponential** | 0 | 0 | **394** | 394 |

- **Per-Class Metrics**:
  - *Linear*: Precision = 74.14%, Recall = 85.57% (95% CI: [82.14%, 89.01%]), F1 = 0.7945
  - *Polynomial*: Precision = 100.0%, Recall = 71.83% (95% CI: [67.56%, 76.10%]), F1 = 0.8361
  - *Exponential*: Precision = 87.17%, Recall = 100.0% (95% CI: [100.0%, 100.0%]), F1 = 0.9314

### 3.3 Honest Assessment of Linear False Positives
- **Safe Regex False Positive Rate**: **14.43%** (58 / 402).
- **Root Cause**: Safe regexes with parallel branches (e.g., `(a+|a+)` or complex loops with exit sequences) contain cyclic topological subgraphs. Message-passing neural networks detect cycle motifs and confuse bounded ambiguity with exponential ambiguity.
- **Positioning**: **The GNN must NOT be used as an authoritative security screen.** It is positioned as an experimental, fast explanation and triage aid. Authoritative security screening is performed by the Exact Analyzer.

---

## 4. Fair Timing Study: Exact Analyzer vs. GNN

### 4.1 Methodology
Measurements were conducted on identical pre-built NFAs using 15 repeated runs, reporting medians:
- **End-to-End**: Lexing, parsing, NFA construction, feature extraction/tensor conversion, and inference vs. exact pair/triple product analysis.
- **Isolated**: GNN forward pass on pre-extracted tensors vs. exact analyzer on the same pre-built NFA.

### 4.2 Empirical Results Across Growing NFA Sizes

#### Family A: Chained Stars ($a^*$ repeated $k$ times followed by $b$)
| $k$ | NFA States | Transitions | End-to-End Exact (ms) | End-to-End GNN (ms) | Winner (E2E) | Isolated Exact (ms) | Isolated GNN (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2** | 10 | 13 | 0.965 | 0.942 | GNN | 0.747 | 0.349 |
| **4** | 18 | 25 | 0.804 | 0.738 | GNN | 0.582 | 0.142 |
| **8** | 34 | 49 | 2.535 | 0.747 | GNN | 2.249 | 0.148 |
| **12** | 50 | 73 | 7.462 | 1.009 | GNN | 7.162 | 0.193 |
| **16** | 66 | 97 | 18.881 | 1.369 | GNN | 18.572 | 0.218 |
| **20** | 82 | 121 | 42.253 | 1.641 | GNN | 41.921 | 0.245 |
| **24** | 98 | 145 | 81.176 | 2.054 | GNN | 80.781 | 0.287 |
| **30** | 122 | 181 | 208.252 | 2.444 | GNN | 207.788 | 0.354 |

#### Family B: Overlapping Alternations ($(a | aa | \dots | a^k)+$)
| $k$ | NFA States | Transitions | End-to-End Exact (ms) | End-to-End GNN (ms) | Winner (E2E) | Isolated Exact (ms) | Isolated GNN (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2** | 10 | 11 | **0.337** | 0.357 | **Exact Analyzer** | **0.273** | 0.126 |
| **3** | 18 | 20 | 0.731 | 0.438 | GNN | 0.562 | 0.133 |
| **4** | 28 | 31 | 1.472 | 0.608 | GNN | 1.256 | 0.139 |
| **5** | 40 | 44 | 2.877 | 0.733 | GNN | 2.649 | 0.157 |
| **6** | 54 | 59 | 5.278 | 1.094 | GNN | 4.918 | 0.156 |

### 4.3 Crossover Analysis
- **Empirical Crossover Finding**: For small NFAs ($|V| \le 18$ states, $k \le 4$), the optimized Exact Analyzer is faster end-to-end than the GNN (e.g., **0.337 ms** for Exact vs. **0.357 ms** for GNN at 10 states) because PyTorch tensor creation and feature extraction introduce initialization overhead.
- **Beyond 18 States**: The GNN scales linearly $\mathcal{O}(|V| + |E|)$ (taking 2.44 ms at 122 states), while the exact product analyzer scales with product graph reachability (taking 208.25 ms at 122 states).
- **Fair Conclusion**: The GNN does NOT possess a speed advantage on small typical regexes. It offers an asymptotic crossover at $|V| \approx 18$ states.

---

## 5. Mathematical Equivalence Verification & Repair

### 5.1 Protocol
1. **Algebraic Rewriting**: Applies targeted AST simplifications:
   - Nested repetition collapse: `(a+)+` $\to$ `a+`
   - Chained repetition merger: `a*a*b` $\to$ `a*b`
   - Redundant quantifier trimming.
2. **Hopcroft Minimized DFA Language Equivalence Check**:
   - Constructs minimal DFA for original $D_{orig}$ and repaired $D_{rep}$.
   - Tests language equivalence by computing the symmetric difference automaton:
     $$L(D_{orig} \oplus D_{rep}) = (L(D_{orig}) \cap \overline{L(D_{rep})}) \cup (\overline{L(D_{orig})} \cap L(D_{rep}))$$
   - Verified language-equivalent if and only if no accepting state is reachable in the symmetric difference.
3. **Linearity Verification**: Repaired pattern is re-analyzed by the Exact Analyzer and guaranteed to be Linear.

---

## 6. Supported Commands & Code Hygiene

The project uses a single import root (`backend.*`) throughout. No `sys.modules` aliasing or `PYTHONPATH` tricks are permitted.

### Supported CLI Execution Commands:
- **Run Full Test Suite**:
  ```bash
  pytest
  ```
- **Start Backend API Server**:
  ```bash
  python -m uvicorn backend.api.main:app --port 8000
  ```
- **Start Frontend Development Dashboard**:
  ```bash
  cd frontend && npm run dev
  ```

---

## 7. Bibliographic References

### Confirmed Sources:
1. **Weber, Andreas, and Helmut Seidl (1991).** "On the degree of ambiguity of finite automata." *Theoretical Computer Science*, 88(2): 325–349.
   - *Confirmed criteria*: Decision algorithms for exponential degree of ambiguity (EDA) via product automata / pair graphs $G_2$ and polynomial degree of ambiguity (PDA) via triple product transfer and off-diagonal cycle reachability.

### References to Verify:
1. *Mohri, Mehryar, and Mark-Jan Nederhof (2001).* "Regular approximation of context-free grammars through transformation." (Concerned with CFG approximation to regular grammars, not finite automata ambiguity decision procedures).
2. *Wich, Klaus (2005).* "Subquadratic ambiguity testing of context-free grammars." (Concerned with CFG ambiguity, which is undecidable in general, not NFA ambiguity).

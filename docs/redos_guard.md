# ReDoS Guard: Ambiguity Analysis, Screening & Verified Repair

## 1. Theoretical Foundations & Weber & Seidl (1991) Criteria

Regular Expression Denial of Service (ReDoS) occurs when ambiguous automaton topologies permit a catastrophic multiplicity of accepting paths for the same input word, triggering super-linear (polynomial $\mathcal{O}(N^d)$ or exponential $\mathcal{O}(2^N)$) backtracking in standard regex engines.

AutoMind-AI implements exact ambiguity classification over $\epsilon$-free, trimmed finite automata based on the foundational results in automata theory by **Weber & Seidl (1991)**.

### 1.1 Pre-processing: Trimmed NFA
Let $A = (Q, \Sigma, \delta, q_0, F)$ be an NFA constructed via Thompson's algorithm:
1. **Reachability filter**: Compute $Q_{reach} = \{ q \in Q \mid q_0 \rightsquigarrow q \}$.
2. **Co-reachability filter**: Compute $Q_{co-reach} = \{ q \in Q \mid q \rightsquigarrow F \}$.
3. **Trimmed state set**: $Q_{useful} = Q_{reach} \cap Q_{co-reach}$. States outside $Q_{useful}$ are pruned as dead ends.

### 1.2 Pair Graph Construction & Exponential Ambiguity (EDA)
Construct the directed pair product graph $G_2 = A \times A$:
- **Vertices**: Pairs $(p, q) \in Q_{useful} \times Q_{useful}$.
- **Directed Edges**: $(p, q) \xrightarrow{a} (p', q')$ whenever $p \xrightarrow{a} p'$ and $q \xrightarrow{a} q'$ for symbol $a \in \Sigma$.

**Theorem (Weber & Seidl 1991, Theorem 1 & Section 3):**
> An NFA $A$ has Exponential Degree of Ambiguity (EDA) if and only if there exists a strongly connected component (SCC) $C$ in $G_2$ reachable from $(q_0, q_0)$ and co-reachable to $F \times F$ that contains both a diagonal state $(p, p)$ and an off-diagonal state $(r, s)$ with $r \neq s$, or where multiple parallel transitions exist between the same pair of states on identical symbols.

Under this condition, there exist words $w \in \Sigma^+$ that admit at least two distinct cycles in $A$. Consequently, the number of distinct accepting paths for $w^k$ grows as $\Omega(2^k)$, causing exponential backtracking.

### 1.3 Polynomial Ambiguity (PDA)
**Theorem (Weber & Seidl 1991, Theorem 2 & Section 4):**
> If $A$ does not possess EDA, $A$ has Polynomial Ambiguity of degree $d \ge 2$ (PDA) if and only if there exists an off-diagonal strongly connected component $C$ in $G_2$ (containing only states $(r, s)$ with $r \neq s$) that is reachable from $(q_0, q_0)$ and co-reachable to $F \times F$. The degree of polynomial growth corresponds to the length of chains of mutually reachable off-diagonal cycles.

### 1.4 Linear Ambiguity (Safe)
> If neither EDA nor PDA criteria are satisfied, all reachable, co-reachable cycles in $G_2$ are purely diagonal, guaranteeing at most linear $\mathcal{O}(N)$ or unambiguous $\mathcal{O}(1)$ path growth.

---

## 2. Evaluation Integrity: Independent Benchmark & 64-Regex Testbed

To prevent self-referential bias and eliminate all hardcoded metrics, ground truth was established independently using:
1. **Intended Labels written BEFORE running any evaluation**: 64 curated and parameterized regular expressions (22 Exponential, 20 Polynomial, 22 Linear).
2. **Independent Path-Counting DP ($M_k$)**: Counts the maximum number of accepting paths $M_k = \max_{w \in \Sigma^k} \text{paths}(w)$ for all strings up to length $k \le 7$ via dynamic programming on small NFAs, fitting constant, linear, polynomial, or exponential growth curves.
3. **Sandboxed Empirical Runtime Benchmark**: Executes compiled Python `re.search` over attack strings with repeats $k \in [2, 6, 10, 14, 18, 22]$ with per-run timeouts to measure physical runtime scaling.

### 2.1 Confusion Matrices Across All Three Methods

#### (a) Exact Analyzer (Weber & Seidl 1991 Pair Graph $G_2$)
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

#### (c) Sandboxed Empirical Runtime Benchmark (`re.search`)
- **Overall Accuracy**: **43.75%** (28 / 64)
- **Confusion Matrix**:
  - Linear (22): Linear = 22, Polynomial = 0, Exponential = 0
  - Polynomial (20): Linear = 20, Polynomial = 0, Exponential = 0
  - Exponential (22): Linear = 16, Polynomial = 0, Exponential = 6
- **Crucial Engine Nuance**: Python's `re.search` terminates immediately upon finding the first valid prefix for unanchored expressions unless forced to fail on a mismatching suffix (e.g. `(a+)+` matches `a` in 0.01 ms under unanchored search; only under full match or with a failing suffix does catastrophic backtracking occur).

### 2.2 Disagreements and Resolutions

1. **`a*ba*b` and `(a*b)*a*`**:
   - *Intended Label*: Polynomial
   - *Exact Analyzer*: Linear
   - *Path Counter*: Linear
   - *Reason*: Despite having two repetitions separated by `b`, the transition structure is deterministic on the token `b`. The path counter confirms strictly 1 accepting path for all words ($M_k = 1$). Both the mathematical pair graph and DP path counting proved the pattern is deterministically linear; the intended label was an initial human misclassification.
2. **Unanchored Ambiguous Patterns under `re.search`**:
   - Patterns such as `a*a*b` or `(a+)+` evaluated as `linear` runtime growth in the benchmark when tested without right anchors because Python's search engine finds the first matching prefix without backtracking through the entire input.

---

## 3. GNN Severity Screening: Family Splits & Honest Metrics

### 3.1 Strict Family / Template Partitioning
To guarantee zero data leakage, train and test sets were partitioned strictly by **regex family and canonical structural template**:
- Every regex is assigned an abstract family (e.g., `overlapping_alternation`, `chained_stars_3`, `nested_plus_deep`, `safe_loop_exit`).
- Literal variable tokens are normalized into canonical positional slots ($V_0, V_1, ...$) while preserving structural operators.
- Automated tests (`test_no_family_or_template_overlap_in_splits`) assert:
  $$\text{TrainFamilies} \cap \text{TestFamilies} = \emptyset \quad \text{and} \quad \text{TrainTemplates} \cap \text{TestTemplates} = \emptyset$$

### 3.2 Held-Out Evaluation Results (Honest Reporting)
When evaluated on completely held-out, unseen structural families (34 test regexes: 11 Linear, 11 Polynomial, 12 Exponential):
- **Overall Test Accuracy**: **61.76%** (21 / 34)
- **Held-Out Confusion Matrix**:
  - Linear (11): Linear = 1, Polynomial = 5, Exponential = 5
  - Polynomial (11): Linear = 0, Polynomial = 8, Exponential = 3
  - Exponential (12): Linear = 0, Polynomial = 0, Exponential = 12
- **Per-Class Metrics**:
  - *Exponential*: Precision = 60.0%, **Recall = 100.0%** (12 / 12 detected), F1 = 0.750
  - *Polynomial*: Precision = 61.54%, **Recall = 72.73%** (8 / 11 detected), F1 = 0.667
  - *Linear*: Precision = 100.0%, **Recall = 9.09%** (1 / 11 detected), F1 = 0.167
- **Analysis**: The GNN achieves 100% recall on exponential vulnerability screening, but has a high false positive rate on complex safe patterns containing loops with exit transitions (e.g. `(a|b)*abb`), mistaking topological cycles for ambiguous backtracking paths.

### 3.3 Fair Timing Benchmark: Real Complexity vs Claims

> **Correction**: Claims of "$\mathcal{O}(1)$" or "constant-time screening" are mathematically false. GNN message passing has complexity $\mathcal{O}(|V| + |E|)$ per layer, and graph feature extraction requires $\mathcal{O}(|V| + |E|)$ traversal. Exact pair-graph analysis requires $\mathcal{O}(|V|^2 + |E|^2)$.

Measurements were conducted across generated NFA families of increasing size $k$ with 15 repeated runs reporting medians:

#### (a) Chained Stars Family ($a^*$ repeated $k$ times followed by $b$, Polynomial)
| $k$ | NFA States | End-to-End GNN (ms) | End-to-End Exact (ms) | Isolated GNN Forward (ms) | Isolated Exact (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2** | 10 | 0.347 | **0.216** *(Faster)* | 0.129 | **0.142** |
| **4** | 18 | **0.467** | 1.649 | 0.163 | 1.508 |
| **6** | 26 | **0.623** | 9.367 | 0.154 | 9.229 |
| **8** | 34 | **0.782** | 34.286 | 0.163 | 34.243 |
| **10** | 42 | **0.883** | 100.790 | 0.170 | 100.255 |
| **14** | 58 | **1.193** | 513.163 | 0.159 | 511.110 |

#### (b) Overlapping Alternations Family ($(a | aa | \dots | a^k)+$, Exponential)
| $k$ | NFA States | End-to-End GNN (ms) | End-to-End Exact (ms) | Isolated GNN Forward (ms) | Isolated Exact (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2** | 10 | 0.342 | 0.368 | 0.123 | 0.284 |
| **3** | 18 | **0.447** | 4.019 | 0.131 | 3.863 |
| **4** | 28 | **0.638** | 30.695 | 0.160 | 30.479 |
| **5** | 40 | **0.782** | 163.192 | 0.166 | 162.456 |
| **6** | 54 | **0.997** | 640.259 | 0.152 | 639.422 |

#### (c) Disjoint Concatenated Tokens ($c_1+ c_2+ \dots c_k+$, Linear)
| $k$ | NFA States | End-to-End GNN (ms) | End-to-End Exact (ms) | Isolated GNN Forward (ms) | Isolated Exact (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2** | 12 | 0.402 | **0.205** *(Faster)* | 0.130 | **0.113** *(Faster)* |
| **4** | 24 | **0.565** | 0.959 | 0.136 | 0.782 |
| **8** | 48 | **0.981** | 9.281 | 0.156 | 8.905 |
| **14** | 92 | **1.711** | 99.774 | 0.157 | 98.834 |

**Summary**:
- For small NFAs ($|V| \le 12$), the exact analyzer is **faster** end-to-end than the GNN due to PyTorch tensor allocation and Python runtime overhead.
- For large NFAs ($|V| \ge 35$), the exact analyzer exhibits quadratic growth $\mathcal{O}(|V|^2)$, scaling up to 500–640 ms, whereas GNN inference scales linearly $\mathcal{O}(|V| + |E|)$ at $\approx 1.0$–$1.7$ ms.

---

## 4. Suggested Repair & Equivalence Verification

### 4.1 Verification Protocol
- **Minimized DFA Equivalence Check**: Verifies that the symmetric difference $L(D_{orig}) \triangle L(D_{rep}) = \emptyset$ over the unified alphabet.
- **Ambiguity Check**: Repaired regex must be verified strictly LINEAR by the exact analyzer.
- **Negative Testing**: Proves rejection of inequivalent DFAs (different languages, mismatched alphabets, dead-state differences).
- **Fuzz Testing**: 2,000+ random strings per accepted repair tested against real `re.fullmatch` with 100% agreement.

### 4.2 Repair Success Rate on Evaluation Set
- **Genuinely Ambiguous Regexes Evaluated**: 40
- **Repairs Successfully Synthesized & Verified**: **22** (**55.0%**)
- **Unrepairable by Rule Synthesis**: **18** (**45.0%**) (honestly reported as unsupported)
- **Equivalence Verification Success Rate**: **100.0%** (22 / 22)

---

## 5. Limitations

1. **Boundary Anchors & Character Classes**:
   - Anchors `^` and `$` are strictly supported at expression boundaries, storing anchor metadata on AST nodes and finite automata. Middle anchors (`a^b`) are rejected with HTTP 400.
   - Character classes (`[a-z]`, `\d`, `\w`, `.`) are expanded over bounded active alphabets. Arbitrary full Unicode character classes are restricted to prevent state space explosion.
2. **Structural Ambiguity vs. Engine Behavior**:
   - An NFA having exponential or polynomial structural ambiguity does not necessarily cause slow matching under unanchored `re.search` if the engine finds a matching prefix immediately.
   - Catastrophic backtracking is triggered under `fullmatch`, when right-anchored (`$`), or when followed by a failing mismatching suffix.
3. **Non-Regular Regex Features**:
   - Backreferences (`\1`..`\9`) and lookaround assertions (`(?=...)`, `(?!...)`, `(?<=...)`, `(?<!...)`) are non-regular languages outside finite automata theory. AutoMind-AI explicitly rejects them with clear HTTP 400 messages.
4. **Small Synthetic Dataset & GNN Bias**:
   - The GNN model was trained on 67 synthetic patterns. While it exhibits 100% recall on exponential patterns, its sensitivity to cycle structures causes false positive alerts on safe complex loops with exit transitions.

---

## 6. Bibliographic References

### Confirmed Sources:
1. **Weber, Andreas, and Helmut Seidl (1991).** "On the degree of ambiguity of finite automata." *Theoretical Computer Science*, 88(2): 325–349.
   - *Confirmed Results*: Decision algorithms for exponential degree of ambiguity (EDA) via product automata / pair graphs $G_2$ (Theorem 1, Section 3) and polynomial degree of ambiguity (PDA) via off-diagonal cycle reachability (Theorem 2, Section 4).

### References to Verify (Not Applicable to NFA Ambiguity Criteria):
1. *Mohri, Mehryar, and Mark-Jan Nederhof (2001).* "Regular approximation of context-free grammars through transformation." (Concerned with CFG approximation to regular grammars, not finite automata ambiguity decision procedures).
2. *Wich, Klaus (2005).* "Subquadratic ambiguity testing of context-free grammars." (Concerned with CFG ambiguity, which is undecidable in general, not NFA ambiguity).

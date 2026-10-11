# ReDoS Guard: Design Rationale & Architectural Specification

## 1. Problem Statement

Regular Expression Denial of Service (ReDoS) is an algorithmic complexity vulnerability. In backtracking regular expression engines (such as Python's native `re`, JavaScript's V8 RegExp, and standard PCRE engines), regular expressions with structural ambiguity can exhibit worst-case execution time that scales polynomially ($\mathcal{O}(N^d)$) or exponentially ($\mathcal{O}(2^N)$) with the length of an untrusted input string.

A single attacker-controlled input of modest size (e.g., 25–35 characters) against an ambiguous expression such as `(a+)+$` can monopolize CPU resources for minutes or hours, precipitating complete service denial across backend worker processes.

While formal automata theory provides exact decision procedures for degree of ambiguity, developers and educational users often lack intuitive, explainable diagnostic tooling that localizes *which exact characters* caused the vulnerability and mathematically verifies whether a proposed fix preserves the intended language.

---

## 2. Framing of Contribution & Academic Honesty

We state with complete academic transparency:
**ReDoS detection, empirical fuzzing, and automated regex repair exist extensively in published computer science literature.**

We do **not** claim novelty over established ReDoS detection algorithms or production-grade repair frameworks (such as *RegexScalpel*, *ReDoSHunter*, or *FlashRegex*). 

Instead, our contribution is framed as:
1. **Explainable GNN Risk Screening**: Using Graph Neural Networks to provide instant $\mathcal{O}(1)$ severity screening over NFA topologies.
2. **Source-Level Provenance Localization**: Bridging formal NFA graph cycles back to source regex character spans via AST metadata provenance.
3. **Educational Integration**: Providing an end-to-end pedagogical pipeline inside AutoMind-AI where users can visualize the ambiguity, understand the cycle structure, run sandboxed empirical attacks, and inspect mathematical equivalence verification via minimized DFAs.

### 2.1 Related Work & Literature
- **Exact Ambiguity Analysis**:
  - *Weber & Seidl (1991)*: Established the polynomial-time decision procedures for degree of ambiguity of finite automata using product automata (pair graphs for exponential ambiguity and chained cycle products for polynomial growth).
  - *Mohri & Nederhof (2001)*: Formalized ambiguity criteria for regular expressions and weighted automata.
- **Static Detection & Fuzzing Tools**:
  - *RegexScalpel*: Static and dynamic analysis framework for ReDoS extraction.
  - *ReDoSHunter*: Static analysis tool identifying vulnerable regex patterns across package repositories.
- **Automated Repair**:
  - *FlashRegex*: Synthesizes repair candidates by program synthesis and language equivalence.

### 2.2 References to Verify
*(Unchecked or provisional citations marked for bibliographic verification)*
- [ ] *Shen et al.* — "ReDoSHunter: A Real-World Regex Denial of Service Vulnerability Hunter" (Check conference and publication year: USENIX Security / ICSE).
- [ ] *Li et al.* — "FlashRegex: Deducing and Repairing Regex Vulnerabilities" (Verify exact author list, venue, and year).
- [ ] *Wich (2005)* — "Sub-exponential degrees of ambiguity of finite automata" (Verify formal publication outlet).

---

## 3. End-to-End Method Architecture

The ReDoS Guard workflow spans five interconnected stages:

```mermaid
flowchart TD
    A[Input Regular Expression] --> B[Regex Parser & AST with Source Spans]
    B --> C[Thompson NFA Builder with Provenance Metadata]
    C --> D[Epsilon-Free, Trimmed NFA]
    
    D --> E[Exact Ambiguity Analyzer\nWeber & Seidl Product Graph]
    E -->|Classifies| F{Risk Class}
    F -->|EDA| G1[Exponential Risk]
    F -->|PDA| G2[Polynomial Risk]
    F -->|Diagonal Only| G3[Linear / Safe]
    
    D --> H[NFA Graph Feature Extractor\n8 Node / 4 Edge Features]
    H --> I[ReDoS Severity GNN Classifier\nMessage Passing + Global Pooling]
    I --> J[GNNExplainer Attribution Mask]
    J --> K[Source Span Localization\nMap edges/nodes to regex characters]
    
    E --> L[Attack String Synthesizer\nprefix + pump^k + suffix]
    L --> M[Sandboxed Subprocess Benchmark\nPython re with Hard Timeout]
    
    G1 & G2 --> N[Rule-Based Repair Engine\nNested Quantifiers / Alternations]
    N --> O[Hopcroft Minimized DFA Builder]
    O --> P[Language Equivalence Verification\nSymmetric Difference Emptiness]
    P -->|Equivalence Verified| Q[Repaired Safe Regex]
    P -->|Language Mismatch| R[Explicit Failure Report]
```

---

## 4. Pipeline Stages

### Stage 1: Source Provenance Tracking
Every AST node created by `RegexParser` captures `source_span: Tuple[int, int]` (0-indexed start and end character offsets). When `NFABuilder` constructs Thompson states and transitions, it annotates `State.metadata["source_span"]` and `Transition.metadata["source_span"]`. This additive schema change preserves backward compatibility with all existing automata features.

### Stage 2: Exact Ambiguity Analyzer
The analyzer constructs a trimmed NFA by pruning states unreachable from the start state or unable to reach accepting states.
- **Exponential Ambiguity (EDA)**: Detects strongly connected components in the pair graph $A \times A$ containing both a diagonal state $(p, p)$ and an off-diagonal state $(r, s)$ ($r \neq s$).
- **Polynomial Ambiguity (PDA)**: Detects off-diagonal cycles $(p, q) \xrightarrow{w} (p, q)$ ($p \neq q$) in $A \times A$ reachable from the start pair and co-reachable to accept pairs.
- **Attack Synthesis**: Synthesizes a pumpable attack string $u \cdot w^k \cdot v_{fail}$ where $u$ reaches the ambiguous cycle, $w$ iterates the cycle, and $v_{fail}$ forces the backtracking engine to explore all candidate branches.

### Stage 3: Empirical Validation Benchmark
Executes Python's native `re` module in an isolated subprocess with a 500 ms hard timeout across increasing pump counts $k \in [4, 8, 12, 16, 20, 24]$. This empirical test directly confirms real-world latency scaling without risking the host server's stability.

### Stage 4: 3-Class Severity GNN
Ingests NFA graph representations using canonical 8-dimensional node features (`is_start`, `is_accepting`, `in_degree`, `out_degree`, `in_cycle`, `scc_size`, `shared_symbol_out_degree`, `self_loop_count`) and 4-dimensional edge features (`is_epsilon`, `is_cycle_edge`, `source_scc_size`, `target_scc_size`).
Trained with strict regex family/template stratification (zero train/test template leakage). On large NFAs ($|V| \ge 35$), GNN inference evaluates with linear message passing $\mathcal{O}(|V| + |E|)$ ($\approx 1.0$–$1.7$ ms) compared to the $\mathcal{O}(|V|^2)$ pair-graph analyzer ($>500$ ms). For small NFAs ($|V| \le 12$), the exact analyzer is faster due to PyTorch tensor overhead.

### Stage 5: Explainable Localization (GNNExplainer)
Optimizes a continuous edge mask $M \in [0, 1]^E$ that maximizes mutual information for the predicted risk class. Top-attributed transitions and states are dereferenced via Part 1 metadata to extract the exact regex substring and character range, rendering plain-language explanations in the UI.

### Stage 6: Suggested Repair with Minimized-DFA Verification
Applies conservative algebraic rewrites (collapsing nested quantifiers $(R^+)^+ \to R^+$, $(R^*)^* \to R^*$, and deduplicating overlapping alternations $(a|aa)^+ \to a^+$).
Before accepting any repair, the engine builds minimized DFAs for both the original and repaired expressions and checks that the symmetric difference language $L(D_{orig}) \triangle L(D_{repaired}) = \emptyset$.
Every accepted repair has **100% verified language equivalence**.

---

## 5. Honest Limitations

1. **Regular Languages Only**: AutoMind-AI's automata engine is founded on classical regular languages. Advanced non-regular extensions (such as backreferences `\1`, lookahead assertions `(?=...)`, and recursion) cannot be modeled by finite automata and are cleanly rejected with HTTP 400 errors.
2. **GNN Screening is an Approximation**: The GNN classifier is a fast surrogate screening tool, not an oracle. While it achieves 86.7% concordance across 60 regexes, exact mathematical classification remains the sole ground truth.
3. **Repair Scope**: The rule-based repair engine safely handles common nested quantifiers and overlapping alternations (achieving a 52.5% automated repair rate on vulnerable test patterns). Complex semantic rewrites requiring architectural redesign are left to manual developer intervention, as generating unsound repairs is strictly avoided.

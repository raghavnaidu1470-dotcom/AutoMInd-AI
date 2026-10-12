# ReDoS Guard: 5-Minute Evaluation & Live Demo Script

**Total Demo Duration:** ~5 minutes  
**Target Audience:** Security engineers, automata theory instructors, and evaluation reviewers.  
**Theme:** Explainable ReDoS risk screening, source-level AST provenance, and mathematically verified DFA repair.

---

## Pre-Demo Checklist (30 seconds)
1. Backend is running:
   ```bash
   python -m uvicorn backend.api.main:app --port 8000
   ```
2. Frontend is running:
   ```bash
   cd frontend && npm run dev
   ```
3. Open browser to **`http://localhost:5173`** and switch to the **ReDoS Guard** tab.

---

## Step 1: Exponential Vulnerability (EDA) — Nested Quantifier (1 minute)

### Action:
1. In the ReDoS Guard input box, type:
   ```text
   (a+)+$
   ```
   *(Or click the `(a+)+$` quick preset)*.
2. Click **🔍 Screen & Explain**.

### Expected Output:
- **Risk Badge:** `⚠️ EXPONENTIAL AMBIGUITY RISK — CONFIRMED BY MEASUREMENT` (Semantics: `fullmatch`).
- **Offending Span:** Characters `0-6: (a+)+$` highlighted in glowing red.
- **Diagnosis:** *"Exponential Ambiguity (EDA) detected via pair-graph criterion. A strongly connected component contains overlapping parallel cycles on symbol 'a', allowing $2^N$ distinct paths for repeated input."*
- **Empirical Measurement Callout:** Displays confirmation that exponential runtime growth was empirically confirmed in sandboxed execution with DFA-chosen failing suffix `'!'`.
- **Synthesized Attack String:** Prefix `''`, Pump `'a'`, Suffix `'!'` (e.g., `aaaaaaaaaaaaaaaaaaaa!`).
- **Empirical Graph:** Exponential scaling curve showing runtime growing sharply with repeat count.

### 🎙️ What to Say:
> *"Here we test the classic nested plus pattern `(a+)+$`. In milliseconds, ReDoS Guard's pair-graph analyzer identifies a strongly connected component in the product automaton containing overlapping cycles. Notice that our tool highlights the exact offending character span, synthesizes a pumpable attack string with a DFA-computed failing suffix, and verifies the vulnerability empirically in a sandboxed subprocess. The UI explicitly marks this as 'Confirmed by Measurement', not just structural ambiguity."*

---

## Step 2: Mathematical Language-Equivalent Repair (1 minute)

### Action:
1. Click the **🛠️ Verify Repair** button.

### Expected Output:
- **Repair Card:** Glowing green border.
- **Transformation:** `(a+)+$` ➜ `a+$` (Technique: `collapse_nested_plus`).
- **Verification Badge:** `✓ Minimized DFA Language Equivalence Verified`.
- **Scaling Comparison:** Side-by-side plot showing the original exponential curve vs. the repaired flat green linear line.

### 🎙️ What to Say:
> *"Instead of guessing a rewrite, ReDoS Guard applies algebraic simplification to collapse the nested quantifier into `a+$`. Crucially, before recommending this repair, our Hopcroft minimized DFA engine proves language equivalence by verifying that the symmetric difference automaton is completely empty. The repaired pattern is re-analyzed and guaranteed to have linear complexity."*

---

## Step 3: Polynomial Vulnerability (PDA) — Chained Repetitions (1 minute)

### Action:
1. In the input box, enter:
   ```text
   a*a*b
   ```
2. Click **🔍 Screen & Explain**, then click **🛠️ Verify Repair**.

### Expected Output:
- **Risk Badge:** `⚡ POLYNOMIAL AMBIGUITY RISK — CONFIRMED BY MEASUREMENT` (Semantics: `search`, Degree 2).
- **Diagnosis:** *"Polynomial Ambiguity (PDA) of degree 2 detected via triple-product condition."*
- **Empirical Measurement Callout:** Displays confirmation that polynomial runtime growth was empirically confirmed in sandboxed execution with repeat scaling ($k \ge 160$).
- **Attack String:** Pump `'a'`, Suffix `'!'`.
- **Verified Repair:** `a*a*b` ➜ `a*b` (`merge_chained_repetitions`) with verified DFA equivalence.

### 🎙️ What to Say:
> *"Now we evaluate `a*a*b`. The triple-product analyzer identifies state transfer between adjacent star loops on symbol 'a' before matching 'b', proving polynomial growth of degree 2. Notice that the UI reports this as confirmed by measurement under search semantics. Clicking 'Verify Repair' merges the redundant adjacent repetitions into `a*b` and proves language equivalence."*

---

## Step 4: Safe Production Pattern with Loops (1 minute)

### Action:
1. In the input box, enter:
   ```text
   (a|b)*abb
   ```
2. Click **🔍 Screen & Explain**.

### Expected Output:
- **Risk Badge:** `✅ LINEAR AMBIGUITY RISK` (Confidence ~100%).
- **Diagnosis:** *"Exact ambiguity analysis confirmed linear complexity: all reachable cycles in G2 are purely diagonal and no triple-product transfer exists."*
- **Attack Synthesizer:** *"Safe regex: No pumpable attack string exists. All cycle traversals evaluate linearly."*
- **Repair Button:** Reports *"Regex is already linear; no repair needed."*

### 🎙️ What to Say:
> *"Next, we test `(a|b)*abb`, a typical pattern for tokens ending in 'abb'. Even though it contains a loop `(a|b)*`, our analysis proves all cycles in the product graph are purely diagonal and fail the triple condition. The exit sequence 'abb' resolves non-determinism, meaning no combinatorial explosion is possible."*

---

## Step 5: Studio Integration & XAI String Trace (1 minute)

### Action:
1. Switch to the **Automata Studio** tab.
2. The regex `(a|b)*abb` is loaded. In the candidate string box, type:
   ```text
   aabbabba
   ```
3. Click **Simulate** and step through the animation.
4. Click **Explain with XAI** to view the GNN node and edge attribution heatmap.

### Expected Output:
- **NFA, DFA, and Minimized DFA Graphs:** Rendered cleanly in Cytoscape.
- **Simulation Trace:** Shows step-by-step state transitions over `aabbabba` reaching an accepting state.
- **XAI Explanation:** GNNExplainer attribution scores highlighting the transition edges critical to acceptance.

### 🎙️ What to Say:
> *"Finally, we connect ReDoS Guard to the educational core of AutoMind-AI. Here in the Studio, students and researchers can inspect the full NFA, DFA, and Hopcroft minimized DFA for the same pattern, animate step-by-step string simulation, and inspect GNN edge attributions. This bridges formal automata theory with explainable AI in a unified, verified pipeline."*

---

## Summary of Evaluated Key Numbers
- **Exact Analyzer Accuracy on 64-Regex Suite:** **96.88%** (62 / 64).
- **DP Path Counter Cross-Check:** **93.75%** (60 / 64 on suite, 97.27% on 220 random regexes).
- **Sandboxed Benchmark Agreement:** **96.88%** (62 / 64; 22/22 exponential confirmed, 18/20 polynomial confirmed super-linear, 22/22 linear confirmed safe).
- **GNN Held-Out Screening Accuracy:** **85.43%** (95% CI: [83.45%, 87.41%]) across 1,222 test samples with zero family/template overlap.
- **Timing Crossover:** At $|V| \le 18$ states, Exact Analyzer is faster end-to-end (0.337 ms vs 0.357 ms). Empirical crossover at $|V| \approx 18$ states.
- **Equivalence Verification Success on Accepted Repairs:** **100.0%** (22 / 22 verified, 0 false positive repairs).
- **Fuzz Testing:** 2,000+ random strings per accepted repair tested against `re.fullmatch` with zero discrepancies.

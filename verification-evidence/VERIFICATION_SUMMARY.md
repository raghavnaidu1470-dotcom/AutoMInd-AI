# AutoMind-AI Verification Evidence Summary

This directory contains standalone, reproducible browser verification artifacts, actual exported image samples (PNG and SVG), and verification logs for the AutoMind-AI application redesign.

---

## 1. Exported Automata Samples (PNG & SVG)

Exports were generated from actual browser canvas rasterization at **3× high-DPI scaling** independently of viewport pan/zoom state. Both formats feature solid blueprint paper background (`#f8fafc`), technical 20px grid, header title bar with state/transition metrics, and crisp JetBrains Mono typography.

| Sample | Formal Regex | Representation | State Count | Transition Count | SVG Dimensions | PNG Dimensions (3×) | File Links |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Simple Automaton** | `(a|b)*abb` | Minimized DFA | **4 states** (`q0`–`q3`) | **8 transitions** | 781 × 516 px | **2343 × 1548 px** (222 KB) | [SVG](file:///Users/raghavnaidu/AutoMind-AI/verification-evidence/export_simple_automaton.svg) · [PNG](file:///Users/raghavnaidu/AutoMind-AI/verification-evidence/export_simple_automaton.png) |
| **Large Automaton** | `(state_alpha\|state_beta)*sync(x\|y)*` | Minimized DFA | **17 states** (`q0`–`q16`) | **35 transitions** (merged parallel edges + self-loops) | 1813 × 1164 px | **5439 × 3492 px** (1.48 MB) | [SVG](file:///Users/raghavnaidu/AutoMind-AI/verification-evidence/export_large_automaton.svg) · [PNG](file:///Users/raghavnaidu/AutoMind-AI/verification-evidence/export_large_automaton.png) |

### Visual Inspection Findings:
- **Clipping:** Zero clipping observed. All self-loops (e.g. on `q0`, `q1`, `q8`), start arrows, double circles on accepting states, and long multi-symbol edge labels (`_, a, b, c, e, h, l, n, p, s, t, x, y`) remain strictly inside layout bounds.
- **Readability:** Edge labels are placed in dedicated rounded pill badges (`#ffffff` ground, `#cbd5e1` outline) avoiding line clutter; font rendered with sharp subpixel antialiasing.
- **Background:** Solid paper background `#f8fafc` fills the entire canvas canvas, ensuring clean contrast and eliminating transparent background issues.
- **Zoom/Pan Independence:** Verified by testing with active viewport transformation (`translate(195px, -85px) scale(2.35)` on simple, and `translate(-240px, 120px) scale(0.65)` on large). The export functions strip interactive transforms and recompute the canvas around natural graph dimensions, producing identical centered exports regardless of interactive manipulation.

---

## 2. Browser Screenshots (5 Required User Flows)

1. **[Screenshot 1: Main Beginner Workspace](file:///Users/raghavnaidu/AutoMind-AI/verification-evidence/screenshot_1_main_beginner_workspace.png)** (134 KB)
   - Verified default regex `(a|b)*abb`, plain-English description, interactive syntax tokens, and "Walk me through this" action button.
2. **[Screenshot 2: NFA Multi-State Simulation](file:///Users/raghavnaidu/AutoMind-AI/verification-evidence/screenshot_2_nfa_multi_state_simulation.png)** (140 KB)
   - Verified active state subset tracking `{q0, q1, q2}` and multi-path trace visualization.
3. **[Screenshot 3: Hopcroft Minimization Comparison](file:///Users/raghavnaidu/AutoMind-AI/verification-evidence/screenshot_3_minimization_comparison.png)** (192 KB)
   - Verified side-by-side state reduction metrics, equivalence partition table, and algorithm step walkthrough.
4. **[Screenshot 4: ReDoS Analysis & Presets](file:///Users/raghavnaidu/AutoMind-AI/verification-evidence/screenshot_4_redos_analysis_presets.png)** (130 KB)
   - Verified 5 vulnerability archetypes, polynomial vs. exponential danger badges, bounded testing safeguards, and safe alternative suggestions.
5. **[Screenshot 5: Mobile Layout (390×844px)](file:///Users/raghavnaidu/AutoMind-AI/verification-evidence/screenshot_5_mobile_layout.png)** (201 KB)
   - Verified collapsible drawer navigation, vertical stage stack, and touch-friendly controls.

---

## 3. Panel Reopening & Modal Focus Trap Verification

Verified via automated Chrome DevTools Protocol (`scratch_verify_gaps.mjs`):

- **Repeated Panel Reopening:**
  - **Navigation Rail:** 3 consecutive close $\to$ reopen cycles verified (`#btn-close-rail` and `#btn-persistent-open-rail`).
  - **Inspector Column (Margin Column):** 3 consecutive close $\to$ reopen cycles verified (`#btn-close-margin-column` and `#btn-persistent-open-sidebar`).
- **Modal Keyboard Focus Trap & Restoration:**
  - **Walk Me Through Modal:** Tab wraps from last element to first element; Shift+Tab wraps from first element to last element. Dismissal via `Escape` cleanly returns focus to `#btn-walk-me-through`.
  - **Supported Syntax Modal (`RegexExplainer`):** Focus remains trapped inside modal card; dismissal via `Escape` restores focus to `#btn-syntax-reference`.
  - **Hopcroft Minimization Modal:** Focus remains trapped inside modal card; dismissal via `Escape` restores focus to `#btn-minimization-diff`.

---

## 4. Theory of Computation Precision Corrections

- **Backreferences & Non-Regularity:** Corrected misconception claiming $\{ww \mid w \in \Sigma^*\}$ is NP-complete.
  - **Actual Property:** $\{ww \mid w \in \Sigma^*\}$ is a classic non-regular (and non-context-free) language when $|\Sigma| \ge 2$, requiring unbounded memory to compare repeated substrings.
  - **String Check Complexity:** Deciding whether a given string $s$ consists of two identical halves is straightforward and deterministic in $O(|s|)$ linear time.
  - **Distinction from General Regex Matching:** The general decision problem of matching an arbitrary regular expression with backreferences against an arbitrary target string is NP-complete. These two concepts are now clearly separated across `frontend/src/components/RegexExplainer.jsx`, `frontend/src/utils/regexExplainer.js`, and unit test assertions in `frontend/tests/requirements.test.js`.

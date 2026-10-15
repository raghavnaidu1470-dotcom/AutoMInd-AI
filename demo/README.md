# AutoMind AI — Automated Live Demonstration Suite

> **Comprehensive Browser-Driven Theory of Computation Demonstration & Verification System**

This suite executes an automated live demonstration of the complete AutoMind AI platform inside a visible browser window (Google Chrome on macOS). It exercises every implemented feature, validates formal language theory invariants, verifies ReDoS screening, and tests real vector SVG, PNG, and JSON downloads.

---

## 🚀 Quick Start

Ensure Node.js 18+ and Python 3.9+ are available.

```bash
# 1. Run complete visible live demonstration in headed Google Chrome:
npm run demo

# 2. Run fast headless assertion verification mode (skips pacing pauses):
npm run demo:fast

# 3. Run complete headed demo and record high-resolution session video:
npm run demo:record

# 4. Run an individual chapter (e.g. Chapter 8: ReDoS Studio):
node demo/run_live_demo.js --chapter 8

# 5. Run demo at custom presentation pace (e.g. 1.5x speed):
node demo/run_live_demo.js --speed 1.5
```

The script automatically detects if the FastAPI backend and Vite frontend are already running. If not, it launches them automatically using the project's native commands and terminates only the processes it spawned upon exit.

---

## 🎬 Live Presentation Overlay & Controls

During headed demonstration, a presentation caption overlay appears at the top-right corner of the browser:
- **Chapter Badge & Step Title:** Explains current topic and step number.
- **Current Action:** Summarizes what the automated operator is doing on screen.
- **Expected Result:** Explains the formal theory or UI invariant being asserted.
- **Interactive Controls:**
  - `[⏸ Pause]` / `[▶ Resume]` button: Pause the demonstration at any moment to inspect the interface.
  - Keyboard shortcut **`P`**: Toggles pause/resume directly from the keyboard.
  - Speed readout: Displays active pacing multiplier.

---

## 📚 Demonstration Chapters

| # | Chapter Name | Key Features & Invariants Demonstrated |
| :---: | :--- | :--- |
| **1** | **Initial Workspace** | Clean application shell, live FastAPI backend health status readout (`Engine: connected`), default pattern `(a|b)*abb` and candidate string `ababb`, canonical 4-state Minimized DFA. |
| **2** | **Walkthrough & Syntax** | 6-step educational walkthrough (Regex, Thompson NFA, Subset DFA, Hopcroft Minimization, Tape Simulator, ReDoS Immunity), keyboard Escape dismissal, Formal Syntax Guide modal, regular language limits. |
| **3** | **View Modes & Explainer** | Beginner vs Advanced mode switching, plain-English regular expression narrative generation, interactive parsed AST token chips with hover and click role inspection. |
| **4** | **Candidates & Presets** | Synthesized test candidates partitioned into Accepted, Rejected, and Edge cases, hover reason callouts, one-click tape loading, `Show more`/`Show fewer`, `+ Generate more`, standard presets dropdown, and history recall. |
| **5** | **Automata Models** | Switching across NFA (Thompson, 11 states), DFA (Subset, 4 states), and Minimized DFA (Hopcroft, 4 states). Hover subset pills, click state-inspector drawer, Hopcroft comparison modal with state partition table, accessible transition table view. |
| **6** | **Canvas Interactions** | Zoom In (+), Zoom Out (−), Fit view centering, mouse drag canvas panning, transform matrix stability, technical 20px plotting grid ground. |
| **7** | **Tape & Playback** | Pinned tape transport bar, rectangular tape cells, amber read head, Next/Back/Reset/Last controls, scrubber range slider, speed selector, automated play loop, green-bar trace table row jumps, GNN edge weight toggles, rejection by missing transition vs rejection by non-accepting state, NFA branching sets. |
| **8** | **ReDoS Studio** | Static cycle analysis vs runtime backtracking benchmarks, safe linear baseline `(a|b)*abb`, exponential archetype `(a+)+$`, offending span localization, attack string synthesis with Copy feedback, SVG scaling chart with Logarithmic scale toggle, safe alternative `a+$` with DFA isomorphism verification, educational presets catalog with benign matches and bounded Web Worker cancellation (`worker.terminate()`). |
| **9** | **Sidebars & Mobile** | Collapsing and reopening left StageRail via persistent button, collapsing and reopening right margin column via toolbar and `Alt+S` shortcut, keyboard shortcut suppression inside input fields, mobile responsive viewport (<800px) adaptation. |
| **10** | **File Exports** | Triggering real downloads for SVG, PNG, and JSON for simple and larger graphs (`(01)*101`), verifying unclipped viewBox under pan/zoom, 3x high-DPI retina PNG canvas rasterization, opening downloaded SVG directly in the browser. |
| **11** | **Matrix & Robustness** | Independently checked test matrix covering literals, concatenation, alternation, repetition (star/plus/opt), character classes, escapes, empty-string acceptance/rejection; syntax error character pointers (`^`), mid-playback edits, long inputs, characters outside alphabet. |

---

## 📊 Verification Evidence & Artifacts

After execution, all artifacts are saved to `demo/artifacts/`:
- `verification_report.md`: Markdown summary with executive statistics, feature-to-test coverage matrix, and detailed step logs.
- `verification_report.json`: Machine-readable results and timings.
- `downloads/`: Real exported files (`simple_automaton.svg`, `simple_automaton.png`, `simple_automaton.json`, `large_binary_automaton.svg`, etc.).
- `recordings/`: High-resolution WebM session recording (when `--record` is enabled).
- `*.png`: Milestone screenshots captured across major chapters.

---

## 🛠️ CLI Options Reference

```
Options:
  --headed              Run in visible browser window (default: true)
  --headless            Run without GUI window
  --fast                Fastest verification mode (headless, no presentation pauses)
  --speed <num>         Pacing speed multiplier (e.g. 0.5, 1.0, 2.0; default: 1.0)
  --chapter <name|num>  Run specific chapter (1-11, or 'workspace', 'redos', etc.)
  --record              Record entire browser session to WebM video in artifacts/
  --out-dir <path>      Output directory for screenshots, reports, and downloads
  --no-server-start     Do not start backend or frontend (assumes already running)
  --help, -h            Show CLI help message
```

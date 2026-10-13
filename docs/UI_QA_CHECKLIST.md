# AutoMind-AI UI & UX Manual QA Checklist

> **Note on Automated Browser Tooling:** During test execution, automated browser tooling failed to launch because the sandbox environment lacks Playwright driver binaries (`404 Not Found` downloading Playwright driver from Azure CDN). Consequently, this manual QA checklist documents every verification step for human visual and functional verification.

---

## 1. Quick Start

Start both services in separate terminals:

```bash
# Terminal 1: Backend API (FastAPI)
cd /Users/raghavnaidu/AutoMind-AI
./backend/venv/bin/python -m uvicorn backend.api.main:app --port 8000

# Terminal 2: Frontend (Vite)
cd /Users/raghavnaidu/AutoMind-AI/frontend
npm run dev
```

Open your browser to: **`http://localhost:5173`**

---

## 2. Visual Direction & Aesthetic Integrity

| # | Inspection Item | Expected Behavior | Pass/Fail |
|---|----------------|-------------------|:---------:|
| 2.1 | **Color Palette** | Cool off-white paper background (`#f8f9fa`), slate ink text (`#1e293b`), signal amber accents (`#d97706`), muted green accept (`#15803d`), brick red risk (`#b91c1c`), and green-bar tint (`#edf7ed`). **No** purple, **no** neon cyan, **no** glowing gradients, **no** dark theme. | [ ] |
| 2.2 | **Typography** | UI chrome, headings, explanations, and buttons render in `Atkinson Hyperlegible`. Only real code tokens (regular expressions, candidate strings, tape cells, state IDs) render in `JetBrains Mono`. Zero CDN network requests in Network tab. | [ ] |
| 2.3 | **Shapes & Chrome** | Ruled 1px borders, square tape cells (`border-radius: 2px`), round automaton states. **No** uniform rounded glassmorphic cards with blur or drop shadows. | [ ] |
| 2.4 | **Reduced Motion** | Enable OS "Reduce motion" preference: animations and transitions immediately deactivate. | [ ] |

---

## 3. Top Command Bar & Live Syntax Validation

| # | Inspection Item | Expected Behavior | Pass/Fail |
|---|----------------|-------------------|:---------:|
| 3.1 | **Command Bar Layout** | Thin single row at the top containing Regex input, String input, "Run string" button, quiet Examples dropdown, and Recent history dropdown. | [ ] |
| 3.2 | **Enter Key Execution** | Pressing `Enter` in either the regex or string input triggers pipeline execution. | [ ] |
| 3.3 | **Standard Examples Dropdown** | Selecting an example (e.g. `Ends in abb: (a|b)*abb`) populates the fields and automatically triggers simulation. | [ ] |
| 3.4 | **Syntax Error Highlighting** | Type an invalid regex such as `(a|b` or `a**`: <br>• The input field displays a red border.<br>• An error alert shows the exact character position and character marker (`^`).<br>• Plain language advice explains what went wrong and how to fix it (e.g. "Add a closing parenthesis ')' to match the opening '(' at position 0."). | [ ] |

---

## 4. Sequential Stage Rail (Left Rail)

| # | Inspection Item | Expected Behavior | Pass/Fail |
|---|----------------|-------------------|:---------:|
| 4.1 | **Ordered Pipeline Stages** | Displays strictly ordered numbered stages: `1. Regex`, `2. NFA`, `3. DFA`, `4. Minimized DFA`, `5. Run`, `6. ReDoS check`. | [ ] |
| 4.2 | **State Counts** | Shows accurate state counts on relevant stages (e.g. `11 states` on NFA, `4 states` on DFA). | [ ] |
| 4.3 | **Stage Switching** | Clicking a stage updates the drawing area to display that automaton or view. | [ ] |

---

## 5. Drawing Canvas & Railway Schematic

| # | Inspection Item | Expected Behavior | Pass/Fail |
|---|----------------|-------------------|:---------:|
| 5.1 | **Plotting Grid** | Clean drawing area featuring a faint 20px technical plotting grid. | [ ] |
| 5.2 | **Left-to-Right Layered Layout** | States are laid out hierarchically from left to right using Dagre layout. Transitions are smooth curved paths. | [ ] |
| 5.3 | **Merged Parallel Transitions** | Multiple transitions between the same two states are merged into a single edge with a combined label (e.g. `a, b`). | [ ] |
| 5.4 | **Self-Loops** | Self-transitions render as tidy loops above the state node with a clean label box. | [ ] |
| 5.5 | **Start & Accepting Markers** | Start state has a directed incoming arrow. Accepting states feature a double concentric ring. | [ ] |
| 5.6 | **State Hover Linkage** | In DFA and Minimized DFA views, hovering over a state reveals an inspection tooltip displaying the exact NFA states (or merged DFA states) it originated from. | [ ] |
| 5.7 | **Pan & Zoom Controls** | `Zoom +`, `Zoom -`, and `Fit view` work. Mouse drag pans the canvas, and mouse wheel zooms smoothly. | [ ] |
| 5.8 | **View as Table Toggle** | Clicking `View as table` switches to an accessible tabular list of states and transitions. | [ ] |
| 5.9 | **Export Controls** | `SVG`, `PNG`, and `JSON` buttons download respective files. | [ ] |
| 5.10 | **Large Input Warning** | For automata with ≥60 states, a warning banner appears and simplified fast layout activates without page freezing. | [ ] |

---

## 6. Pinned Tape Transport Bar (Bottom Bar)

| # | Inspection Item | Expected Behavior | Pass/Fail |
|---|----------------|-------------------|:---------:|
| 6.1 | **Tape Cells & Read Head** | Pinned to bottom of viewport. Each input character has a distinct rectangular cell. A signal-amber read head pointer sits above the active character. | [ ] |
| 6.2 | **Playback Controls** | `First (\|<)`, `Back (<)`, `Play/Pause`, `Step (>)`, `Last (>\|)` advance and rewind the tape and diagram state in sync. | [ ] |
| 6.3 | **Keyboard Operation** | Pressing `Space` plays/pauses. `Left Arrow` steps back. `Right Arrow` steps forward (when not focused in text inputs). | [ ] |
| 6.4 | **Scrubber & Speed** | Scrubbing the range slider jumps to any step index. Speed dropdown (0.5×, 1×, 2×, 4×) adjusts playback rate. | [ ] |
| 6.5 | **Consumed Counter & Status** | Status line displays `Step N / Total`, active state set `{q0, ...}`, and count of consumed vs. remaining characters. | [ ] |
| 6.6 | **Plain-Language Verdict** | On completion, displays a plain-language termination verdict (e.g. `Accepted: reached accepting state {q3} after 5 steps.` or `Rejected: no transition for 'x' from {q2}.`). | [ ] |
| 6.7 | **Screen Reader ARIA Live** | Inspect the DOM: `<div class="sr-only" aria-live="polite">` updates with step announcements. | [ ] |

---

## 7. Execution Trace (Green-Bar Printer Paper)

| # | Inspection Item | Expected Behavior | Pass/Fail |
|---|----------------|-------------------|:---------:|
| 7.1 | **Green-Bar Aesthetic** | Trace table features authentic alternating pale green (`#edf7ed`) and white rows with green header. | [ ] |
| 7.2 | **Interactive Row Jump** | Clicking any row in the trace jumps the tape read head and diagram active state directly to that step index. | [ ] |

---

## 8. Explainable AI (GNN) Margin Panel

| # | Inspection Item | Expected Behavior | Pass/Fail |
|---|----------------|-------------------|:---------:|
| 8.1 | **Plain Lead Sentence** | Explanation leads with one plain sentence summarizing model verdict and confidence percentage. | [ ] |
| 8.2 | **Edge Weight Toggle** | Toggling "Show edge weight on diagram" increases the stroke width of critical transitions directly on the canvas. | [ ] |
| 8.3 | **Human-Readable Features** | Structural features are displayed with plain human names (e.g. "Cyclic paths detected" rather than `is_cyclic`). | [ ] |
| 8.4 | **Honest Academic Disclaimer** | States clearly that the GNN is statistical/experimental and that the exact simulator decides acceptance. | [ ] |

---

## 9. ReDoS Guard View

| # | Inspection Item | Expected Behavior | Pass/Fail |
|---|----------------|-------------------|:---------:|
| 9.1 | **Underlined Offending Span** | The regular expression displays in monospace with the offending sub-pattern underlined in brick red. An AST diagnosis callout appears below it. | [ ] |
| 9.2 | **Honest Verdict Wording** | Explicitly distinguishes `Confirmed by measurement (EXPONENTIAL RISK)` from `Structurally ambiguous only`. | [ ] |
| 9.3 | **Attack Synthesizer** | Displays pumpable attack string with prefix, pump, and suffix tokens. "Copy" button provides feedback. | [ ] |
| 9.4 | **Scaling Chart & Log Scale** | Time vs. Input Length SVG chart plots original vs. repaired regex. "Scale: Logarithmic (log₁₀)" toggle transforms the Y-axis. | [ ] |
| 9.5 | **Verified Repair Diff** | Displays diff (`- original` / `+ repaired`) and confirms language equivalence via Minimized DFA isomorphism. | [ ] |
| 9.6 | **Tool Limitations Notice** | Plainly notes that backreferences and lookaround assertions are outside regular language scope. | [ ] |

---

## 10. URL State & Local History

| # | Inspection Item | Expected Behavior | Pass/Fail |
|---|----------------|-------------------|:---------:|
| 10.1 | **Shareable State Link** | Changing regex, string, stage, or step updates URL parameters: `?regex=...&string=...&stage=...&step=...`. Copying and pasting the URL in an incognito window reproduces the exact view. | [ ] |
| 10.2 | **Recent History** | The "Recent" dropdown preserves the last 10 tested patterns in `localStorage`. | [ ] |

---

## 11. Mobile Responsiveness (< 800px)

| # | Inspection Item | Expected Behavior | Pass/Fail |
|---|----------------|-------------------|:---------:|
| 11.1 | **Viewport Scaling** | Resize browser to 375px wide (iPhone width). | [ ] |
| 11.2 | **Stage Rail Adaptation** | The left rail converts to a horizontal scrolling stage strip at the top. | [ ] |
| 11.3 | **Pinned Tape Bar** | The tape transport bar remains pinned to the bottom of the viewport. | [ ] |
| 11.4 | **Touch & Pan** | Canvas fills the viewport and allows smooth touch drag and pinch zoom. | [ ] |

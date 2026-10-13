# AutoMind-AI Frontend Design Specification

## 1. Subject and Concept: "Tape and Track"

**Audience:** Students, educators, and software engineers learning formal language theory, automata construction, and the mechanics of Regular Expression Denial of Service (ReDoS).

**Primary Job:** Enable a user to enter a regular expression and an input string, watch the automaton mechanically step through the input tape cell by cell, and understand the formal verdict and computational complexity.

**Metaphor:**
- **The Track:** The automaton diagram is rendered like a clean railway schematic or technical engineering blueprint: crisp lines, curved tracks, merged parallel transitions, unambiguous start markers, and double rings for accepting states.
- **The Tape:** Pinned to the bottom of the viewport is a physical-feeling mechanical tape transport with distinct rectangular cells, a prominent signal-amber read head pointer, scrubber, step controls, and an explicit live status readout.
- **The Trace:** An authentic green-bar continuous-form printer paper log linking every character transition to its source and target states.
- **The Chrome:** Quiet, disciplined, ruled lines with high whitespace discipline. Chrome steps out of the way so cognitive attention remains entirely on the tape and track.

---

## 2. Color Tokens

A tight, disciplined palette inspired by technical blueprints and high-contrast paper documents. We define exactly 6 core semantic color tokens:

| Token Name | Hex Value | Role & Usage |
| :--- | :--- | :--- |
| `--paper-bg` | `#f8f9fa` | Off-white paper background for the workspace, canvas, and layout chrome. |
| `--ink-slate` | `#1e293b` | Primary text, state borders, transition strokes, and technical line art. High contrast (11:1 on paper). |
| `--amber-signal` | `#d97706` | Active state indicator, read head marker on tape, scrubber thumb, and traversal edges. |
| `--green-accept` | `#15803d` | Accepting states, accepted run verdicts, linear-time confirmation, verified repairs. |
| `--red-risk` | `#b91c1c` | Exponential ReDoS risk, rejected run verdicts, syntax error markers, failed states. |
| `--greenbar-tint` | `#edf7ed` | Pale green-bar alternating row background for the execution trace log. |

### Supporting Tone Tokens (Shades of Slate & Paper)
- `--paper-panel`: `#ffffff` (Clean white for distinct panel grounds)
- `--ink-secondary`: `#475569` (Secondary labels, metadata, captions, inactive controls)
- `--ink-border`: `#cbd5e1` (1px technical ruled lines and dividers)
- `--amber-tint`: `#fef3c7` (Subtle amber highlight for active tape cell)
- `--red-hatch`: `repeating-linear-gradient(45deg, #fee2e2, #fee2e2 4px, #fecaca 4px, #fecaca 8px)` (Non-color hatch for risk)

**Strict Color Prohibitions:**
- No purple or neon cyan accents.
- No gradient washes or glowing drop-shadows.
- No glassmorphism, blur backdrops, or faux frosted glass.
- No near-black background (`#070913`).

---

## 3. Typography & Type Roles

Fonts are self-hosted via `@fontsource` packages to guarantee offline privacy, determinism, and zero CDN dependencies.

1. **Interface Type:** `Atkinson Hyperlegible` (`@fontsource/atkinson-hyperlegible`)
   - Purpose: Designed specifically by the Braille Institute to maximize character distinction (e.g. differentiating `I`, `l`, `1`, and `O`, `0`).
   - Roles: Command bar controls, stage rail labels, buttons, diagram inspector text, natural language explanations, ReDoS diagnoses, accessibility descriptions.
   - Body line limit: Strictly constrained to `< 80` characters for reading comfort.
2. **Code & Machine Content:** `JetBrains Mono` (`@fontsource/jetbrains-mono`)
   - Strict Rule: Monospace is reserved **strictly** for real machine content. It is never used as an aesthetic choice for small labels, dates, or metadata.
   - Roles: The regex input string, candidate input strings, individual tape character cells, automaton state identifiers (`q0`, `q1`), transition symbols (`a`, `b`, `ε`), attack strings, and code diffs.

### Type Scale
- **Headline (h1 / brand):** 1.25rem (20px) / bold / tracking normal
- **Section Title (h2):** 1.05rem (17px) / bold
- **Body Regular:** 0.875rem (14px) / line-height 1.5 / max-width 72ch
- **Body Small / Captions:** 0.75rem (12px) / line-height 1.4
- **Monospace Code:** 0.875rem (14px) / line-height 1.4 / font-feature-settings: "liga" 0

---

## 4. Layout Architecture & ASCII Wireframes

### Desktop Layout (>= 800px)

```
+-------------------------------------------------------------------------------------------------------------+
| AUTO MIND AI                                        [Engine: Connected] [Retry]                             |
+-------------------------------------------------------------------------------------------------------------+
| COMMAND:  Regex: [ (a|b)*abb          ]   String: [ ababb    ]   [ Run string ]   Examples: [ Ends in abb v ]  |
+------------+--------------------------------------------------------------------+--------------------------+
| STAGES     | DIAGRAM AREA (Faint Grid, Pan, Zoom, Fit-to-view, Export SVG/PNG) | MARGIN COLUMN (Conditional)
|            |                                                                    | 
| [x] Regex  |   +------------------------------------------------------------+   | [Callout: q2 -> q3]
| (valid)    |   |                                                            |   | Critical transition:
|            |   |   (->) ((q0)) == 'a' ==> (q1) == 'b' ==> (((q2)))          |   | Consumed 'b' from active
| [x] NFA    |   |           \__ 'b' __/                 (double ring)        |   | set {q1}.
|   (11 sts) |   |                                                            |   |
|            |   |                                                            |   | [Trace Log (Green-Bar)]
| [x] DFA    |   |                                                            |   | #  Ch  State  Next  Trans
|   (4 sts)  |   +------------------------------------------------------------+   | 0  a   q0     q1    q0->q1
|            |                                                                    | 1  b   q1     q2    q1->q2
| [o] Min DFA|   [ Zoom In ] [ Zoom Out ] [ Reset View ] [ Table View ] [ Export ]|   | 
|   (4 sts)  |                                                                    | [Explanation (GNN)]
|            |                                                                    | Exact simulator verified:
| [ ] Run    |                                                                    | Accepted in 5 steps.
|   (step 2) |                                                                    | Edge weight: 89% imp.
|            |                                                                    |
| [ ] ReDoS  |                                                                    | [ReDoS Screening]
|   (Linear) |                                                                    | Linear: No cycle pump.
+------------+--------------------------------------------------------------------+--------------------------+
| TAPE TRANSPORT (Pinned Bottom Bar):                                                                         |
| [ |< First ] [ < Back ] [ > Play ] [ > Step ] [ >| Last ]  [---O-------------]  Speed: [ 1x v ]             |
| Tape: [ a ] [ b ] [ a ] [ b ] [ b ]  (Consumed: 2 / Remaining: 3)                                           |
| Status: Reading 'a' at cell 2 -> transition to {q1, q2}. Stepper active.                                    |
+-------------------------------------------------------------------------------------------------------------+
```

### Mobile Layout (< 800px)

```
+-------------------------------------------------------------------------+
| AUTO MIND AI                                        [Engine: Connected] |
+-------------------------------------------------------------------------+
| Regex: [ (a|b)*abb      ]  String: [ ababb ]  [ Run ]                   |
+-------------------------------------------------------------------------+
| STAGE BAR: [ Regex ] [ NFA (11) ] [ DFA (4) ] [ Min DFA ] [ ReDoS ]     |
+-------------------------------------------------------------------------+
| DIAGRAM VIEW (Full-width, touch pan/zoom)                               |
|                                                                         |
|                (->) (q0) === 'a' ===> ((q1))                            |
|                                                                         |
+-------------------------------------------------------------------------+
| [^ View Trace & Margin Notes (Drawer)]                                  |
+-------------------------------------------------------------------------+
| TAPE PINNED: [ < ] [ > Play ] [ > ]  Tape: [a][b][a][b][b]              |
| Verdict: Reading cell 2                                                 |
+-------------------------------------------------------------------------+
```

---

## 5. Principles & Non-Color Redundant Encodings

1. **Dual Encoding for Every State:**
   - **Accepting States:** Rendered with a definitive SVG double ring (`circle` + concentric outer `circle`), not merely green stroke.
   - **Reject Verdict:** Rendered with struck label (`q3` with strike line) and explicit natural language verdict ("Rejected: no transition for 'x' from q3").
   - **ReDoS Vulnerability:** Rendered with diagonal hatch pattern (`#red-hatch`), explicit textual risk level ("Exponential Risk - Confirmed by measurement"), and detailed complexity label.
   - **Dead / Unreachable States:** Rendered with dashed border (`stroke-dasharray="4 3"`), dimmed opacity (0.45), and text caption.
2. **Structural Clarity through Whitespace & Ruled Lines:**
   - Eliminate card-inside-card nests.
   - Use thin 1px slate rules (`#cbd5e1`) and solid paper backgrounds to establish visual grouping.
3. **Purposeful Motion Only:**
   - The only moving elements are intentional feedback: the tape read head pointer sliding into place, active diagram nodes transitioning border stroke, and the trace row highlight jumping.
   - Full support for `@media (prefers-reduced-motion: reduce)`.
4. **Honest System Status:**
   - Header shows only the product title and an honest engine status indicator: "Connected" or "Backend not reachable [Retry]". No mock badges or fake preview chips.

---

## 6. Critique Against the "Avoid" List

| Avoid List Item | Former Implementation | Redesigned Implementation | Why We Changed It |
| :--- | :--- | :--- | :--- |
| **Identical rounded cards with soft shadows** | Glassmorphic cards with `border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.37)`. | Strict geometric hierarchy: square tape cells (`border-radius: 2px`), circular automaton nodes, clean 1px ruled borders on panels. | Prevents the repetitive generic web-template look; reinforces physical schematic metaphor. |
| **Gradient washes & neon glow** | `radial-gradient(circle at 15% 15%, rgba(139,92,246,0.08)...)` with neon cyan and violet dropshadows. | Solid, cool off-white paper (`#f8f9fa`) with a faint technical 16px plotting grid. Clean slate ink lines. | Eliminates eye strain; mimics engineering graph paper and blueprints. |
| **Tracked all-caps labels above headings** | Uppercase tags like `DECISION SUMMARY`, `KEY TRANSITION PATHS`, `EXPLAINABLE AI ANALYTICS`. | Natural sentence-case typography: "Decision summary", "Key transition paths", "Explainable AI analytics". | Normal case is faster and more comfortable to read, without artificial tech-bro posture. |
| **Numbered 01/02/03 markers on non-sequential content** | Numbered badges on parallel tabs and independent metric boxes. | Numbered indicators *only* on the strictly sequential Stage Rail: `1. Regex`, `2. NFA`, `3. DFA`, `4. Minimized DFA`, `5. Run`, `6. ReDoS check`. | Numbers signify actual execution order in the formal language compiler pipeline. |
| **Meta strings joined with middle dots** | `Confidence: 94% · States: 4 · Time: 12ms`. | Clean tabular layout or separated label/value pairs: `Confidence: 94%`, `States: 4`, `Exact time: 12ms`. | Eliminates cluttered boilerplate punctuation. |
| **"→" at the end of every button** | "Generate & Explain →", "Step ▶", "Repair ➜". | Plain, crisp action verbs: "Run string", "Step forward", "Repair regex", "Export SVG". | Functional UI verbs are unambiguous and screen-reader friendly without extraneous glyphs. |
| **Emoji as icons** | `Ψ`, `🔥`, `⚡`, `🛡️`, `💣`, `🚨`, `📈`. | Minimalist SVG icons with accessible titles and labels, or plain text symbols where appropriate. | Emoji render unpredictably across OS platforms and undermine technical gravitas. |
| **Big-number-with-gradient hero** | Neon cyan `98.4%` confidence display with glowing background bars. | Crisp monospace metrics with high-contrast text (`98.4%`) and honest calibration notes. | Treats academic GNN predictions as statistical models rather than vanity metrics. |
| **Monospace for every small label** | Labels, buttons, badges, and headers rendered in `var(--font-mono)`. | Atkinson Hyperlegible for all UI text, labels, and explanations. Monospace strictly for regular expressions, string tokens, and automaton states. | Restores typographical hierarchy and human readability. |
| **Decorative badges** | "Member A: Automata", "Member B: GNN & XAI", "Member C: API & UI", "NEW" chips. | Clean, honest header with system title and real engine connectivity. | Removes distracting internal project artifact labels. |

---

## 7. Self-Critique of Initial Default Thoughts

1. *Initial impulse:* Keep the dark theme because "automata diagrams look like glowing circuit boards."
   - *Critique:* Glowing dark neon reads as a toy crypto or generic AI dashboard. Formal languages and automata theory were born on paper, blackboards, and punched tape.
   - *Resolution:* Shifted entirely to off-white blueprint paper (`#f8f9fa`), crisp slate lines (`#1e293b`), and amber signal ink (`#d97706`).
2. *Initial impulse:* Put all explanations and ReDoS checks in stacked right-side cards.
   - *Critique:* Stacking identical boxes clutters the screen and squeezes the drawing canvas.
   - *Resolution:* Created a collapsible margin column that appears only when diagnostic or ReDoS findings exist, using thin engineering callout leader lines to connect notes directly to diagram nodes and transitions.
3. *Initial impulse:* Use simple circle-packing coordinates for automata.
   - *Critique:* Automata with >10 states become unreadable spiderwebs without left-to-right layering.
   - *Resolution:* Implemented hierarchical left-to-right layout via `dagre` with bezier curves, merged parallel edges, and self-loops on top.

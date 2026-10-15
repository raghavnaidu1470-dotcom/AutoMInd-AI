import React, { useState, useEffect, useRef } from 'react';

const WALKTHROUGH_STEPS = [
  {
    step: 1,
    title: '1. What is a Regular Expression?',
    concept: 'Formal Language Specification',
    content: (
      <>
        <p>
          A regular expression is a mathematical description of a set of valid strings (a <em>formal language</em>).
        </p>
        <p>
          For example, in <code>(a|b)*abb</code>:
        </p>
        <ul>
          <li><code>(a|b)</code> means choosing either <strong>a</strong> or <strong>b</strong> (alternation).</li>
          <li><code>*</code> is the <strong>Kleene Star</strong>: repeat the choice zero or more times.</li>
          <li><code>abb</code> means the string must conclude with the exact sequence <strong>a-b-b</strong>.</li>
        </ul>
        <p>
          Any string ending in <code>abb</code> (like <code>abb</code>, <code>ababb</code>, <code>babb</code>) belongs to this language.
        </p>
      </>
    ),
  },
  {
    step: 2,
    title: '2. From Regex to NFA (Thompson\'s Construction)',
    concept: 'Nondeterministic Finite Automaton',
    content: (
      <>
        <p>
          Every regular expression is mechanically converted into an <strong>Nondeterministic Finite Automaton (NFA)</strong>.
        </p>
        <div style={{ background: 'var(--paper-subtle)', padding: '0.5rem', borderRadius: '4px', margin: '0.4rem 0' }}>
          <strong>Key NFA Concepts:</strong>
          <ul>
            <li><strong>Start State:</strong> Where the machine begins reading input (marked with a green ▶ arrow).</li>
            <li><strong>Accepting State:</strong> A valid end state (rendered with a concentric <strong>double circle</strong>).</li>
            <li><strong>Epsilon (ε) Transitions:</strong> Instantaneous jumps taken without consuming any character from the string.</li>
            <li><strong>Nondeterminism:</strong> The machine can be in multiple states simultaneously (represented as a set of active states).</li>
          </ul>
        </div>
      </>
    ),
  },
  {
    step: 3,
    title: '3. Determinization (DFA & Subset Construction)',
    concept: 'Deterministic Finite Automaton',
    content: (
      <>
        <p>
          Because computers cannot guess paths, we convert the NFA into a <strong>Deterministic Finite Automaton (DFA)</strong> via Subset Construction.
        </p>
        <ul>
          <li>In a DFA, for every state and every alphabet symbol, there is <strong>exactly one</strong> deterministic outgoing transition.</li>
          <li>There are <strong>zero ε-transitions</strong>.</li>
          <li>Each DFA state corresponds directly to a <strong>subset of NFA states</strong> reachable simultaneously.</li>
        </ul>
        <p>
          For a <strong>fixed compiled DFA</strong>, string matching is strictly <em>linear in input length O(|w|)</em>—reading one character per transition. (Note: constructing a DFA can have worst-case exponential state complexity <em>O(2<sup>|Q|</sup>)</em>).
        </p>
      </>
    ),
  },
  {
    step: 4,
    title: '4. Minimization (Hopcroft\'s Algorithm)',
    concept: 'Optimal Equivalent Automaton',
    content: (
      <>
        <p>
          A DFA may contain redundant states that perform identical tasks. <strong>Hopcroft\'s Algorithm</strong> partitions states into indistinguishable equivalence classes.
        </p>
        <ul>
          <li>States that share identical <strong>right-languages</strong> (yielding identical accept/reject decisions on all future suffixes under the Myhill-Nerode Theorem) are <strong>merged together</strong>.</li>
          <li>The resulting <strong>Minimized DFA</strong> has the provably minimal number of states required to recognize the language.</li>
          <li>By the Myhill-Nerode Theorem, this canonical minimal automaton is <em>unique</em> up to state renaming!</li>
        </ul>
      </>
    ),
  },
  {
    step: 5,
    title: '5. Running Strings on the Tape',
    concept: 'Step-by-Step Simulation',
    content: (
      <>
        <p>
          At the bottom of the screen is the <strong>Tape Transport Bar</strong> evaluating <strong>full-string acceptance</strong> (<em>w ∈ L(r)</em>).
        </p>
        <ul>
          <li>The input string is loaded onto physical tape cells.</li>
          <li>The amber read head advances one character at a time, consuming the candidate string from start to end.</li>
          <li>At each step, the diagram lights up the active state(s) and the traversed transition.</li>
          <li>When all symbols are consumed: if the machine ends in an accepting double-circle state, the string is <strong>Accepted</strong> (<em>w ∈ L(r)</em>); otherwise, it is <strong>Rejected</strong>.</li>
        </ul>
      </>
    ),
  },
  {
    step: 6,
    title: '6. ReDoS & Why Automata are Immune',
    concept: 'Regular Expression Denial of Service',
    content: (
      <>
        <p>
          Many programming languages (JavaScript, Python <code>re</code>, PCRE) evaluate regexes using <strong>backtracking engines</strong> rather than finite automata.
        </p>
        <p>
          When an expression has nested or overlapping quantifiers like <code>(a+)+$</code>, backtracking engines explore up to 2<sup>n</sup> possible match permutations on near-matches (like <code>aaaaaaaaaa!</code>), freezing the application thread!
        </p>
        <div style={{ background: 'var(--green-tint)', border: '1px solid var(--green-accept)', padding: '0.5rem', borderRadius: '4px', margin: '0.4rem 0' }}>
          <strong>The Automata Immunity Guarantee:</strong>
          <br />
          Because compiled DFAs evaluate deterministically in <em>strict linear time O(|w|)</em> without backtracking, they are immune to catastrophic ReDoS execution stalls.
        </div>
      </>
    ),
  },
];

export default function WalkMeThroughModal({ isOpen, onClose }) {
  const [currentStep, setCurrentStep] = useState(0);
  const previouslyFocusedRef = useRef(null);
  const modalCardRef = useRef(null);
  const closeBtnRef = useRef(null);

  // Focus management: capture previous element, trap tab focus, and restore on unmount
  useEffect(() => {
    if (isOpen) {
      previouslyFocusedRef.current = document.activeElement;
      // Focus modal close button
      setTimeout(() => {
        closeBtnRef.current?.focus();
      }, 50);

      const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          onClose();
          return;
        }

        if (e.key === 'Tab') {
          const modalEl = modalCardRef.current;
          if (!modalEl) return;
          const focusables = Array.from(
            modalEl.querySelectorAll(
              'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
            )
          );
          if (focusables.length === 0) return;
          const first = focusables[0];
          const last = focusables[focusables.length - 1];
          if (e.shiftKey) {
            if (document.activeElement === first || !modalEl.contains(document.activeElement)) {
              e.preventDefault();
              last.focus();
            }
          } else {
            if (document.activeElement === last || !modalEl.contains(document.activeElement)) {
              e.preventDefault();
              first.focus();
            }
          }
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => {
        window.removeEventListener('keydown', handleKeyDown);
        if (previouslyFocusedRef.current && previouslyFocusedRef.current.focus) {
          previouslyFocusedRef.current.focus();
        }
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const stepData = WALKTHROUGH_STEPS[currentStep];
  const isFirst = currentStep === 0;
  const isLast = currentStep === WALKTHROUGH_STEPS.length - 1;

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Walk me through AutoMind AI"
      onClick={(e) => {
        if (e.target.classList.contains('modal-backdrop')) onClose();
      }}
    >
      <div className="modal-card" ref={modalCardRef} style={{ maxWidth: '620px' }}>
        <div className="modal-header">
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--amber-signal)', fontWeight: 700 }}>
              Guided Tutorial · {stepData.concept}
            </div>
            <h3 style={{ margin: '0.2rem 0 0 0', fontSize: 'var(--text-md)' }}>
              {stepData.title}
            </h3>
          </div>
          <button
            ref={closeBtnRef}
            type="button"
            className="btn-quiet"
            onClick={onClose}
            aria-label="Close walkthrough"
          >
            ✕
          </button>
        </div>

        <div className="modal-body" style={{ minHeight: '260px' }}>
          {stepData.content}
        </div>

        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-secondary)' }}>
            Step {currentStep + 1} of {WALKTHROUGH_STEPS.length}
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              className="btn-quiet"
              onClick={() => setCurrentStep((s) => Math.max(0, s - 1))}
              disabled={isFirst}
            >
              ◀ Previous
            </button>

            {isLast ? (
              <button
                type="button"
                className="btn-run"
                onClick={onClose}
              >
                Ready to Explore!
              </button>
            ) : (
              <button
                type="button"
                className="btn-run"
                onClick={() => setCurrentStep((s) => Math.min(WALKTHROUGH_STEPS.length - 1, s + 1))}
              >
                Next Step ▶
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

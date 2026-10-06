"""
Synthetic Automaton and Trace Generator
=======================================
Owned by: Member B (GNN + Explainable AI Module)

Generates synthetic finite automata conforming strictly to `docs/json_schema.md`
paired with labeled candidate strings (accepted / rejected) and their
step-by-step simulation traces.

Supports:
  - Diverse state counts (2 to 10 states)
  - Varied alphabets (['a', 'b'], ['0', '1'], ['a', 'b', 'c'], ['0', '1', '2'])
  - Accepting state distributions & transition densities
  - Structured formal language families:
      * Substring suffix matching (e.g., ends with "abb", "01")
      * Substring prefix matching (e.g., starts with "ab", "101")
      * Substring containment (e.g., contains "11", "aba")
      * Parity / counting (e.g., even number of 'a's, odd count)
      * Modulo length (e.g., length % 2 == 0, length % 3 == 0)
      * Random valid reachable DFAs
  - Balanced string generation & simulation trace generation
"""

import random
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import deque


class SyntheticAutomataGenerator:
    """
    Generator creating varied synthetic automata and labeled simulation traces
    for training and evaluating GNN classifiers and explainability modules.
    """

    DEFAULT_ALPHABETS = [
        ["a", "b"],
        ["0", "1"],
        ["a", "b", "c"],
        ["0", "1", "2"],
    ]

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    # -------------------------------------------------------------------------
    # Structured Automata Generators
    # -------------------------------------------------------------------------

    def generate_ends_with_dfa(self, pattern: str, alphabet: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Builds a minimal DFA recognizing strings ending in `pattern`.
        Uses KMP-style failure function transitions.
        """
        alphabet = sorted(list(set(alphabet or ["a", "b"])))
        for ch in pattern:
            if ch not in alphabet:
                alphabet.append(ch)
        alphabet.sort()

        m = len(pattern)
        num_states = m + 1
        states = []
        for i in range(num_states):
            states.append({
                "id": f"q{i}",
                "label": f"q{i}" + (f" (saw {pattern[:i]})" if i > 0 else " (start)"),
                "is_start": (i == 0),
                "is_accepting": (i == m),
                "metadata": {"matched_prefix_len": i},
            })

        transitions = []
        t_id = 0
        for i in range(num_states):
            current_prefix = pattern[:i]
            for sym in alphabet:
                candidate = current_prefix + sym
                # Find longest proper prefix of pattern that is a suffix of candidate
                next_state_idx = 0
                for k in range(min(len(candidate), m), 0, -1):
                    if candidate.endswith(pattern[:k]):
                        next_state_idx = k
                        break
                transitions.append({
                    "id": f"t_{t_id}",
                    "from_state": f"q{i}",
                    "to_state": f"q{next_state_idx}",
                    "symbol": sym,
                })
                t_id += 1

        auto_id = f"dfa_ends_with_{pattern}_{uuid.uuid4().hex[:6]}"
        return {
            "id": auto_id,
            "name": f"DFA: Ends with '{pattern}'",
            "type": "DFA",
            "alphabet": alphabet,
            "start_state": "q0",
            "states": states,
            "transitions": transitions,
            "metadata": {
                "regex": f"({ '|'.join(alphabet) })*{pattern}",
                "state_count": num_states,
                "transition_count": len(transitions),
                "is_minimized": True,
                "family": "ends_with",
                "pattern": pattern,
            },
        }

    def generate_starts_with_dfa(self, prefix: str, alphabet: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Builds a DFA recognizing strings starting with `prefix`.
        States: q0..qm (matching prefix) and q_trap (trap/dead state).
        """
        alphabet = sorted(list(set(alphabet or ["a", "b"])))
        for ch in prefix:
            if ch not in alphabet:
                alphabet.append(ch)
        alphabet.sort()

        m = len(prefix)
        states = []
        for i in range(m + 1):
            states.append({
                "id": f"q{i}",
                "label": f"q{i}" + (" (matched)" if i == m else ""),
                "is_start": (i == 0),
                "is_accepting": (i == m),
                "metadata": {},
            })
        states.append({
            "id": "q_trap",
            "label": "q_trap",
            "is_start": False,
            "is_accepting": False,
            "metadata": {},
        })

        transitions = []
        t_id = 0
        for i in range(m):
            expected_sym = prefix[i]
            for sym in alphabet:
                to_state = f"q{i+1}" if sym == expected_sym else "q_trap"
                transitions.append({
                    "id": f"t_{t_id}",
                    "from_state": f"q{i}",
                    "to_state": to_state,
                    "symbol": sym,
                })
                t_id += 1

        # Accepting state loops on all alphabet symbols
        for sym in alphabet:
            transitions.append({
                "id": f"t_{t_id}",
                "from_state": f"q{m}",
                "to_state": f"q{m}",
                "symbol": sym,
            })
            t_id += 1

        # Trap state loops on all alphabet symbols
        for sym in alphabet:
            transitions.append({
                "id": f"t_{t_id}",
                "from_state": "q_trap",
                "to_state": "q_trap",
                "symbol": sym,
            })
            t_id += 1

        auto_id = f"dfa_starts_with_{prefix}_{uuid.uuid4().hex[:6]}"
        return {
            "id": auto_id,
            "name": f"DFA: Starts with '{prefix}'",
            "type": "DFA",
            "alphabet": alphabet,
            "start_state": "q0",
            "states": states,
            "transitions": transitions,
            "metadata": {
                "regex": f"{prefix}({ '|'.join(alphabet) })*",
                "state_count": len(states),
                "transition_count": len(transitions),
                "is_minimized": True,
                "family": "starts_with",
                "pattern": prefix,
            },
        }

    def generate_contains_dfa(self, pattern: str, alphabet: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Builds a DFA recognizing strings containing substring `pattern`.
        """
        alphabet = sorted(list(set(alphabet or ["a", "b"])))
        for ch in pattern:
            if ch not in alphabet:
                alphabet.append(ch)
        alphabet.sort()

        m = len(pattern)
        num_states = m + 1
        states = []
        for i in range(num_states):
            states.append({
                "id": f"q{i}",
                "label": f"q{i}" + (" (contains)" if i == m else ""),
                "is_start": (i == 0),
                "is_accepting": (i == m),
                "metadata": {},
            })

        transitions = []
        t_id = 0
        for i in range(m):
            curr_pref = pattern[:i]
            for sym in alphabet:
                cand = curr_pref + sym
                next_k = 0
                for k in range(min(len(cand), m), 0, -1):
                    if cand.endswith(pattern[:k]):
                        next_k = k
                        break
                transitions.append({
                    "id": f"t_{t_id}",
                    "from_state": f"q{i}",
                    "to_state": f"q{next_k}",
                    "symbol": sym,
                })
                t_id += 1

        # Final state stays in q_m
        for sym in alphabet:
            transitions.append({
                "id": f"t_{t_id}",
                "from_state": f"q{m}",
                "to_state": f"q{m}",
                "symbol": sym,
            })
            t_id += 1

        auto_id = f"dfa_contains_{pattern}_{uuid.uuid4().hex[:6]}"
        return {
            "id": auto_id,
            "name": f"DFA: Contains '{pattern}'",
            "type": "DFA",
            "alphabet": alphabet,
            "start_state": "q0",
            "states": states,
            "transitions": transitions,
            "metadata": {
                "regex": f"({ '|'.join(alphabet) })*{pattern}({ '|'.join(alphabet) })*",
                "state_count": num_states,
                "transition_count": len(transitions),
                "is_minimized": True,
                "family": "contains",
                "pattern": pattern,
            },
        }

    def generate_parity_dfa(self, target_symbol: str, alphabet: Optional[List[str]] = None, even: bool = True) -> Dict[str, Any]:
        """
        Builds a 2-state DFA tracking even/odd count of `target_symbol`.
        """
        alphabet = sorted(list(set(alphabet or ["a", "b"])))
        if target_symbol not in alphabet:
            alphabet.append(target_symbol)
            alphabet.sort()

        states = [
            {"id": "q0", "label": "q0 (Even)", "is_start": True, "is_accepting": even, "metadata": {}},
            {"id": "q1", "label": "q1 (Odd)", "is_start": False, "is_accepting": not even, "metadata": {}},
        ]

        transitions = []
        t_id = 0
        for s_idx, sid in enumerate(["q0", "q1"]):
            other_sid = "q1" if sid == "q0" else "q0"
            for sym in alphabet:
                to_state = other_sid if sym == target_symbol else sid
                transitions.append({
                    "id": f"t_{t_id}",
                    "from_state": sid,
                    "to_state": to_state,
                    "symbol": sym,
                })
                t_id += 1

        mode_str = "even" if even else "odd"
        auto_id = f"dfa_parity_{target_symbol}_{mode_str}_{uuid.uuid4().hex[:6]}"
        return {
            "id": auto_id,
            "name": f"DFA: {mode_str.capitalize()} count of '{target_symbol}'",
            "type": "DFA",
            "alphabet": alphabet,
            "start_state": "q0",
            "states": states,
            "transitions": transitions,
            "metadata": {
                "regex": f"({target_symbol}{target_symbol})*" if even else f"{target_symbol}({target_symbol}{target_symbol})*",
                "state_count": 2,
                "transition_count": len(transitions),
                "is_minimized": True,
                "family": "parity",
            },
        }

    def generate_modulo_length_dfa(self, mod: int = 3, alphabet: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Builds a DFA where acceptance requires string length % mod == 0.
        """
        alphabet = sorted(list(set(alphabet or ["a", "b"])))
        states = []
        for i in range(mod):
            states.append({
                "id": f"q{i}",
                "label": f"q{i} (len%{mod}={i})",
                "is_start": (i == 0),
                "is_accepting": (i == 0),
                "metadata": {},
            })

        transitions = []
        t_id = 0
        for i in range(mod):
            nxt = (i + 1) % mod
            for sym in alphabet:
                transitions.append({
                    "id": f"t_{t_id}",
                    "from_state": f"q{i}",
                    "to_state": f"q{nxt}",
                    "symbol": sym,
                })
                t_id += 1

        auto_id = f"dfa_mod_{mod}_{uuid.uuid4().hex[:6]}"
        return {
            "id": auto_id,
            "name": f"DFA: String length mod {mod} == 0",
            "type": "DFA",
            "alphabet": alphabet,
            "start_state": "q0",
            "states": states,
            "transitions": transitions,
            "metadata": {
                "state_count": mod,
                "transition_count": len(transitions),
                "is_minimized": True,
                "family": "modulo_length",
            },
        }

    def generate_random_dfa(
        self,
        num_states: int = 4,
        alphabet: Optional[List[str]] = None,
        accepting_ratio: float = 0.35,
        density: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Builds a valid, connected random DFA with reachable states.
        """
        alphabet = sorted(list(set(alphabet or ["a", "b"])))
        state_ids = [f"q{i}" for i in range(num_states)]

        # Guarantee at least one accepting state (not start, unless 1 state) and at least one non-accepting
        num_accepting = max(1, min(num_states - 1, int(round(num_states * accepting_ratio))))
        accepting_pool = state_ids[1:] if num_states > 1 else state_ids
        accepting_states = set(random.sample(accepting_pool, min(num_accepting, len(accepting_pool))))

        states = []
        for sid in state_ids:
            states.append({
                "id": sid,
                "label": sid,
                "is_start": (sid == "q0"),
                "is_accepting": (sid in accepting_states),
                "metadata": {},
            })

        # Ensure reachability: create a random spanning tree from q0
        unvisited = set(state_ids[1:])
        visited = ["q0"]
        transitions = []
        t_id = 0
        assigned_edges: Set[Tuple[str, str]] = set()

        while unvisited:
            src = random.choice(visited)
            dst = random.choice(list(unvisited))
            sym = random.choice(alphabet)
            transitions.append({
                "id": f"t_{t_id}",
                "from_state": src,
                "to_state": dst,
                "symbol": sym,
            })
            assigned_edges.add((src, sym))
            t_id += 1
            visited.append(dst)
            unvisited.remove(dst)

        # Complete transitions for each state x symbol according to density
        for sid in state_ids:
            for sym in alphabet:
                if (sid, sym) in assigned_edges:
                    continue
                if random.random() <= density:
                    dst = random.choice(state_ids)
                    transitions.append({
                        "id": f"t_{t_id}",
                        "from_state": sid,
                        "to_state": dst,
                        "symbol": sym,
                    })
                    t_id += 1

        auto_id = f"dfa_random_{num_states}st_{uuid.uuid4().hex[:6]}"
        return {
            "id": auto_id,
            "name": f"Random DFA ({num_states} states)",
            "type": "DFA",
            "alphabet": alphabet,
            "start_state": "q0",
            "states": states,
            "transitions": transitions,
            "metadata": {
                "state_count": len(states),
                "transition_count": len(transitions),
                "is_minimized": False,
                "family": "random",
            },
        }

    # -------------------------------------------------------------------------
    # Simulation & Trace Execution
    # -------------------------------------------------------------------------

    def simulate_string(self, automaton: Dict[str, Any], input_string: str) -> Dict[str, Any]:
        """
        Simulates candidate string execution against an automaton dict.
        Returns a SimulationResult dict conforming to `docs/json_schema.md`.
        """
        start_time = time.time()
        start_state = automaton.get("start_state", "q0")
        states = automaton.get("states", [])
        transitions = automaton.get("transitions", [])
        accepting_ids = {s["id"] for s in states if s.get("is_accepting", False)}

        # Build transition map: (from_state, symbol) -> Transition dict
        trans_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for t in transitions:
            key = (t["from_state"], t["symbol"])
            # In DFA there is at most one, in NFA pick first deterministic path
            if key not in trans_map:
                trans_map[key] = t

        steps = []
        current_state = start_state

        # Step 0: Initial state
        steps.append({
            "step": 0,
            "current_states": [current_state],
            "symbol_read": None,
            "transition_taken": None,
            "next_states": [current_state],
        })

        for idx, char in enumerate(input_string):
            key = (current_state, char)
            t_obj = trans_map.get(key)
            if t_obj:
                next_state = t_obj["to_state"]
                step_record = {
                    "step": idx + 1,
                    "current_states": [current_state],
                    "symbol_read": char,
                    "transition_taken": {
                        "from_state": t_obj["from_state"],
                        "to_state": t_obj["to_state"],
                        "symbol": t_obj["symbol"],
                    },
                    "next_states": [next_state],
                }
                steps.append(step_record)
                current_state = next_state
            else:
                # Dead state
                dead_state = "trap"
                step_record = {
                    "step": idx + 1,
                    "current_states": [current_state],
                    "symbol_read": char,
                    "transition_taken": None,
                    "next_states": [dead_state],
                }
                steps.append(step_record)
                current_state = dead_state
                break

        accepted = (current_state in accepting_ids)
        elapsed_ms = round((time.time() - start_time) * 1000, 3)

        return {
            "automaton_id": automaton.get("id", "automaton_default"),
            "input_string": input_string,
            "accepted": accepted,
            "final_states": [current_state],
            "execution_time_ms": elapsed_ms,
            "steps": steps,
        }

    # -------------------------------------------------------------------------
    # Labeled String & Trace Generation
    # -------------------------------------------------------------------------

    def generate_labeled_samples(
        self,
        automaton: Dict[str, Any],
        num_accepted: int = 5,
        num_rejected: int = 5,
        max_length: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Generates balanced candidate strings and simulation traces for an automaton.

        Returns:
            List of dicts: [
                {
                    "automaton": automaton,
                    "simulation_trace": trace_dict,
                    "input_string": str,
                    "accepted": bool,
                }, ...
            ]
        """
        alphabet = automaton.get("alphabet", ["a", "b"])
        states = automaton.get("states", [])
        start_state = automaton.get("start_state", "q0")
        accepting_ids = {s["id"] for s in states if s.get("is_accepting", False)}

        # Build BFS graph to find strings leading to states
        trans_map: Dict[Tuple[str, str], str] = {}
        for t in automaton.get("transitions", []):
            k = (t["from_state"], t["symbol"])
            if k not in trans_map:
                trans_map[k] = t["to_state"]

        accepted_strings: List[str] = []
        rejected_strings: List[str] = []
        seen_strings: Set[str] = set()

        # BFS queue of (current_state, string_so_far)
        queue = deque([(start_state, "")])
        seen_state_strings = {(start_state, "")}

        while queue and (len(accepted_strings) < num_accepted * 2 or len(rejected_strings) < num_rejected * 2):
            curr_state, s_so_far = queue.popleft()

            if s_so_far not in seen_strings:
                seen_strings.add(s_so_far)
                if curr_state in accepting_ids:
                    if len(accepted_strings) < num_accepted * 2:
                        accepted_strings.append(s_so_far)
                else:
                    if len(rejected_strings) < num_rejected * 2:
                        rejected_strings.append(s_so_far)

            if len(s_so_far) < max_length:
                # Shuffle alphabet for stochastic variety
                shuffled_alpha = list(alphabet)
                random.shuffle(shuffled_alpha)
                for sym in shuffled_alpha:
                    nxt = trans_map.get((curr_state, sym))
                    if nxt and (nxt, s_so_far + sym) not in seen_state_strings:
                        seen_state_strings.add((nxt, s_so_far + sym))
                        queue.append((nxt, s_so_far + sym))

        # Supplement with random walks if more are needed
        attempts = 0
        while (len(accepted_strings) < num_accepted or len(rejected_strings) < num_rejected) and attempts < 100:
            attempts += 1
            length = random.randint(1, max_length)
            cand_str = "".join(random.choice(alphabet) for _ in range(length))
            if cand_str in seen_strings:
                continue
            seen_strings.add(cand_str)
            sim = self.simulate_string(automaton, cand_str)
            if sim["accepted"] and len(accepted_strings) < num_accepted:
                accepted_strings.append(cand_str)
            elif not sim["accepted"] and len(rejected_strings) < num_rejected:
                rejected_strings.append(cand_str)

        # Select target counts
        selected_accepted = accepted_strings[:num_accepted]
        selected_rejected = rejected_strings[:num_rejected]

        results = []
        for s in selected_accepted + selected_rejected:
            trace = self.simulate_string(automaton, s)
            results.append({
                "automaton": automaton,
                "simulation_trace": trace,
                "input_string": s,
                "accepted": trace["accepted"],
            })

        return results

    # -------------------------------------------------------------------------
    # Full Dataset Generator
    # -------------------------------------------------------------------------

    def generate_dataset(
        self,
        num_automata: int = 40,
        samples_per_automaton: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generates a rich, varied dataset across multiple automaton families.

        Args:
            num_automata: Total number of distinct automata to construct.
            samples_per_automaton: Number of labeled string samples per automaton.

        Returns:
            List of sample dicts containing automaton, simulation_trace, input_string, accepted.
        """
        automata_list = []
        per_class = samples_per_automaton // 2

        # 1. Ends-with suite
        suffixes = ["abb", "ab", "bba", "01", "101", "11", "a", "b", "0", "1"]
        for suf in suffixes:
            alpha = ["a", "b"] if any(c in suf for c in "ab") else ["0", "1"]
            automata_list.append(self.generate_ends_with_dfa(suf, alpha))

        # 2. Contains suite
        contains_patterns = ["aa", "bb", "00", "11", "aba", "010"]
        for pat in contains_patterns:
            alpha = ["a", "b"] if any(c in pat for c in "ab") else ["0", "1"]
            automata_list.append(self.generate_contains_dfa(pat, alpha))

        # 3. Starts-with suite
        starts_patterns = ["a", "ab", "10", "01"]
        for pat in starts_patterns:
            alpha = ["a", "b"] if any(c in pat for c in "ab") else ["0", "1"]
            automata_list.append(self.generate_starts_with_dfa(pat, alpha))

        # 4. Parity suite
        automata_list.append(self.generate_parity_dfa("a", ["a", "b"], even=True))
        automata_list.append(self.generate_parity_dfa("a", ["a", "b"], even=False))
        automata_list.append(self.generate_parity_dfa("1", ["0", "1"], even=True))
        automata_list.append(self.generate_parity_dfa("1", ["0", "1"], even=False))

        # 5. Modulo length suite
        automata_list.append(self.generate_modulo_length_dfa(mod=2, alphabet=["a", "b"]))
        automata_list.append(self.generate_modulo_length_dfa(mod=3, alphabet=["0", "1"]))

        # 6. Random automata to reach num_automata
        remaining = max(0, num_automata - len(automata_list))
        for _ in range(remaining):
            n_states = random.randint(2, 6)
            alpha = random.choice(self.DEFAULT_ALPHABETS[:2])
            automata_list.append(self.generate_random_dfa(num_states=n_states, alphabet=alpha))

        # Now collect labeled samples
        dataset: List[Dict[str, Any]] = []
        for auto in automata_list:
            samples = self.generate_labeled_samples(
                auto,
                num_accepted=per_class,
                num_rejected=per_class,
            )
            dataset.extend(samples)

        random.shuffle(dataset)
        return dataset

"""
Automata Engine Correctness Tests against Python's `re.fullmatch`
================================================================
Verifies that:
1. For >= 15 diverse regular expressions, Python's re.fullmatch agrees
   with the NFA, DFA, and Minimized DFA on every single test string.
2. The Minimized DFA never has more states than the unminimized DFA.
3. Minimizing an already minimized DFA is idempotent.
"""

import re
import random
import pytest

from backend.automata_engine.engine import build_all
from backend.automata_engine.simulator.simulator import AutomataSimulator
from backend.automata_engine.dfa_minimizer.minimizer import DFAMinimizer


TEST_REGEXES = [
    "(a|b)*abb",
    "a*b*",
    "(ab)+",
    "a(b|c)*d",
    "0*10*1*",
    "(0|1)*00(0|1)*",
    "a+b+c+",
    "(a|b)*a(a|b)",
    "1(0|1)*0",
    "(ab|ba)*",
    "a?b+c*",
    "(0|1)+",
    "(a|b)*aaa(a|b)*",
    "(a|b)+abb",
    "a(a|b)*b",
    "x|y|z",
]


@pytest.fixture
def simulator():
    return AutomataSimulator()


@pytest.fixture
def minimizer():
    return DFAMinimizer()


@pytest.mark.parametrize("pattern", TEST_REGEXES)
def test_regex_correctness_against_re(pattern, simulator, minimizer):
    bundle = build_all(pattern)
    nfa = bundle["nfa"]
    dfa = bundle["dfa"]
    min_dfa = bundle["minimized_dfa"]
    alphabet = bundle["alphabet"]

    # 1. State count assertion: Minimized DFA states <= DFA states
    assert len(min_dfa.states) <= len(dfa.states), (
        f"For {pattern}, min DFA ({len(min_dfa.states)}) has more states than DFA ({len(dfa.states)})"
    )

    # 2. Idempotency: minimizing twice changes nothing
    min_dfa_again = minimizer.minimize(min_dfa)
    assert len(min_dfa_again.states) == len(min_dfa.states), (
        f"Minimizing twice changed state count for {pattern}"
    )
    assert len(min_dfa_again.transitions) == len(min_dfa.transitions)

    # Compile Python regex
    py_re = re.compile(pattern)

    # Generate candidate test strings
    # - Empty string
    # - Short strings
    # - Random strings of varying lengths
    candidates = [""]
    for sym in alphabet:
        candidates.append(sym)
        candidates.append(sym * 2)
        candidates.append(sym * 3)

    for c1 in alphabet:
        for c2 in alphabet:
            candidates.append(c1 + c2)

    # Add random strings
    random.seed(42)
    for _ in range(35):
        length = random.randint(1, 10)
        rand_str = "".join(random.choice(alphabet) for _ in range(length))
        candidates.append(rand_str)

    # Add strings with outside symbol
    candidates.append("xyz_invalid")

    # 3. Assert full agreement across re.fullmatch, NFA, DFA, and Minimized DFA
    for s in candidates:
        expected = bool(py_re.fullmatch(s))
        nfa_res = simulator.simulate(nfa, s).accepted
        dfa_res = simulator.simulate(dfa, s).accepted
        min_res = simulator.simulate(min_dfa, s).accepted

        assert nfa_res == expected, f"NFA mismatch on regex '{pattern}' with string '{s}': expected {expected}, got {nfa_res}"
        assert dfa_res == expected, f"DFA mismatch on regex '{pattern}' with string '{s}': expected {expected}, got {dfa_res}"
        assert min_res == expected, f"Min DFA mismatch on regex '{pattern}' with string '{s}': expected {expected}, got {min_res}"

"""
Unit Tests for Automata Simulator (Member A)
============================================
Tests DFA and NFA string simulation, trace formatting, and edge cases.
"""

import pytest
from backend.automata_engine.engine import build_all
from backend.automata_engine.simulator.simulator import AutomataSimulator


@pytest.fixture
def simulator():
    return AutomataSimulator()


def test_dfa_simulation_trace_format(simulator):
    bundle = build_all("(a|b)*abb")
    min_dfa = bundle["minimized_dfa"]

    res = simulator.simulate(min_dfa, "ababb")
    assert res.accepted is True
    assert res.automaton_id == min_dfa.id
    assert res.input_string == "ababb"
    assert len(res.steps) == 6  # Step 0 + 5 characters

    # Check step 0
    step0 = res.steps[0]
    assert step0.step == 0
    assert step0.current_states == ["q0"]
    assert step0.symbol_read is None
    assert step0.transition_taken is None
    assert step0.next_states == ["q0"]

    # Check step 1
    step1 = res.steps[1]
    assert step1.step == 1
    assert step1.current_states == ["q0"]
    assert step1.symbol_read == "a"
    assert step1.transition_taken is not None
    assert step1.next_states == ["q1"]


def test_nfa_simulation_trace_format(simulator):
    bundle = build_all("(a|b)*abb")
    nfa = bundle["nfa"]

    res = simulator.simulate(nfa, "ababb")
    assert res.accepted is True
    assert len(res.steps) == 6
    assert res.steps[0].step == 0
    # Step 0 on NFA should contain epsilon closure of start state
    assert len(res.steps[0].current_states) > 0


def test_simulation_empty_string(simulator):
    # Regex accepting empty string: a*
    bundle_star = build_all("a*")
    res_star_dfa = simulator.simulate(bundle_star["dfa"], "")
    res_star_nfa = simulator.simulate(bundle_star["nfa"], "")
    assert res_star_dfa.accepted is True
    assert res_star_nfa.accepted is True
    assert len(res_star_dfa.steps) == 1
    assert len(res_star_nfa.steps) == 1

    # Regex rejecting empty string: a+
    bundle_plus = build_all("a+")
    res_plus_dfa = simulator.simulate(bundle_plus["dfa"], "")
    res_plus_nfa = simulator.simulate(bundle_plus["nfa"], "")
    assert res_plus_dfa.accepted is False
    assert res_plus_nfa.accepted is False


def test_simulation_symbol_outside_alphabet(simulator):
    bundle = build_all("(a|b)*abb")
    min_dfa = bundle["minimized_dfa"]
    nfa = bundle["nfa"]

    # 'z' is not in alphabet ['a', 'b']
    res_dfa = simulator.simulate(min_dfa, "abzbb")
    assert res_dfa.accepted is False
    assert len(res_dfa.steps) == 4  # steps 0, 'a', 'b', 'z' (fails and halts early)

    res_nfa = simulator.simulate(nfa, "abzbb")
    assert res_nfa.accepted is False
    assert len(res_nfa.steps) == 4


def test_simulation_long_string(simulator):
    bundle = build_all("(a|b)*abb")
    min_dfa = bundle["minimized_dfa"]

    # 1000 characters ending in 'abb'
    long_str = ("ab" * 499) + "abb"
    res = simulator.simulate(min_dfa, long_str)
    assert res.accepted is True
    assert len(res.steps) == len(long_str) + 1

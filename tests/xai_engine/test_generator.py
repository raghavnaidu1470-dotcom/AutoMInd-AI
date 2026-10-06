"""
Unit Tests for Synthetic Automata Generator (Member B)
======================================================
Verifies generation of diverse, schema-compliant finite automata,
candidate strings, and simulation traces.
"""

import pytest
from backend.xai_engine.data.generator import SyntheticAutomataGenerator
from backend.automata_engine.models import Automaton, SimulationResult


@pytest.fixture
def generator():
    return SyntheticAutomataGenerator(seed=123)


def test_generate_ends_with_dfa(generator):
    dfa = generator.generate_ends_with_dfa("abb", ["a", "b"])
    # Validate structure and schema
    auto_obj = Automaton(**dfa)
    assert auto_obj.type == "DFA"
    assert auto_obj.start_state == "q0"
    assert len(auto_obj.states) == 4
    assert any(s.is_accepting for s in auto_obj.states)
    assert dfa["metadata"]["family"] == "ends_with"
    assert auto_obj.metadata.state_count == 4


def test_generate_starts_with_dfa(generator):
    dfa = generator.generate_starts_with_dfa("01", ["0", "1"])
    auto_obj = Automaton(**dfa)
    assert auto_obj.type == "DFA"
    assert len(auto_obj.states) >= 3
    assert any(s.is_accepting for s in auto_obj.states)
    assert dfa["metadata"]["family"] == "starts_with"


def test_generate_contains_dfa(generator):
    dfa = generator.generate_contains_dfa("aa", ["a", "b"])
    auto_obj = Automaton(**dfa)
    assert auto_obj.type == "DFA"
    assert dfa["metadata"]["family"] == "contains"


def test_generate_parity_dfa(generator):
    dfa_even = generator.generate_parity_dfa("a", ["a", "b"], even=True)
    auto_even = Automaton(**dfa_even)
    assert len(auto_even.states) == 2

    # String with even 'a's should be accepted
    trace_even = generator.simulate_string(dfa_even, "baa")
    assert trace_even["accepted"] is True

    # String with odd 'a's should be rejected
    trace_odd = generator.simulate_string(dfa_even, "ba")
    assert trace_odd["accepted"] is False


def test_generate_modulo_length_dfa(generator):
    dfa_mod = generator.generate_modulo_length_dfa(mod=3, alphabet=["0", "1"])
    auto_mod = Automaton(**dfa_mod)
    assert len(auto_mod.states) == 3

    # String of length 3 should be accepted
    trace_3 = generator.simulate_string(dfa_mod, "010")
    assert trace_3["accepted"] is True

    # String of length 2 should be rejected
    trace_2 = generator.simulate_string(dfa_mod, "01")
    assert trace_2["accepted"] is False


def test_simulate_string_trace_structure(generator):
    dfa = generator.generate_ends_with_dfa("abb", ["a", "b"])
    trace = generator.simulate_string(dfa, "ababb")
    trace_obj = SimulationResult(**trace)

    assert trace_obj.accepted is True
    assert len(trace_obj.steps) == 6  # Step 0 + 5 characters
    assert trace_obj.steps[0].step == 0
    assert trace_obj.steps[0].symbol_read is None
    assert trace_obj.steps[-1].step == 5
    assert trace_obj.steps[-1].symbol_read == "b"


def test_generate_labeled_samples(generator):
    dfa = generator.generate_ends_with_dfa("abb", ["a", "b"])
    samples = generator.generate_labeled_samples(dfa, num_accepted=3, num_rejected=3)

    assert len(samples) == 6
    accepted_count = sum(1 for s in samples if s["accepted"])
    rejected_count = sum(1 for s in samples if not s["accepted"])
    assert accepted_count == 3
    assert rejected_count == 3

    for s in samples:
        assert "automaton" in s
        assert "simulation_trace" in s
        assert "input_string" in s
        # Verify schema validity
        Automaton(**s["automaton"])
        SimulationResult(**s["simulation_trace"])


def test_generate_dataset(generator):
    dataset = generator.generate_dataset(num_automata=8, samples_per_automaton=4)
    assert len(dataset) > 0
    # Check balance
    accepted = [s for s in dataset if s["accepted"]]
    rejected = [s for s in dataset if not s["accepted"]]
    assert len(accepted) > 0
    assert len(rejected) > 0

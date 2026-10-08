"""
Unit Tests for Automata Data Models (Member A)
==============================================
Verifies that:
1. Pydantic models parse and validate the shared JSON contract accurately.
2. Canonical fixtures conform to schema.
"""

import pytest
from backend.automata_engine.models import Automaton, SimulationResult


def test_automaton_model_validation(mock_automaton_dict):
    """Verifies that the canonical mock automaton JSON parses cleanly into Automaton model."""
    automaton = Automaton.model_validate(mock_automaton_dict)
    assert automaton.id == "dfa_regex_ends_with_abb"
    assert automaton.type == "DFA"
    assert len(automaton.states) == 4
    assert len(automaton.transitions) == 8
    assert automaton.start_state == "q0"
    assert "a" in automaton.alphabet
    assert "b" in automaton.alphabet


def test_simulation_result_validation(mock_simulation_trace_dict):
    """Verifies that the canonical mock trace JSON parses into SimulationResult."""
    trace = SimulationResult.model_validate(mock_simulation_trace_dict)
    assert trace.automaton_id == "dfa_regex_ends_with_abb"
    assert trace.accepted is True
    assert len(trace.steps) == 6
    assert trace.final_states == ["q3"]

"""
Unit Tests for Automata Engine Stubs (Member A)
==============================================
Verifies that:
1. Pydantic models parse and validate the shared JSON contract accurately.
2. Member A's placeholder classes raise descriptive NotImplementedErrors.
"""

import pytest
from backend.automata_engine.models import Automaton, SimulationResult
from backend.automata_engine.regex_parser.parser import RegexParser
from backend.automata_engine.nfa_builder.builder import NFABuilder
from backend.automata_engine.dfa_converter.converter import DFAConverter
from backend.automata_engine.dfa_minimizer.minimizer import DFAMinimizer
from backend.automata_engine.simulator.simulator import AutomataSimulator


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


def test_regex_parser_stub_raises():
    """Verifies that RegexParser raises NotImplementedError until Member A builds it."""
    parser = RegexParser()
    with pytest.raises(NotImplementedError) as exc_info:
        parser.parse("(a|b)*abb")
    assert "Member A" in str(exc_info.value)


def test_nfa_builder_stub_raises():
    """Verifies that NFABuilder raises NotImplementedError until Member A builds it."""
    builder = NFABuilder()
    with pytest.raises(NotImplementedError) as exc_info:
        builder.build_from_ast(None)
    assert "Member A" in str(exc_info.value)


def test_dfa_converter_stub_raises(mock_automaton_dict):
    """Verifies that DFAConverter raises NotImplementedError for NFAs."""
    converter = DFAConverter()
    nfa_dict = dict(mock_automaton_dict)
    nfa_dict["type"] = "NFA"
    nfa = Automaton.model_validate(nfa_dict)
    with pytest.raises(NotImplementedError) as exc_info:
        converter.convert(nfa)
    assert "Member A" in str(exc_info.value)


def test_dfa_minimizer_stub_raises(mock_automaton_dict):
    """Verifies that DFAMinimizer raises NotImplementedError until Member A builds it."""
    minimizer = DFAMinimizer()
    dfa = Automaton.model_validate(mock_automaton_dict)
    with pytest.raises(NotImplementedError) as exc_info:
        minimizer.minimize(dfa)
    assert "Member A" in str(exc_info.value)


def test_simulator_stub_raises(mock_automaton_dict):
    """Verifies that AutomataSimulator raises NotImplementedError until Member A builds it."""
    simulator = AutomataSimulator()
    dfa = Automaton.model_validate(mock_automaton_dict)
    with pytest.raises(NotImplementedError) as exc_info:
        simulator.simulate(dfa, "ababb")
    assert "Member A" in str(exc_info.value)

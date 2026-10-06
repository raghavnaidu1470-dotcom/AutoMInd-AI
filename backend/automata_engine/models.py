"""
AutoMind AI — Shared Automata Data Models
=========================================
Owned by: Member A (Automata Theory Engine)
Consumed by: Member B (XAI Engine), Member C (API & Frontend)

Defines the Pydantic data schemas representing finite automata (NFA/DFA),
transitions, states, execution traces, and simulation outputs according to
the canonical schema documented in `docs/json_schema.md`.
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


class State(BaseModel):
    """
    Represents an individual state in a Finite Automaton.
    """
    id: str = Field(..., description="Unique state identifier (e.g., 'q0', 'q1')")
    label: Optional[str] = Field(None, description="Human-readable label for visualization")
    is_start: bool = Field(False, description="True if this is the start state")
    is_accepting: bool = Field(False, description="True if this state is an accepting / final state")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata, e.g. subset state IDs")


class Transition(BaseModel):
    """
    Represents a directed transition between two states on an alphabet symbol.
    For NFAs, symbol can be 'ε' or empty string for epsilon transitions.
    """
    id: Optional[str] = Field(None, description="Optional unique transition identifier")
    from_state: str = Field(..., description="Source state ID")
    to_state: str = Field(..., description="Target state ID")
    symbol: str = Field(..., description="Alphabet symbol or 'ε' for epsilon transition")


class AutomatonMetadata(BaseModel):
    """
    Metadata relating to the automaton construction and properties.
    """
    regex: Optional[str] = Field(None, description="Original source regular expression")
    state_count: Optional[int] = Field(None, description="Total number of states")
    transition_count: Optional[int] = Field(None, description="Total number of transitions")
    is_minimized: Optional[bool] = Field(False, description="True if DFA has undergone minimization")
    description: Optional[str] = Field(None, description="Free-text description or notes")


class Automaton(BaseModel):
    """
    Top-level representation of an NFA, DFA, or Minimized DFA.
    """
    id: str = Field(..., description="Unique identifier for the automaton")
    name: Optional[str] = Field(None, description="Display name for UI")
    type: str = Field("DFA", description="Type of automaton: 'NFA', 'DFA', or 'MINIMIZED_DFA'")
    alphabet: List[str] = Field(default_factory=list, description="Alphabet symbols excluding epsilon")
    start_state: str = Field(..., description="Start state ID")
    states: List[State] = Field(default_factory=list, description="List of all states")
    transitions: List[Transition] = Field(default_factory=list, description="List of all state transitions")
    metadata: Optional[AutomatonMetadata] = Field(default_factory=AutomatonMetadata, description="Associated metadata")


class SimulationStep(BaseModel):
    """
    Represents a single step in string simulation through the automaton.
    """
    step: int = Field(..., description="Step index (0 = initial state)")
    current_states: List[str] = Field(..., description="Active state IDs before reading the symbol")
    symbol_read: Optional[str] = Field(None, description="Character consumed from input string")
    transition_taken: Optional[Transition] = Field(None, description="Transition traversed in this step")
    next_states: List[str] = Field(..., description="Active state IDs after reading the symbol")


class SimulationResult(BaseModel):
    """
    Full result of executing a string on an automaton, including execution trace.
    """
    automaton_id: str = Field(..., description="ID of automaton simulated")
    input_string: str = Field(..., description="String tested against the automaton")
    accepted: bool = Field(..., description="True if string was accepted by the language")
    final_states: List[str] = Field(default_factory=list, description="States active at string termination")
    execution_time_ms: Optional[float] = Field(0.0, description="Execution time in milliseconds")
    steps: List[SimulationStep] = Field(default_factory=list, description="Step-by-step trace")

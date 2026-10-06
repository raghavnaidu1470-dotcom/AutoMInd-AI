# AutoMind AI — Shared JSON Schema Specification

This document defines the canonical JSON schemas used across all AutoMind AI subsystems. Both the **XAI Engine (Member B)** and the **Frontend / API Layer (Member C)** consume outputs produced by the **Automata Engine (Member A)**. Adhering to this contract ensures independent development and smooth integration.

---

## Table of Contents
1. [Design Principles](#design-principles)
2. [Automaton Schema (DFA & NFA)](#1-automaton-schema-dfa--nfa)
3. [Execution Trace Schema](#2-execution-trace-schema)
4. [XAI Explanation Output Schema](#3-xai-explanation-output-schema)
5. [Canonical Examples](#4-canonical-examples)

---

## Design Principles

- **Graph-Oriented Representation:** States are nodes, transitions are directed edges.
- **Support for Both NFA and DFA:** NFA transitions permit epsilon transitions (`"ε"` or `""`), multiple targets for the same symbol, and non-deterministic branching.
- **Typed IDs:** States use string IDs (e.g., `"q0"`, `"q1"`).
- **Extensible Metadata:** Includes source regular expressions, minimization status, and structural metrics.

---

## 1. Automaton Schema (DFA & NFA)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Automaton",
  "type": "object",
  "required": ["id", "type", "alphabet", "states", "transitions", "start_state"],
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique identifier for this automaton instance."
    },
    "name": {
      "type": "string",
      "description": "Human-readable label for display."
    },
    "type": {
      "type": "string",
      "enum": ["NFA", "DFA", "MINIMIZED_DFA"],
      "description": "Class of finite automaton."
    },
    "alphabet": {
      "type": "array",
      "items": { "type": "string" },
      "uniqueItems": true,
      "description": "Input alphabet symbols (excluding epsilon)."
    },
    "start_state": {
      "type": "string",
      "description": "ID of the designated start state."
    },
    "states": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "is_start", "is_accepting"],
        "properties": {
          "id": { "type": "string" },
          "label": { "type": "string" },
          "is_start": { "type": "boolean" },
          "is_accepting": { "type": "boolean" },
          "metadata": {
            "type": "object",
            "properties": {
              "nfa_subset": {
                "type": "array",
                "items": { "type": "string" },
                "description": "Original NFA state IDs if this state was produced by subset construction."
              }
            }
          }
        }
      }
    },
    "transitions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["from_state", "to_state", "symbol"],
        "properties": {
          "id": { "type": "string" },
          "from_state": { "type": "string" },
          "to_state": { "type": "string" },
          "symbol": {
            "type": "string",
            "description": "Input character or 'ε' for epsilon transitions."
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "regex": { "type": "string" },
        "state_count": { "type": "integer" },
        "transition_count": { "type": "integer" },
        "is_minimized": { "type": "boolean" }
      }
    }
  }
}
```

---

## 2. Execution Trace Schema

Produced when evaluating an input string against an automaton.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SimulationResult",
  "type": "object",
  "required": ["automaton_id", "input_string", "accepted", "steps", "final_states"],
  "properties": {
    "automaton_id": { "type": "string" },
    "input_string": { "type": "string" },
    "accepted": { "type": "boolean" },
    "final_states": {
      "type": "array",
      "items": { "type": "string" }
    },
    "execution_time_ms": { "type": "number" },
    "steps": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["step", "current_states", "symbol_read", "transition_taken", "next_states"],
        "properties": {
          "step": { "type": "integer" },
          "current_states": {
            "type": "array",
            "items": { "type": "string" }
          },
          "symbol_read": {
            "type": ["string", "null"]
          },
          "transition_taken": {
            "type": ["object", "null"],
            "properties": {
              "from_state": { "type": "string" },
              "to_state": { "type": "string" },
              "symbol": { "type": "string" }
            }
          },
          "next_states": {
            "type": "array",
            "items": { "type": "string" }
          }
        }
      }
    }
  }
}
```

---

## 3. XAI Explanation Output Schema

Produced by the GNNExplainer and SHAP pipeline (Member B) and consumed by the Frontend (Member C).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "XAIExplanation",
  "type": "object",
  "required": [
    "automaton_id",
    "input_string",
    "predicted_accepted",
    "confidence",
    "node_importance",
    "edge_importance",
    "critical_subgraph",
    "feature_attributions",
    "explanation_summary"
  ],
  "properties": {
    "automaton_id": { "type": "string" },
    "input_string": { "type": "string" },
    "predicted_accepted": { "type": "boolean" },
    "confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "node_importance": {
      "type": "object",
      "additionalProperties": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
      "description": "Mapping from state ID to attribution score [0, 1]."
    },
    "edge_importance": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["from_state", "to_state", "symbol", "importance"],
        "properties": {
          "from_state": { "type": "string" },
          "to_state": { "type": "string" },
          "symbol": { "type": "string" },
          "importance": { "type": "number", "minimum": 0.0, "maximum": 1.0 }
        }
      }
    },
    "critical_subgraph": {
      "type": "object",
      "required": ["nodes", "edges"],
      "properties": {
        "nodes": { "type": "array", "items": { "type": "string" } },
        "edges": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "from_state": { "type": "string" },
              "to_state": { "type": "string" },
              "symbol": { "type": "string" }
            }
          }
        }
      }
    },
    "feature_attributions": {
      "type": "object",
      "additionalProperties": { "type": "number" },
      "description": "SHAP feature-level attributions (e.g. is_accepting, in_degree, visit_frequency)."
    },
    "explanation_summary": {
      "type": "string",
      "description": "Natural language summary explaining why the string was accepted or rejected."
    }
  }
}
```

---

## 4. Canonical Examples

### Sample DFA for `(a|b)*abb`
A canonical automaton recognizing all strings over `{a, b}` ending in `"abb"`:

```json
{
  "id": "dfa_regex_ends_with_abb",
  "name": "DFA for (a|b)*abb",
  "type": "DFA",
  "alphabet": ["a", "b"],
  "start_state": "q0",
  "states": [
    { "id": "q0", "label": "q0", "is_start": true, "is_accepting": false },
    { "id": "q1", "label": "q1", "is_start": false, "is_accepting": false },
    { "id": "q2", "label": "q2", "is_start": false, "is_accepting": false },
    { "id": "q3", "label": "q3", "is_start": false, "is_accepting": true }
  ],
  "transitions": [
    { "from_state": "q0", "to_state": "q1", "symbol": "a" },
    { "from_state": "q0", "to_state": "q0", "symbol": "b" },
    { "from_state": "q1", "to_state": "q1", "symbol": "a" },
    { "from_state": "q1", "to_state": "q2", "symbol": "b" },
    { "from_state": "q2", "to_state": "q1", "symbol": "a" },
    { "from_state": "q2", "to_state": "q3", "symbol": "b" },
    { "from_state": "q3", "to_state": "q1", "symbol": "a" },
    { "from_state": "q3", "to_state": "q0", "symbol": "b" }
  ],
  "metadata": {
    "regex": "(a|b)*abb",
    "state_count": 4,
    "transition_count": 8,
    "is_minimized": true
  }
}
```

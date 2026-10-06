"""
Pytest Configuration & Fixtures
================================
Provides common fixtures and path resolution across all test suites.
"""

import sys
import json
from pathlib import Path
import pytest

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture
def mock_automaton_dict():
    """Loads the canonical mock automaton JSON fixture."""
    fixture_path = FIXTURES_DIR / "mock_automaton.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_simulation_trace_dict():
    """Loads the canonical mock simulation trace JSON fixture."""
    fixture_path = FIXTURES_DIR / "mock_simulation_trace.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_xai_explanation_dict():
    """Loads the canonical mock XAI explanation JSON fixture."""
    fixture_path = FIXTURES_DIR / "mock_xai_explanation.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)

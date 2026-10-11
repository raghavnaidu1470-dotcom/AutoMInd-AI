"""
Unit and Integration Tests for ReDoS Guard API Routes (Part 7)
=============================================================
Tests /api/redos/analyze and /api/redos/repair endpoints,
including input limits, error handling (400, 422), and response schemas.
"""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_analyze_exponential_regex(client):
    """Verify POST /api/redos/analyze detects exponential ReDoS on (a+)+$."""
    res = client.post("/api/redos/analyze", json={"regex": "(a+)+$", "run_empirical": True})
    assert res.status_code == 200
    data = res.json()
    assert data["risk_class"] == "exponential"
    assert data["is_vulnerable"] is True
    assert data["attack_string"] is not None
    assert "a" in data["attack_string"]["pump"]
    assert len(data["highlighted_spans"]) > 0
    assert data["empirical_benchmark"] is not None


def test_analyze_polynomial_regex(client):
    """Verify POST /api/redos/analyze detects polynomial ambiguity on a*a*b."""
    res = client.post("/api/redos/analyze", json={"regex": "a*a*b", "run_empirical": False})
    assert res.status_code == 200
    data = res.json()
    assert data["risk_class"] == "polynomial"
    assert data["is_vulnerable"] is True
    assert data["degree"] is not None


def test_analyze_linear_safe_regex(client):
    """Verify POST /api/redos/analyze confirms linear complexity on safe regex."""
    res = client.post("/api/redos/analyze", json={"regex": "(a|b)*abb", "run_empirical": False})
    assert res.status_code == 200
    data = res.json()
    assert data["risk_class"] == "linear"
    assert data["is_vulnerable"] is False
    assert data["attack_string"] is None


def test_analyze_empty_regex_400(client):
    """Verify empty regex returns real 400 error."""
    res = client.post("/api/redos/analyze", json={"regex": "   "})
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_analyze_length_limit_exceeded_4xx(client):
    """Verify regex exceeding 300 characters returns 422 or 400 validation error."""
    long_regex = "a" * 310
    res = client.post("/api/redos/analyze", json={"regex": long_regex})
    assert res.status_code in (400, 422)


def test_analyze_unsupported_backreference_400(client):
    """Verify backreferences return 400 with clear diagnostic message."""
    res = client.post("/api/redos/analyze", json={"regex": r"(a+)\1"})
    assert res.status_code == 400
    assert "backreferences" in res.json()["detail"].lower()


def test_repair_nested_plus_endpoint(client):
    """Verify POST /api/redos/repair returns language-equivalent repair with verification."""
    res = client.post("/api/redos/repair", json={"regex": "(a+)+$", "benchmark_before_after": True})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["repaired_regex"] == "a+$"
    assert data["equivalence_verified"] is True
    assert data["repaired_risk"] == "linear"
    assert data["before_benchmark"] is not None
    assert data["after_benchmark"] is not None


def test_repair_overlapping_alternation_endpoint(client):
    """Verify POST /api/redos/repair fixes overlapping alternation."""
    res = client.post("/api/redos/repair", json={"regex": "(a|aa)+", "benchmark_before_after": False})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["repaired_regex"] == "a+"
    assert data["equivalence_verified"] is True


def test_repair_unsupported_lookahead_400(client):
    """Verify unsupported lookahead in repair returns 400 error."""
    res = client.post("/api/redos/repair", json={"regex": "(?=abc)a*"})
    assert res.status_code == 400
    assert "lookahead" in res.json()["detail"].lower()

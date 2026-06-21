"""
Tests for the dashboard endpoints.
"""
from fastapi.testclient import TestClient

import src.agent as agent


def _analyze_payload(**overrides):
    base = {
        "pipeline_id": "p1", "status": "failed", "duration_seconds": 120,
        "logs": "x", "vulnerabilities": ["CVE-1"], "branch": "main",
        "commit_sha": "abcdef1234", "test_coverage_percent": 65.0,
        "is_direct_push": True, "pr_approved": False, "pr_reviewers_count": 0,
    }
    base.update(overrides)
    return base


def test_dashboard_page_served():
    with TestClient(agent.app) as c:
        r = c.get("/dashboard")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "CI/CD Guardian" in r.text


def test_dashboard_data_shape_and_recent(monkeypatch):
    monkeypatch.delenv("GUARDIAN_API_KEY", raising=False)
    with TestClient(agent.app) as c:
        c.post("/analyze", json=_analyze_payload())
        r = c.get("/dashboard/data")
    assert r.status_code == 200
    body = r.json()
    assert "metrics" in body and "recent" in body
    assert body["metrics"]["total_pipelines_analyzed"] >= 1
    assert body["metrics"]["ltm_backend"] in ("sqlite", "postgres")
    assert len(body["recent"]) >= 1
    assert body["recent"][0]["pipeline_id"] == "p1"
    assert body["recent"][0]["blocked"] is True


def test_dashboard_data_respects_auth(monkeypatch):
    monkeypatch.setenv("GUARDIAN_API_KEY", "secret")
    with TestClient(agent.app) as c:
        assert c.get("/dashboard/data").status_code == 401
        assert c.get("/dashboard/data", headers={"X-API-Key": "secret"}).status_code == 200
    # The HTML page itself stays open even when auth is enabled.
    with TestClient(agent.app) as c:
        assert c.get("/dashboard").status_code == 200

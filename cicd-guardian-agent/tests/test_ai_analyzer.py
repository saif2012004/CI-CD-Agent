"""
Tests for the optional Claude-powered AI analyzer.

The anthropic client is mocked, so these run with no API key and no network.
"""
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import src.agent as agent
from src.ai_analyzer import AIAnalyzer


class _Anomaly:
    def __init__(self, type, description, severity):
        self.type = type
        self.description = description
        self.severity = severity


def _text_block(text):
    b = MagicMock()
    b.type = "text"
    b.text = text
    return b


def test_disabled_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    analyzer = AIAnalyzer()
    assert analyzer.enabled is False
    assert analyzer.analyze("failed", "critical", [], "logs") is None


def test_enabled_returns_text(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    analyzer = AIAnalyzer()
    # Replace the real client with a mock regardless of SDK availability.
    analyzer.client = MagicMock()
    analyzer.client.messages.create.return_value = MagicMock(
        content=[_text_block("Root cause: tests failed.\nFix:\n- fix the test")]
    )

    out = analyzer.analyze(
        "failed", "critical",
        [_Anomaly("build_failure", "Pipeline build failed", "high")],
        "Traceback ... AssertionError",
    )
    assert "Root cause" in out
    assert "Fix:" in out
    # Verify it called the model with adaptive thinking
    _, kwargs = analyzer.client.messages.create.call_args
    assert kwargs["thinking"] == {"type": "adaptive"}
    assert kwargs["model"]


def test_api_error_degrades_to_none(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    analyzer = AIAnalyzer()
    analyzer.client = MagicMock()
    analyzer.client.messages.create.side_effect = RuntimeError("boom")
    assert analyzer.analyze("failed", "high", [], "logs") is None


def test_logs_are_truncated(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    analyzer = AIAnalyzer()
    analyzer.client = MagicMock()
    analyzer.client.messages.create.return_value = MagicMock(content=[_text_block("ok")])
    huge = "x" * 50000
    analyzer.analyze("failed", "high", [], huge)
    _, kwargs = analyzer.client.messages.create.call_args
    prompt = kwargs["messages"][0]["content"]
    # The full 50k log must not be passed verbatim
    assert len(prompt) < 20000


def test_analyze_endpoint_includes_ai_analysis(monkeypatch):
    monkeypatch.delenv("GUARDIAN_API_KEY", raising=False)
    payload = {
        "pipeline_id": "p1", "status": "failed", "duration_seconds": 100,
        "logs": "boom", "vulnerabilities": ["CVE-1"], "branch": "main",
        "commit_sha": "abc12345", "test_coverage_percent": 95.0,
        "is_direct_push": False, "pr_approved": True, "pr_reviewers_count": 2,
    }
    fake = MagicMock()
    fake.enabled = True
    fake.analyze.return_value = "AI: dependency CVE.\nFix:\n- bump the package"
    with TestClient(agent.app) as c:
        agent.AI_ANALYZER = fake  # override the one built during startup
        r = c.post("/analyze", json=payload)
    assert r.status_code == 200
    assert r.json()["ai_analysis"] == "AI: dependency CVE.\nFix:\n- bump the package"


def test_analyze_endpoint_ai_analysis_null_when_disabled(monkeypatch):
    monkeypatch.delenv("GUARDIAN_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    payload = {
        "pipeline_id": "p2", "status": "success", "duration_seconds": 100,
        "logs": "ok", "vulnerabilities": [], "branch": "feature/x",
        "commit_sha": "abc12345", "test_coverage_percent": 95.0,
        "is_direct_push": False, "pr_approved": True, "pr_reviewers_count": 2,
    }
    with TestClient(agent.app) as c:
        r = c.post("/analyze", json=payload)
    assert r.status_code == 200
    assert r.json()["ai_analysis"] is None

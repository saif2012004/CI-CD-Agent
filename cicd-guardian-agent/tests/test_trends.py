"""
Tests for historical trend detection (MemoryManager.get_trends) and its
exposure on /dashboard/data.
"""
from fastapi.testclient import TestClient

import src.agent as agent
from src.memory_manager import MemoryManager


class _Anomaly:
    def __init__(self, type, description, severity):
        self.type = type
        self.description = description
        self.severity = severity


def _mm(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return MemoryManager(
        stm_path=str(tmp_path / "stm.json"),
        ltm_path=str(tmp_path / "ltm.db"),
    )


def _save(mm, duration, blocked):
    mm.save_incident(
        pipeline_id="p", status="failed", severity="high",
        duration_seconds=duration, branch="main", commit_sha="abc",
        anomalies=[_Anomaly("x", "d", "high")] if blocked else [],
        recommendation="r", blocked=blocked,
    )


def test_trends_unavailable_with_few_incidents(tmp_path, monkeypatch):
    mm = _mm(tmp_path, monkeypatch)
    _save(mm, 100, False)
    assert mm.get_trends()["available"] is False


def test_trends_detect_rising_duration(tmp_path, monkeypatch):
    mm = _mm(tmp_path, monkeypatch)
    # Older incidents (inserted first) are fast; newer ones are slow.
    for _ in range(4):
        _save(mm, 100, False)
    for _ in range(4):
        _save(mm, 400, False)
    trends = mm.get_trends()
    assert trends["available"] is True
    assert trends["duration"]["direction"] == "rising"
    assert any("duration" in i.lower() for i in trends["insights"])


def test_trends_detect_rising_block_rate(tmp_path, monkeypatch):
    mm = _mm(tmp_path, monkeypatch)
    for _ in range(4):
        _save(mm, 100, False)   # older: not blocked
    for _ in range(4):
        _save(mm, 100, True)    # newer: blocked
    trends = mm.get_trends()
    assert trends["block_rate"]["direction"] == "rising"


def test_dashboard_data_includes_trends(monkeypatch):
    monkeypatch.delenv("GUARDIAN_API_KEY", raising=False)
    with TestClient(agent.app) as c:
        r = c.get("/dashboard/data")
    assert r.status_code == 200
    assert "trends" in r.json()

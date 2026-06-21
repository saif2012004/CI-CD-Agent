"""
Tests for the LTM storage backend selection and the SQLite path.

The Postgres path needs a live server, so it isn't exercised here; instead we
test the pure backend-selection / placeholder logic plus a full SQLite round
trip (which covers the refactored DDL, insert, and metrics code).
"""
from src.memory_manager import detect_backend, to_paramstyle, MemoryManager


# --- backend detection ------------------------------------------------------

def test_detect_sqlite_when_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert detect_backend() == ("sqlite", None)


def test_detect_postgres_full_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host/db")
    assert detect_backend() == ("postgres", "postgresql://u:p@host/db")


def test_detect_postgres_short_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host/db")
    backend, _ = detect_backend()
    assert backend == "postgres"


def test_detect_ignores_non_postgres_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql://x")
    assert detect_backend() == ("sqlite", None)


# --- placeholder translation ------------------------------------------------

def test_paramstyle_postgres():
    assert to_paramstyle("VALUES (?, ?, ?)", "postgres") == "VALUES (%s, %s, %s)"


def test_paramstyle_sqlite_unchanged():
    assert to_paramstyle("VALUES (?, ?)", "sqlite") == "VALUES (?, ?)"


# --- SQLite round trip ------------------------------------------------------

class _Anomaly:
    def __init__(self, type, description, severity):
        self.type = type
        self.description = description
        self.severity = severity


def _manager(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return MemoryManager(
        stm_path=str(tmp_path / "stm.json"),
        ltm_path=str(tmp_path / "ltm.db"),
    )


def test_manager_defaults_to_sqlite(tmp_path, monkeypatch):
    mm = _manager(tmp_path, monkeypatch)
    assert mm.backend == "sqlite"
    status = mm.get_memory_status()
    assert status["ltm_backend"] == "sqlite"
    assert status["ltm"] == "ok"


def test_save_and_metrics_roundtrip(tmp_path, monkeypatch):
    mm = _manager(tmp_path, monkeypatch)
    ok = mm.save_incident(
        pipeline_id="p1", status="failed", severity="critical",
        duration_seconds=120, branch="main", commit_sha="abc12345",
        anomalies=[_Anomaly("security_vulnerability", "CVE-1", "critical")],
        recommendation="fix it", blocked=True,
    )
    assert ok is True
    mm.update_stm("p1", "critical")

    metrics = mm.get_metrics()
    assert metrics["total_pipelines_analyzed"] == 1
    assert metrics["critical_incidents"] == 1
    assert metrics["top_anomalies"][0]["type"] == "security_vulnerability"

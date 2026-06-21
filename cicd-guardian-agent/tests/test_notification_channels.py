"""
Tests for the extra notification channels (Discord, Teams) and GitHub issue
creation.
"""
from unittest.mock import MagicMock, patch

from src.notifier import Notifier
from src.github_client import GitHubClient


class _Anomaly:
    def __init__(self, description, severity="high"):
        self.description = description
        self.severity = severity
        self.type = "x"


def _anomalies():
    return [_Anomaly("Pipeline build failed")]


def test_env_vars_take_precedence(monkeypatch):
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord/env")
    monkeypatch.setenv("TEAMS_WEBHOOK_URL", "https://teams/env")
    n = Notifier({"discord_webhook": "https://discord/config"})
    assert n.discord_webhook == "https://discord/env"
    assert n.teams_webhook == "https://teams/env"


def test_discord_and_teams_fired(monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("TEAMS_WEBHOOK_URL", raising=False)
    n = Notifier({
        "discord_webhook": "https://discord.example/hook",
        "teams_webhook": "https://teams.example/hook",
        "alert_on": ["critical", "high"],
    })
    with patch.object(n, "_send_webhook_text", return_value=True) as m:
        results = n.send_notifications(
            "p1", "critical", _anomalies(), "fix it", "main", "abcdef12"
        )
    assert results["discord"] is True
    assert results["teams"] is True
    # Discord uses {"content": ...}, Teams uses {"text": ...}
    payloads = [call.args[1] for call in m.call_args_list]
    assert any("content" in p for p in payloads)
    assert any("text" in p for p in payloads)


def test_low_severity_skips_all(monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    n = Notifier({"discord_webhook": "https://d/hook", "alert_on": ["critical"]})
    results = n.send_notifications("p", "low", _anomalies(), "r", "b", "sha12345")
    assert results == {"notified": False}


def test_webhook_text_handles_204():
    n = Notifier({})
    resp = MagicMock()
    resp.status = 204
    cm = MagicMock()
    cm.__enter__.return_value = resp
    with patch("urllib.request.urlopen", return_value=cm):
        assert n._send_webhook_text("https://x/hook", {"content": "hi"}, "discord") is True


def test_create_issue():
    c = GitHubClient(token="t", repo="o/r")
    c.session = MagicMock()
    c.session.post.return_value = MagicMock()
    assert c.create_issue("title", "body", labels=["x"]) is True
    _, kwargs = c.session.post.call_args
    assert kwargs["json"]["title"] == "title"
    assert kwargs["json"]["labels"] == ["x"]


def test_create_issue_handles_error():
    c = GitHubClient(token="t", repo="o/r")
    c.session = MagicMock()
    c.session.post.return_value.raise_for_status.side_effect = RuntimeError("boom")
    assert c.create_issue("t", "b") is False

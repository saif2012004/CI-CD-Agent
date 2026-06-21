"""
Integration tests for the GitHub wiring in /analyze.

The GitHubClient is replaced with a mock so no network calls happen; these
verify the agent (a) uses real PR review data and (b) posts a Check Run.
"""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import src.agent as agent


@pytest.fixture
def fake_gh(monkeypatch):
    """Patch src.agent.GitHubClient to return a controllable mock instance."""
    instance = MagicMock()
    instance.get_pr_review_status.return_value = {
        "approved": True,
        "approvals_count": 2,
        "reviewers_count": 2,
        "changes_requested": False,
    }
    monkeypatch.setattr(agent, "GitHubClient", lambda *a, **k: instance)
    return instance


def _payload(**overrides):
    base = {
        "pipeline_id": "p1",
        "status": "success",
        "duration_seconds": 100,
        "logs": "ok",
        "vulnerabilities": [],
        "branch": "main",
        "commit_sha": "abc12345",
        "test_coverage_percent": 95.0,
        "is_direct_push": False,
        "pr_approved": None,
        "pr_reviewers_count": None,
        "github_repo": "owner/repo",
        "github_pr_number": 5,
        "github_token": "tok",
    }
    base.update(overrides)
    return base


def test_real_pr_approval_prevents_false_positive(fake_gh):
    """An approved PR to main must NOT be flagged pr_not_approved."""
    with TestClient(agent.app) as c:
        r = c.post("/analyze", json=_payload())
    assert r.status_code == 200
    types = {a["type"] for a in r.json()["anomalies"]}
    assert "pr_not_approved" not in types
    fake_gh.get_pr_review_status.assert_called_once_with(5)


def test_clean_run_posts_success_check(fake_gh):
    with TestClient(agent.app) as c:
        r = c.post("/analyze", json=_payload())
    assert r.json()["block_merge"] is False
    fake_gh.post_check_run.assert_called_once()
    args, _ = fake_gh.post_check_run.call_args
    assert args[0] == "abc12345"   # commit sha
    assert args[1] == "success"    # conclusion


def test_critical_run_posts_failure_check_and_comment(fake_gh):
    # Unapproved PR data + a CVE -> critical -> failure check + PR comment
    fake_gh.get_pr_review_status.return_value = {
        "approved": False, "approvals_count": 0,
        "reviewers_count": 0, "changes_requested": False,
    }
    with TestClient(agent.app) as c:
        r = c.post("/analyze", json=_payload(vulnerabilities=["CVE-2023-1"]))
    assert r.json()["block_merge"] is True
    assert fake_gh.post_check_run.call_args[0][1] == "failure"
    fake_gh.post_pr_comment.assert_called_once()


def test_no_github_context_skips_github(monkeypatch):
    """Without repo/token, the agent must not construct a GitHub client."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    sentinel = MagicMock(side_effect=AssertionError("should not be called"))
    monkeypatch.setattr(agent, "GitHubClient", sentinel)
    with TestClient(agent.app) as c:
        r = c.post("/analyze", json=_payload(github_repo=None, github_token=None,
                                             github_pr_number=None))
    assert r.status_code == 200

"""
Unit tests for GitHubClient (no real network calls — the session is mocked).
"""
from unittest.mock import MagicMock

from src.github_client import GitHubClient


def _client():
    c = GitHubClient(token="t", repo="owner/repo")
    c.session = MagicMock()
    return c


def _resp(json_data=None, raise_exc=None):
    r = MagicMock()
    r.json.return_value = json_data or []
    if raise_exc:
        r.raise_for_status.side_effect = raise_exc
    return r


def test_review_status_counts_approvals_and_changes():
    c = _client()
    c.session.get.return_value = _resp([
        {"user": {"login": "alice"}, "state": "APPROVED"},
        {"user": {"login": "bob"}, "state": "CHANGES_REQUESTED"},
        {"user": {"login": "carol"}, "state": "COMMENTED"},  # ignored
    ])
    status = c.get_pr_review_status(1)
    assert status["approvals_count"] == 1
    assert status["changes_requested"] is True
    assert status["reviewers_count"] == 2  # carol's COMMENTED ignored
    # Approved requires at least one approval AND no changes requested
    assert status["approved"] is False


def test_review_status_approved_when_only_approvals():
    c = _client()
    c.session.get.return_value = _resp([
        {"user": {"login": "alice"}, "state": "APPROVED"},
        {"user": {"login": "bob"}, "state": "APPROVED"},
    ])
    status = c.get_pr_review_status(1)
    assert status["approved"] is True
    assert status["approvals_count"] == 2


def test_review_status_uses_latest_review_per_user():
    c = _client()
    c.session.get.return_value = _resp([
        {"user": {"login": "alice"}, "state": "CHANGES_REQUESTED"},
        {"user": {"login": "alice"}, "state": "APPROVED"},  # later one wins
    ])
    status = c.get_pr_review_status(1)
    assert status["approved"] is True
    assert status["changes_requested"] is False


def test_review_status_returns_none_on_error():
    c = _client()
    c.session.get.side_effect = RuntimeError("boom")
    assert c.get_pr_review_status(1) is None


def test_post_check_run_success_payload():
    c = _client()
    c.session.post.return_value = _resp({})
    ok = c.post_check_run("sha123", "failure", "title", "summary")
    assert ok is True
    _, kwargs = c.session.post.call_args
    payload = kwargs["json"]
    assert payload["conclusion"] == "failure"
    assert payload["head_sha"] == "sha123"
    assert payload["status"] == "completed"


def test_post_check_run_returns_false_on_error():
    c = _client()
    c.session.post.return_value = _resp({}, raise_exc=RuntimeError("nope"))
    assert c.post_check_run("sha", "success", "t", "s") is False


def test_post_pr_comment():
    c = _client()
    c.session.post.return_value = _resp({})
    assert c.post_pr_comment(7, "hello") is True
    _, kwargs = c.session.post.call_args
    assert kwargs["json"] == {"body": "hello"}

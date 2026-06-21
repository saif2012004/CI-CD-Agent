"""
GitHub API client.

Lets the agent act autonomously on GitHub instead of just returning a verdict:
- read the *real* pull-request review state (who approved, who requested changes)
- post a Check Run that gates merges via branch protection
- comment its findings directly on the pull request

All methods are best-effort: failures are logged and reported via the return
value, never raised, so a GitHub hiccup can't break pipeline analysis.
"""
import logging
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
CHECK_RUN_NAME = "CI/CD Guardian"


class GitHubClient:
    """Thin wrapper over the GitHub REST API for the actions the agent needs."""

    def __init__(self, token: str, repo: str, timeout: int = 10):
        """
        Args:
            token: A GitHub token with `checks: write`, `pull-requests: write`.
            repo: Repository in "owner/name" form.
            timeout: Per-request timeout in seconds.
        """
        self.repo = repo
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def get_pr_review_status(self, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Summarize the current review state of a pull request.

        Returns a dict with `approved`, `approvals_count`, `reviewers_count`,
        and `changes_requested`, or None if the data can't be fetched.
        """
        try:
            url = f"{GITHUB_API}/repos/{self.repo}/pulls/{pr_number}/reviews"
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            reviews = resp.json()

            # Keep only each reviewer's latest decisive review (ignore plain comments).
            latest: Dict[str, str] = {}
            for review in reviews:
                user = (review.get("user") or {}).get("login")
                state = review.get("state")
                if not user or state == "COMMENTED":
                    continue
                latest[user] = state

            approvals = [u for u, s in latest.items() if s == "APPROVED"]
            changes_requested = [u for u, s in latest.items() if s == "CHANGES_REQUESTED"]

            return {
                "approved": bool(approvals) and not changes_requested,
                "approvals_count": len(approvals),
                "reviewers_count": len(latest),
                "changes_requested": bool(changes_requested),
            }
        except Exception as e:
            logger.warning(f"Failed to fetch PR review status: {e}")
            return None

    def post_check_run(
        self,
        commit_sha: str,
        conclusion: str,
        title: str,
        summary: str,
    ) -> bool:
        """
        Create a completed Check Run on a commit.

        Args:
            conclusion: "success", "failure", or "neutral".
        """
        try:
            url = f"{GITHUB_API}/repos/{self.repo}/check-runs"
            payload = {
                "name": CHECK_RUN_NAME,
                "head_sha": commit_sha,
                "status": "completed",
                "conclusion": conclusion,
                "output": {"title": title[:120], "summary": summary[:65000]},
            }
            resp = self.session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            logger.info(f"Posted check run ({conclusion}) for {commit_sha[:8]}")
            return True
        except Exception as e:
            logger.warning(f"Failed to create check run: {e}")
            return False

    def post_pr_comment(self, pr_number: int, body: str) -> bool:
        """Post a comment on a pull request (via the issues comments API)."""
        try:
            url = f"{GITHUB_API}/repos/{self.repo}/issues/{pr_number}/comments"
            resp = self.session.post(url, json={"body": body}, timeout=self.timeout)
            resp.raise_for_status()
            logger.info(f"Posted PR comment on #{pr_number}")
            return True
        except Exception as e:
            logger.warning(f"Failed to post PR comment: {e}")
            return False

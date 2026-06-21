"""
Unit tests for PolicyEnforcer.

These cover the core policy-enforcement logic the agent exists to provide:
build status, duration (config-driven), vulnerabilities, branch protection,
PR approval, test coverage, severity calculation, and recommendations.
"""
import pytest

from src.policy_enforcer import PolicyEnforcer
from src.models import Anomaly


@pytest.fixture
def config():
    """Representative config mirroring config/rules.yaml."""
    return {
        "branch_protection": {
            "protected_branches": ["main", "master", "develop"],
            "require_pull_request": True,
            "min_approvals": 2,
        },
        "test_coverage": {"minimum_percentage": 80},
        "build_monitoring": {"max_duration_seconds": 600},
    }


@pytest.fixture
def enforcer(config):
    return PolicyEnforcer(config)


def _analyze(enforcer, **overrides):
    """Run analyze_pipeline with sensible 'clean pipeline' defaults."""
    kwargs = dict(
        status="success",
        duration_seconds=100,
        vulnerabilities=[],
        branch="feature/x",
        commit_sha="abc12345",
        logs="ok",
        test_coverage_percent=95.0,
        is_direct_push=False,
        pr_approved=True,
        pr_reviewers_count=2,
    )
    kwargs.update(overrides)
    return enforcer.analyze_pipeline(**kwargs)


# --- build status -----------------------------------------------------------

def test_clean_pipeline_has_no_anomalies(enforcer):
    assert _analyze(enforcer) == []


def test_failed_build_flagged_high(enforcer):
    anomalies = _analyze(enforcer, status="failed")
    assert any(a.type == "build_failure" and a.severity == "high" for a in anomalies)


def test_aborted_build_flagged_high(enforcer):
    anomalies = _analyze(enforcer, status="aborted")
    assert any(a.type == "build_aborted" and a.severity == "high" for a in anomalies)


def test_status_is_case_insensitive(enforcer):
    assert any(a.type == "build_failure" for a in _analyze(enforcer, status="FAILED"))


# --- duration (config-driven) ----------------------------------------------

def test_duration_within_threshold_ok(enforcer):
    assert not any(a.type == "excessive_duration" for a in _analyze(enforcer, duration_seconds=600))


def test_duration_over_threshold_flagged(enforcer):
    anomalies = _analyze(enforcer, duration_seconds=601)
    assert any(a.type == "excessive_duration" and a.severity == "medium" for a in anomalies)


def test_duration_threshold_respects_config():
    """Regression: the threshold must come from config, not be hardcoded to 600."""
    strict = PolicyEnforcer({"build_monitoring": {"max_duration_seconds": 60}})
    anomalies = strict._check_duration(120)
    assert any(a.type == "excessive_duration" for a in anomalies)


# --- vulnerabilities --------------------------------------------------------

def test_each_cve_is_critical(enforcer):
    anomalies = _analyze(enforcer, vulnerabilities=["CVE-2023-1", "CVE-2023-2"])
    vulns = [a for a in anomalies if a.type == "security_vulnerability"]
    assert len(vulns) == 2
    assert all(a.severity == "critical" for a in vulns)


# --- branch protection ------------------------------------------------------

def test_direct_push_to_protected_branch_is_critical(enforcer):
    anomalies = _analyze(enforcer, branch="main", is_direct_push=True)
    assert any(a.type == "branch_protection_violation" and a.severity == "critical" for a in anomalies)


def test_direct_push_to_unprotected_branch_ok(enforcer):
    anomalies = _analyze(enforcer, branch="feature/x", is_direct_push=True)
    assert not any(a.type == "branch_protection_violation" for a in anomalies)


# --- PR approval ------------------------------------------------------------

def test_unapproved_pr_to_protected_branch_is_critical(enforcer):
    anomalies = _analyze(enforcer, branch="main", pr_approved=False, pr_reviewers_count=2)
    assert any(a.type == "pr_not_approved" and a.severity == "critical" for a in anomalies)


def test_insufficient_reviewers_flagged(enforcer):
    anomalies = _analyze(enforcer, branch="main", pr_approved=True, pr_reviewers_count=1)
    assert any(a.type == "insufficient_reviewers" and a.severity == "high" for a in anomalies)


# --- test coverage ----------------------------------------------------------

def test_low_coverage_is_critical(enforcer):
    anomalies = _analyze(enforcer, test_coverage_percent=79.9)
    assert any(a.type == "insufficient_test_coverage" and a.severity == "critical" for a in anomalies)


def test_coverage_at_threshold_ok(enforcer):
    assert not any(a.type == "insufficient_test_coverage" for a in _analyze(enforcer, test_coverage_percent=80.0))


def test_missing_coverage_is_not_flagged(enforcer):
    assert not any(a.type == "insufficient_test_coverage" for a in _analyze(enforcer, test_coverage_percent=None))


# --- severity calculation ---------------------------------------------------

def test_severity_none_when_clean(enforcer):
    assert enforcer.calculate_severity([]) == "none"


def test_any_critical_makes_overall_critical(enforcer):
    anomalies = [Anomaly(type="x", description="d", severity="critical")]
    assert enforcer.calculate_severity(anomalies) == "critical"


def test_three_or_more_anomalies_escalate_to_critical(enforcer):
    anomalies = [Anomaly(type="x", description="d", severity="medium") for _ in range(3)]
    assert enforcer.calculate_severity(anomalies) == "critical"


def test_single_high_is_high(enforcer):
    anomalies = [Anomaly(type="x", description="d", severity="high")]
    assert enforcer.calculate_severity(anomalies) == "high"


def test_single_medium_is_medium(enforcer):
    anomalies = [Anomaly(type="x", description="d", severity="medium")]
    assert enforcer.calculate_severity(anomalies) == "medium"


# --- recommendations --------------------------------------------------------

def test_recommendation_when_clean(enforcer):
    assert "No action required" in enforcer.generate_recommendation([], "none")


def test_critical_recommendation_blocks_merge(enforcer):
    anomalies = [Anomaly(type="security_vulnerability", description="CVE", severity="critical")]
    rec = enforcer.generate_recommendation(anomalies, "critical")
    assert "Block merge" in rec
    assert "dependencies" in rec.lower()

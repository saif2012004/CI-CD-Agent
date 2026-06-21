"""
Tests for the diff-based extra checks: secret scanning (src/scanners.py) and
the PolicyEnforcer secret / large-file checks.
"""
from src.scanners import scan_diff_for_secrets
from src.policy_enforcer import PolicyEnforcer


# --- secret scanner --------------------------------------------------------

def _diff(file, line):
    return f"diff --git a/{file} b/{file}\n+++ b/{file}\n+{line}\n"


def test_scan_detects_aws_key():
    findings = scan_diff_for_secrets(_diff("config.py", "AKIA1234567890ABCDEF"))
    # AKIA pattern matches; descriptor names the file but not the value
    assert any("AWS Access Key in config.py" == f for f in findings)
    assert all("AKIA" not in f for f in findings)  # value never leaked


def test_scan_detects_private_key():
    findings = scan_diff_for_secrets(_diff("id_rsa", "-----BEGIN RSA PRIVATE KEY-----"))
    assert any("Private Key" in f for f in findings)


def test_scan_detects_generic_assignment():
    findings = scan_diff_for_secrets(_diff("app.py", 'password = "s3cr3tPassw0rd123456"'))
    assert any("Generic Secret Assignment" in f for f in findings)


def test_scan_ignores_placeholders():
    assert scan_diff_for_secrets(_diff("app.py", 'api_key = "YOUR_API_KEY_HERE_PLACEHOLDER"')) == []


def test_scan_ignores_removed_and_context_lines():
    diff = "+++ b/app.py\n-AKIA1234567890ABCDEF\n AKIA1234567890ABCDEF\n"
    assert scan_diff_for_secrets(diff) == []


def test_scan_empty_diff():
    assert scan_diff_for_secrets("") == []


# --- policy enforcer checks ------------------------------------------------

def test_check_secrets_are_critical():
    pe = PolicyEnforcer({})
    anomalies = pe._check_secrets(["AWS Access Key in config.py"])
    assert len(anomalies) == 1
    assert anomalies[0].type == "secret_detected"
    assert anomalies[0].severity == "critical"


def test_check_large_files_flags_over_threshold():
    pe = PolicyEnforcer({"policy": {"max_file_size_mb": 1}})
    anomalies = pe._check_large_files([
        {"path": "big.bin", "size_bytes": 3 * 1024 * 1024},
        {"path": "small.txt", "size_bytes": 1000},
    ])
    assert len(anomalies) == 1
    assert anomalies[0].type == "large_file"
    assert "big.bin" in anomalies[0].description


def test_check_large_files_default_threshold():
    pe = PolicyEnforcer({})  # default 5 MB
    assert pe._check_large_files([{"path": "x", "size_bytes": 4 * 1024 * 1024}]) == []
    assert len(pe._check_large_files([{"path": "x", "size_bytes": 6 * 1024 * 1024}])) == 1


def test_analyze_pipeline_includes_extra_checks():
    pe = PolicyEnforcer({"policy": {"max_file_size_mb": 1}})
    anomalies = pe.analyze_pipeline(
        status="success", duration_seconds=10, vulnerabilities=[],
        branch="main", commit_sha="abc", logs="",
        secrets_detected=["GitHub Token in deploy.sh"],
        changed_files=[{"path": "blob.zip", "size_bytes": 2 * 1024 * 1024}],
    )
    types = {a.type for a in anomalies}
    assert "secret_detected" in types
    assert "large_file" in types

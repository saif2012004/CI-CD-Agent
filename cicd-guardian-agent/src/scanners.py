"""
Diff scanners.

These run inside CI (where the checked-out code lives) so that raw secrets
never leave the runner. They return *redacted* descriptors — a rule name and
file path, never the matched secret value — which the workflow forwards to the
agent for policy enforcement.
"""
import re
from typing import List

# High-precision secret patterns. Kept deliberately narrow to limit false
# positives — broad entropy scanning is intentionally avoided.
SECRET_PATTERNS = {
    "AWS Access Key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub Token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "Slack Token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "Private Key": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"
    ),
    "Generic Secret Assignment": re.compile(
        r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*"
        r"['\"][A-Za-z0-9_\-./+]{16,}['\"]"
    ),
}

# Lines containing these (case-insensitive) are treated as placeholders, not
# real secrets, to cut false positives from examples and templates.
_PLACEHOLDER_HINTS = (
    "your", "example", "changeme", "placeholder", "dummy", "redacted",
    "xxxx", "<", "}}", "${", "sample", "fake", "test-",
)


def _is_placeholder(line: str) -> bool:
    low = line.lower()
    return any(hint in low for hint in _PLACEHOLDER_HINTS)


def scan_diff_for_secrets(diff: str) -> List[str]:
    """
    Scan a unified diff's added lines for secrets.

    Returns redacted descriptors like "AWS Access Key in src/config.py".
    The matched secret value is never included.
    """
    if not diff:
        return []

    findings = set()
    current_file = "unknown"

    for line in diff.splitlines():
        if line.startswith("+++ "):
            # "+++ b/path/to/file" — strip the "b/" prefix when present
            path = line[4:].strip()
            if path.startswith(("a/", "b/")):
                path = path[2:]
            current_file = path or "unknown"
            continue
        # Only consider added lines (but not the file header handled above)
        if not line.startswith("+"):
            continue
        added = line[1:]
        if _is_placeholder(added):
            continue
        for rule, pattern in SECRET_PATTERNS.items():
            if pattern.search(added):
                findings.add(f"{rule} in {current_file}")

    return sorted(findings)

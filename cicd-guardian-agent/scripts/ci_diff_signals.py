#!/usr/bin/env python
"""
Compute diff-based policy signals inside CI.

Usage: python scripts/ci_diff_signals.py <base_sha> <head_sha>

Prints a JSON object: {"changed_files": [{path, size_bytes}], "secrets_detected": [...]}
The secret scan runs here (in CI) and emits only redacted descriptors — the raw
secret value never leaves the runner. Safe to run with empty/zero base (returns
empty signals).
"""
import json
import os
import subprocess
import sys

# Make `from src.scanners import ...` work regardless of cwd.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.scanners import scan_diff_for_secrets  # noqa: E402

MAX_DIFF_BYTES = 200_000
ZERO_SHA = "0" * 40


def _git(args, cwd):
    try:
        return subprocess.run(
            ["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=60
        ).stdout
    except Exception:
        return ""


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else ""
    head = sys.argv[2] if len(sys.argv) > 2 else ""
    root = os.environ.get("GITHUB_WORKSPACE", ".")
    out = {"changed_files": [], "secrets_detected": []}

    if not base or base == ZERO_SHA or not head:
        print(json.dumps(out))
        return

    diff = _git(["diff", base, head], root)[:MAX_DIFF_BYTES]
    out["secrets_detected"] = scan_diff_for_secrets(diff)

    for path in _git(["diff", "--name-only", base, head], root).splitlines():
        path = path.strip()
        full = os.path.join(root, path)
        if path and os.path.isfile(full):
            out["changed_files"].append(
                {"path": path, "size_bytes": os.path.getsize(full)}
            )

    print(json.dumps(out))


if __name__ == "__main__":
    main()

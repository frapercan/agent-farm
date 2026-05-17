"""Sanity tests for scripts/apply-branch-protection.sh (FARM-1.2).

Network-free: we only exercise the inline Python body builder by
extracting it from the shell script and running it in-process. We do
NOT invoke gh; the apply path is tested manually via the dry-run output
log in state/logs/branch-protection-<date>.log.
"""

from __future__ import annotations

import json
import re
import subprocess
import textwrap
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "apply-branch-protection.sh"


def _extract_build_body_python() -> str:
    """Pull the Python heredoc that build_body() uses out of the shell script."""
    text = SCRIPT.read_text(encoding="utf-8")
    match = re.search(
        r"python3 - \"\$contexts\" <<'PY'\n(.*?)\nPY",
        text,
        re.DOTALL,
    )
    assert match is not None, "could not find build_body python heredoc"
    return match.group(1)


def _run_build_body(contexts: str) -> dict:
    src = _extract_build_body_python()
    proc = subprocess.run(
        ["python3", "-c", src, contexts],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


def test_build_body_shape_with_single_context() -> None:
    body = _run_build_body("integration (3.12, 2.1.0)\n")
    assert body["required_status_checks"]["contexts"] == ["integration (3.12, 2.1.0)"]
    assert body["required_status_checks"]["strict"] is False
    assert body["enforce_admins"] is True
    assert body["required_pull_request_reviews"]["dismiss_stale_reviews"] is True
    assert body["required_pull_request_reviews"]["required_approving_review_count"] == 0
    assert body["restrictions"] is None
    assert body["allow_force_pushes"] is False
    assert body["allow_deletions"] is False
    assert body["required_conversation_resolution"] is False
    assert body["required_linear_history"] is False


def test_build_body_preserves_multi_context_order() -> None:
    contexts = "lint (3.12, 2.1.0)\ntest (3.12, 2.1.0)\nintegration (3.12, 2.1.0)\n"
    body = _run_build_body(contexts)
    assert body["required_status_checks"]["contexts"] == [
        "lint (3.12, 2.1.0)",
        "test (3.12, 2.1.0)",
        "integration (3.12, 2.1.0)",
    ]


def test_build_body_handles_empty_context_list() -> None:
    body = _run_build_body("")
    assert body["required_status_checks"]["contexts"] == []


def test_script_targets_cover_pr_base_repos() -> None:
    """Every repo in scripts/lib/pr_base.py REPO_BASE (except cafaeval-protea
    which we deliberately skip) must appear at least once in TARGETS."""
    text = SCRIPT.read_text(encoding="utf-8")
    targets_block = re.search(r"TARGETS=\(\n(.*?)\n\)", text, re.DOTALL)
    assert targets_block is not None
    repos_in_script = set()
    for line in targets_block.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped.startswith('"'):
            continue
        # First field of the quoted row.
        match = re.match(r'"\s*(\S+)', stripped)
        if match:
            repos_in_script.add(match.group(1))

    pr_base_path = Path(__file__).resolve().parents[1] / "scripts" / "lib" / "pr_base.py"
    pr_base_text = pr_base_path.read_text(encoding="utf-8")
    pr_base_repos: set[str] = set()
    table_match = re.search(r"REPO_BASE:\s*dict\[str, str\] = \{(.*?)\n\}", pr_base_text, re.DOTALL)
    assert table_match is not None
    for line in table_match.group(1).splitlines():
        m = re.match(r'\s*"([A-Za-z0-9_.-]+)"\s*:', line)
        if m:
            pr_base_repos.add(m.group(1))

    expected = pr_base_repos - {"cafaeval-protea"}
    missing = expected - repos_in_script
    assert not missing, f"TARGETS missing repos from pr_base: {missing}"


def test_script_default_mode_is_dry_run() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    # Look for the case block that maps "" to dry-run; this guards against
    # an accidental flip to --apply default.
    assert re.search(r'""\)\s*MODE="dry-run"', text), (
        "default mode must be dry-run; the empty-args case must map to dry-run"
    )

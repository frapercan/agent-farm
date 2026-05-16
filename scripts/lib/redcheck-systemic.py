#!/usr/bin/env python3
"""redcheck-systemic — detect systemic red-check patterns across PRs (FARM-1.5).

When the same required check fails on >=3 open PRs across the stack, the
failure is infra-systemic (workflow misconfig, dependency outage, secrets
expiration). A janitor pushing trivial fixes to each PR is wrong: only
the systemic fix PR may justify an admin override. Without this rule the
janitor wastes tokens cycling failures.

Usage:
    python3 scripts/lib/redcheck-systemic.py [--threshold 3] [--repos PROTEA,thesis,...]
        [--owner frapercan] [--json] [--pretty]

The default behaviour reads open PRs across the canonical stack
(REPO_BASE in pr_base.py) via `gh api`, parses each PR's
`statusCheckRollup`, groups failing check names, and emits a JSON
mapping `{ check_name: [ "owner/repo#N", ... ] }` for every check whose
failure list has >= threshold entries. The mapping is empty if no
systemic failure exists.

Exit codes:
    0   no systemic failure detected
    1   at least one systemic failure flagged (callers can treat this as
        a "do not push individual fixes" signal)
    2   usage / underlying gh failure

The module is intentionally tool-agnostic on transport: tests inject a
fake `gh_runner` callable so the threshold logic can be exercised
without spawning subprocesses.

Memory: feedback_janitor_systemic_redcheck_carveout.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Callable, Iterable, Sequence

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import pr_base  # noqa: E402  (sibling module, sys.path tweak above)

# Default repos to sweep. Drops cafaeval-protea (rarely active) but
# keeps the seven PROTEA stack repos plus the two meta repos. Callers
# can override with --repos.
DEFAULT_REPOS: tuple[str, ...] = (
    "PROTEA",
    "protea-contracts",
    "protea-method",
    "protea-sources",
    "protea-runners",
    "protea-backends",
    "protea-reranker-lab",
    "agent-farm",
    "thesis",
)

DEFAULT_OWNER = "frapercan"
DEFAULT_THRESHOLD = 3

# Conclusion / state strings that indicate a check is currently red.
# `gh` exposes both check_run (FAILURE/CANCELLED/TIMED_OUT) and status
# context shapes (state=ERROR/FAILURE). We treat all of these as failing.
FAILING_CONCLUSIONS: frozenset[str] = frozenset(
    {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STALE"}
)
FAILING_STATES: frozenset[str] = frozenset({"FAILURE", "ERROR"})

GhRunner = Callable[[Sequence[str]], str]


# ---------------------------------------------------------------------------
# gh transport
# ---------------------------------------------------------------------------


def _default_gh_runner(args: Sequence[str]) -> str:
    """Run `gh <args>` and return stdout text. Raises on non-zero exit."""
    if shutil.which("gh") is None:
        raise RuntimeError(
            "gh CLI not found on PATH; install GitHub CLI to use redcheck-systemic"
        )
    proc = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"gh {' '.join(args)} failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout


# ---------------------------------------------------------------------------
# Pure logic (tested directly)
# ---------------------------------------------------------------------------


def is_failing(check: dict) -> bool:
    """Return True iff a single statusCheckRollup entry is currently red.

    `gh` returns two shapes:
      - check_run:  {"__typename": "CheckRun", "name": "...",
                     "conclusion": "FAILURE", "status": "COMPLETED"}
      - status:     {"__typename": "StatusContext", "context": "...",
                     "state": "FAILURE"}

    Pending / in-progress / neutral entries are NOT failing. Treating
    them as failing would noise up the systemic detector.
    """
    conclusion = (check.get("conclusion") or "").upper()
    state = (check.get("state") or "").upper()
    status = (check.get("status") or "").upper()

    # CheckRun: only count as failing once the run is COMPLETED with a
    # failing conclusion. In-progress runs are not yet red.
    if conclusion:
        if status and status != "COMPLETED":
            return False
        return conclusion in FAILING_CONCLUSIONS

    # StatusContext: state is terminal by construction.
    if state:
        return state in FAILING_STATES

    return False


def check_name(check: dict) -> str:
    """Best-effort canonical name for a status check.

    For check_run entries we use `name`; for status contexts the field
    is `context`. We fall back to `<unnamed>` rather than dropping the
    record, so a misshapen API response surfaces visibly.
    """
    return check.get("name") or check.get("context") or "<unnamed>"


def group_failures(
    prs: Iterable[dict], owner: str
) -> dict[str, list[str]]:
    """Return `{check_name: [owner/repo#N, ...]}` for every failing check.

    `prs` is an iterable of dicts shaped like the rows returned by
    `gh pr list --json number,repository,statusCheckRollup`. We
    normalise repository slugs via `pr_base.lookup` only to ensure the
    repo is in the canonical table; unknown repos are kept (they just
    won't have a canonical base associated).
    """
    groups: dict[str, list[str]] = defaultdict(list)
    for pr in prs:
        number = pr.get("number")
        repo_info = pr.get("repository") or {}
        repo_name = repo_info.get("name") or pr.get("_repo")
        repo_owner = (repo_info.get("owner") or {}).get("login") or owner
        if not number or not repo_name:
            continue
        slug = f"{repo_owner}/{repo_name}#{number}"
        seen: set[str] = set()
        for check in pr.get("statusCheckRollup") or []:
            if not is_failing(check):
                continue
            name = check_name(check)
            # Dedup within a single PR: a name appearing twice on one
            # PR (rerun rows) must not inflate the systemic count.
            if name in seen:
                continue
            seen.add(name)
            groups[name].append(slug)
    return dict(groups)


def systemic(
    failures: dict[str, list[str]], threshold: int = DEFAULT_THRESHOLD
) -> dict[str, list[str]]:
    """Filter `failures` to checks with at least `threshold` affected PRs."""
    if threshold < 1:
        raise ValueError(f"threshold must be >= 1, got {threshold}")
    return {
        name: sorted(prs)
        for name, prs in failures.items()
        if len(prs) >= threshold
    }


# ---------------------------------------------------------------------------
# gh-backed sweep
# ---------------------------------------------------------------------------


def fetch_open_prs(
    repo: str,
    owner: str = DEFAULT_OWNER,
    gh_runner: GhRunner = _default_gh_runner,
) -> list[dict]:
    """Return open PRs for `owner/repo` with statusCheckRollup populated."""
    raw = gh_runner(
        [
            "pr",
            "list",
            "-R",
            f"{owner}/{repo}",
            "--state",
            "open",
            "--json",
            "number,statusCheckRollup",
            "--limit",
            "100",
        ]
    )
    try:
        prs = json.loads(raw or "[]")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"gh returned invalid JSON for {owner}/{repo}: {e}") from e
    # Inject the repo slug so downstream `group_failures` can read it
    # without an extra API round-trip per PR.
    for pr in prs:
        pr.setdefault("repository", {"name": repo, "owner": {"login": owner}})
    return prs


def sweep(
    repos: Sequence[str] = DEFAULT_REPOS,
    owner: str = DEFAULT_OWNER,
    threshold: int = DEFAULT_THRESHOLD,
    gh_runner: GhRunner = _default_gh_runner,
) -> dict[str, list[str]]:
    """Sweep `repos` and return the systemic-failure mapping."""
    all_prs: list[dict] = []
    for repo in repos:
        try:
            all_prs.extend(fetch_open_prs(repo, owner=owner, gh_runner=gh_runner))
        except RuntimeError as e:
            # A single repo failure must not nuke the whole sweep; we
            # surface it on stderr but continue. The janitor still gets
            # a useful answer for the other repos.
            print(f"redcheck-systemic: {e}", file=sys.stderr)
    failures = group_failures(all_prs, owner=owner)
    return systemic(failures, threshold=threshold)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="redcheck-systemic",
        description=(
            "Detect systemic red-check patterns across open PRs. Exits 1 "
            "if any check is red on >= threshold PRs (and 0 if not)."
        ),
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"min PRs sharing a red check before it counts as systemic (default {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--repos",
        default=",".join(DEFAULT_REPOS),
        help="comma-separated repo names (defaults to the canonical stack)",
    )
    parser.add_argument(
        "--owner",
        default=DEFAULT_OWNER,
        help=f"GitHub owner/org (default {DEFAULT_OWNER})",
    )
    parser.add_argument(
        "--json",
        dest="emit_json",
        action="store_true",
        help="emit raw JSON (default behaviour)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="emit a human-readable summary instead of JSON",
    )
    return parser.parse_args(argv)


def _format_pretty(result: dict[str, list[str]]) -> str:
    if not result:
        return "redcheck-systemic: no systemic failures detected."
    lines = ["redcheck-systemic: SYSTEMIC failures detected:"]
    for name, prs in sorted(result.items()):
        lines.append(f"  - {name} ({len(prs)} PRs):")
        for slug in prs:
            lines.append(f"      * {slug}")
    lines.append(
        "ACTION: do NOT push individual fixes. Open a meta-issue on "
        "frapercan/agent-farm and stop."
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    if not repos:
        print("redcheck-systemic: --repos resolved to empty list", file=sys.stderr)
        return 2
    try:
        result = sweep(
            repos=repos,
            owner=args.owner,
            threshold=args.threshold,
        )
    except RuntimeError as e:
        print(f"redcheck-systemic: {e}", file=sys.stderr)
        return 2

    if args.pretty:
        print(_format_pretty(result))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))

    # Cite the canonical table so callers can sanity check the universe
    # we swept. Only emitted on stderr in pretty mode.
    if args.pretty and result:
        known = ", ".join(pr_base.known_repos())
        print(f"\n(canonical stack: {known})", file=sys.stderr)

    return 1 if result else 0


if __name__ == "__main__":
    raise SystemExit(main())

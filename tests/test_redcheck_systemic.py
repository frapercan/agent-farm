"""Tests for scripts/lib/redcheck-systemic.py (FARM-1.5).

Covers:
- is_failing() classifies CheckRun + StatusContext shapes correctly
- check_name() picks `name` for check_runs and `context` for statuses
- group_failures() builds the {check_name: [owner/repo#N]} mapping
- group_failures() deduplicates within a single PR
- systemic() threshold logic:
    * zero PRs failing same check -> empty
    * 2 PRs failing same check (below threshold) -> empty
    * 3 PRs failing same check -> flagged
    * distinct checks across different PRs -> empty
    * mix of resolved + failing checks -> only counts active failures
- sweep() wires gh_runner injection (no live gh calls)
- CLI emits JSON on --json, exits 0 when clean, 1 when systemic
- Janitor prompt cites the helper (acceptance: wire-in)
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "lib" / "redcheck-systemic.py"
PROMPT_PATH = REPO_ROOT / "prompts" / "janitor.md"


# The module name has a dash, so a plain `import` will not work. Load
# it from the file path under a sanitised module name.
def _load_module():
    spec = importlib.util.spec_from_file_location("redcheck_systemic", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rs = _load_module()


# ---------------------------------------------------------------------------
# is_failing()
# ---------------------------------------------------------------------------


class TestIsFailing:
    def test_check_run_failure_completed(self) -> None:
        assert rs.is_failing(
            {"__typename": "CheckRun", "conclusion": "FAILURE", "status": "COMPLETED"}
        )

    def test_check_run_failure_in_progress_is_not_failing(self) -> None:
        # An in-progress run that happens to carry a stale conclusion
        # should NOT count yet; only completed runs are red.
        assert not rs.is_failing(
            {"conclusion": "FAILURE", "status": "IN_PROGRESS"}
        )

    def test_check_run_success_is_not_failing(self) -> None:
        assert not rs.is_failing(
            {"conclusion": "SUCCESS", "status": "COMPLETED"}
        )

    def test_check_run_skipped_is_not_failing(self) -> None:
        assert not rs.is_failing(
            {"conclusion": "SKIPPED", "status": "COMPLETED"}
        )

    def test_check_run_cancelled_is_failing(self) -> None:
        assert rs.is_failing(
            {"conclusion": "CANCELLED", "status": "COMPLETED"}
        )

    def test_check_run_timed_out_is_failing(self) -> None:
        assert rs.is_failing(
            {"conclusion": "TIMED_OUT", "status": "COMPLETED"}
        )

    def test_status_context_failure(self) -> None:
        assert rs.is_failing(
            {"__typename": "StatusContext", "state": "FAILURE"}
        )

    def test_status_context_error(self) -> None:
        assert rs.is_failing({"state": "ERROR"})

    def test_status_context_success_not_failing(self) -> None:
        assert not rs.is_failing({"state": "SUCCESS"})

    def test_status_context_pending_not_failing(self) -> None:
        assert not rs.is_failing({"state": "PENDING"})

    def test_empty_dict_not_failing(self) -> None:
        assert not rs.is_failing({})


# ---------------------------------------------------------------------------
# check_name()
# ---------------------------------------------------------------------------


class TestCheckName:
    def test_uses_name_for_check_run(self) -> None:
        assert rs.check_name({"name": "ruff", "context": "ignored"}) == "ruff"

    def test_uses_context_for_status(self) -> None:
        assert rs.check_name({"context": "ci/circleci"}) == "ci/circleci"

    def test_unnamed_fallback(self) -> None:
        assert rs.check_name({}) == "<unnamed>"


# ---------------------------------------------------------------------------
# group_failures() + systemic()
# ---------------------------------------------------------------------------


def _pr(repo: str, number: int, checks: list[dict], owner: str = "frapercan") -> dict:
    return {
        "number": number,
        "repository": {"name": repo, "owner": {"login": owner}},
        "statusCheckRollup": checks,
    }


def _fail(name: str) -> dict:
    return {"name": name, "conclusion": "FAILURE", "status": "COMPLETED"}


def _pass(name: str) -> dict:
    return {"name": name, "conclusion": "SUCCESS", "status": "COMPLETED"}


class TestGroupFailures:
    def test_zero_prs(self) -> None:
        assert rs.group_failures([], owner="frapercan") == {}

    def test_no_failing_checks(self) -> None:
        prs = [_pr("PROTEA", 1, [_pass("ruff"), _pass("mypy")])]
        assert rs.group_failures(prs, owner="frapercan") == {}

    def test_one_failing_pr_one_check(self) -> None:
        prs = [_pr("PROTEA", 1, [_fail("ruff")])]
        assert rs.group_failures(prs, owner="frapercan") == {
            "ruff": ["frapercan/PROTEA#1"]
        }

    def test_three_prs_same_check(self) -> None:
        prs = [
            _pr("PROTEA", 1, [_fail("ruff")]),
            _pr("protea-method", 2, [_fail("ruff")]),
            _pr("agent-farm", 3, [_fail("ruff")]),
        ]
        grouped = rs.group_failures(prs, owner="frapercan")
        assert sorted(grouped["ruff"]) == [
            "frapercan/PROTEA#1",
            "frapercan/agent-farm#3",
            "frapercan/protea-method#2",
        ]

    def test_dedupe_within_single_pr(self) -> None:
        # Same check shows up twice on the same PR (e.g. matrix rerun);
        # must not be counted twice toward systemic threshold.
        prs = [_pr("PROTEA", 1, [_fail("ruff"), _fail("ruff")])]
        grouped = rs.group_failures(prs, owner="frapercan")
        assert grouped["ruff"] == ["frapercan/PROTEA#1"]

    def test_mix_resolved_and_failing(self) -> None:
        prs = [
            _pr("PROTEA", 1, [_fail("ruff"), _pass("mypy")]),
            _pr("PROTEA", 2, [_pass("ruff"), _fail("mypy")]),
        ]
        grouped = rs.group_failures(prs, owner="frapercan")
        assert grouped == {
            "ruff": ["frapercan/PROTEA#1"],
            "mypy": ["frapercan/PROTEA#2"],
        }

    def test_status_context_shape(self) -> None:
        # A status (not a check_run) should still be grouped by `context`.
        prs = [
            {
                "number": 7,
                "repository": {"name": "PROTEA", "owner": {"login": "frapercan"}},
                "statusCheckRollup": [
                    {"context": "ci/circleci", "state": "FAILURE"},
                ],
            }
        ]
        grouped = rs.group_failures(prs, owner="frapercan")
        assert grouped == {"ci/circleci": ["frapercan/PROTEA#7"]}


class TestSystemic:
    def test_zero_prs_failing_same_check_returns_empty(self) -> None:
        assert rs.systemic({}, threshold=3) == {}

    def test_below_threshold_returns_empty(self) -> None:
        failures = {"ruff": ["frapercan/PROTEA#1", "frapercan/PROTEA#2"]}
        assert rs.systemic(failures, threshold=3) == {}

    def test_at_threshold_flagged(self) -> None:
        failures = {
            "ruff": [
                "frapercan/PROTEA#1",
                "frapercan/PROTEA#2",
                "frapercan/protea-method#5",
            ]
        }
        result = rs.systemic(failures, threshold=3)
        assert "ruff" in result
        assert len(result["ruff"]) == 3

    def test_above_threshold_flagged(self) -> None:
        failures = {
            "ruff": [
                "frapercan/PROTEA#1",
                "frapercan/PROTEA#2",
                "frapercan/PROTEA#3",
                "frapercan/PROTEA#4",
            ]
        }
        assert "ruff" in rs.systemic(failures, threshold=3)

    def test_distinct_checks_across_prs_returns_empty(self) -> None:
        failures = {
            "ruff": ["frapercan/PROTEA#1"],
            "mypy": ["frapercan/PROTEA#2"],
            "pytest": ["frapercan/PROTEA#3"],
        }
        assert rs.systemic(failures, threshold=3) == {}

    def test_partial_systemic_only_returns_flagged(self) -> None:
        # Three PRs share ruff, one PR alone fails mypy. Only ruff
        # crosses the threshold; mypy must be dropped from the result.
        failures = {
            "ruff": [
                "frapercan/PROTEA#1",
                "frapercan/PROTEA#2",
                "frapercan/PROTEA#3",
            ],
            "mypy": ["frapercan/PROTEA#4"],
        }
        result = rs.systemic(failures, threshold=3)
        assert "ruff" in result
        assert "mypy" not in result

    def test_threshold_one_flags_anything(self) -> None:
        failures = {"ruff": ["frapercan/PROTEA#1"]}
        assert rs.systemic(failures, threshold=1) == {
            "ruff": ["frapercan/PROTEA#1"]
        }

    def test_threshold_zero_rejected(self) -> None:
        with pytest.raises(ValueError):
            rs.systemic({}, threshold=0)

    def test_sorts_pr_list_for_stable_output(self) -> None:
        # Unsorted input order should not appear in the output. Janitors
        # diff this output across sweeps to detect regressions, so order
        # must be deterministic.
        failures = {
            "ruff": [
                "frapercan/protea-method#9",
                "frapercan/PROTEA#1",
                "frapercan/agent-farm#3",
            ]
        }
        result = rs.systemic(failures, threshold=3)
        assert result["ruff"] == sorted(failures["ruff"])


# ---------------------------------------------------------------------------
# sweep() — gh_runner injection
# ---------------------------------------------------------------------------


class FakeGh:
    """Records args and returns canned JSON responses keyed by repo."""

    def __init__(self, by_repo: dict[str, list[dict]]) -> None:
        self.by_repo = by_repo
        self.calls: list[list[str]] = []

    def __call__(self, args):
        self.calls.append(list(args))
        # `args` looks like ["pr", "list", "-R", "frapercan/PROTEA", ...]
        for i, a in enumerate(args):
            if a == "-R" and i + 1 < len(args):
                owner_repo = args[i + 1]
                repo = owner_repo.split("/", 1)[1] if "/" in owner_repo else owner_repo
                return json.dumps(self.by_repo.get(repo, []))
        return "[]"


class TestSweep:
    def test_no_failing_prs(self) -> None:
        gh = FakeGh({"PROTEA": [_pr("PROTEA", 1, [_pass("ruff")])]})
        result = rs.sweep(repos=["PROTEA"], gh_runner=gh)
        assert result == {}

    def test_below_threshold_returns_empty(self) -> None:
        gh = FakeGh(
            {
                "PROTEA": [_pr("PROTEA", 1, [_fail("ruff")])],
                "protea-method": [_pr("protea-method", 2, [_fail("ruff")])],
            }
        )
        result = rs.sweep(repos=["PROTEA", "protea-method"], threshold=3, gh_runner=gh)
        assert result == {}

    def test_three_prs_flagged(self) -> None:
        gh = FakeGh(
            {
                "PROTEA": [_pr("PROTEA", 1, [_fail("ruff")])],
                "protea-method": [_pr("protea-method", 2, [_fail("ruff")])],
                "agent-farm": [_pr("agent-farm", 3, [_fail("ruff")])],
            }
        )
        result = rs.sweep(
            repos=["PROTEA", "protea-method", "agent-farm"],
            threshold=3,
            gh_runner=gh,
        )
        assert "ruff" in result
        assert len(result["ruff"]) == 3

    def test_distinct_checks_returns_empty(self) -> None:
        gh = FakeGh(
            {
                "PROTEA": [_pr("PROTEA", 1, [_fail("ruff")])],
                "protea-method": [_pr("protea-method", 2, [_fail("mypy")])],
                "agent-farm": [_pr("agent-farm", 3, [_fail("pytest")])],
            }
        )
        result = rs.sweep(
            repos=["PROTEA", "protea-method", "agent-farm"],
            threshold=3,
            gh_runner=gh,
        )
        assert result == {}

    def test_mix_resolved_and_failing(self) -> None:
        gh = FakeGh(
            {
                "PROTEA": [
                    _pr("PROTEA", 1, [_fail("ruff"), _pass("mypy")]),
                    _pr("PROTEA", 2, [_fail("ruff"), _pass("mypy")]),
                ],
                "protea-method": [
                    _pr("protea-method", 3, [_fail("ruff"), _pass("mypy")]),
                ],
            }
        )
        result = rs.sweep(
            repos=["PROTEA", "protea-method"], threshold=3, gh_runner=gh
        )
        # Only ruff is systemic across 3 PRs; mypy is green everywhere.
        assert "ruff" in result
        assert "mypy" not in result

    def test_runner_failure_does_not_abort_sweep(self, capsys) -> None:
        def flaky(args):
            for i, a in enumerate(args):
                if a == "-R" and i + 1 < len(args) and "broken" in args[i + 1]:
                    raise RuntimeError("gh blew up")
            return json.dumps([_pr("PROTEA", 1, [_fail("ruff")])])

        # Even though "broken-repo" raises, the sweep should still
        # process PROTEA and emit a (non-systemic) result.
        result = rs.sweep(
            repos=["broken-repo", "PROTEA"], threshold=1, gh_runner=flaky
        )
        assert "ruff" in result
        err = capsys.readouterr().err
        assert "gh blew up" in err

    def test_gh_called_per_repo(self) -> None:
        gh = FakeGh({})
        rs.sweep(repos=["PROTEA", "protea-method"], gh_runner=gh)
        assert len(gh.calls) == 2
        repos_called = [
            args[args.index("-R") + 1]
            for args in gh.calls
            if "-R" in args
        ]
        assert "frapercan/PROTEA" in repos_called
        assert "frapercan/protea-method" in repos_called


# ---------------------------------------------------------------------------
# CLI smoke
# ---------------------------------------------------------------------------


class TestCli:
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            capture_output=True,
            text=True,
            check=False,
            env={"PATH": "/nonexistent", **{}},
        )

    def test_no_gh_emits_warning_but_returns_empty(self) -> None:
        # With PATH stripped of gh, every repo lookup raises -> stderr
        # carries the failures, stdout carries {} (no systemic).
        res = self._run("--repos", "PROTEA")
        assert res.returncode == 0
        assert json.loads(res.stdout) == {}
        assert "gh CLI not found" in res.stderr or "gh " in res.stderr

    def test_empty_repos_list_rejected(self) -> None:
        res = self._run("--repos", "")
        assert res.returncode == 2
        assert "empty list" in res.stderr

    def test_pretty_mode_human_readable(self) -> None:
        # When pretty mode runs on empty (no gh, no systemic), the
        # script should print the friendly "no systemic" line.
        res = self._run("--repos", "PROTEA", "--pretty")
        assert res.returncode == 0
        assert "no systemic failures" in res.stdout


# ---------------------------------------------------------------------------
# Janitor prompt wire-in (acceptance: prompt cites the helper)
# ---------------------------------------------------------------------------


class TestJanitorPromptCarveOut:
    def _text(self) -> str:
        return PROMPT_PATH.read_text()

    def test_prompt_mentions_redcheck_systemic(self) -> None:
        assert "redcheck-systemic" in self._text()

    def test_prompt_has_carveout_section(self) -> None:
        text = self._text().lower()
        assert "systemic" in text
        assert "carve-out" in text or "carveout" in text

    def test_prompt_says_do_not_push_individual_fixes(self) -> None:
        text = self._text().lower()
        assert "do not push" in text or "do not fix" in text or "not push" in text

    def test_prompt_says_open_meta_issue(self) -> None:
        text = self._text()
        # The escalation channel is a meta-issue on agent-farm.
        assert "gh issue create" in text
        assert "frapercan/agent-farm" in text

    def test_prompt_cites_memory(self) -> None:
        text = self._text()
        assert "feedback_janitor_systemic_redcheck_carveout" in text

    def test_prompt_wires_into_startup(self) -> None:
        # The carve-out check must run BEFORE individual PR fixes; the
        # prompt should reference it in the sweep checklist, not just
        # in an isolated rules block.
        text = self._text()
        # We don't pin the exact wording but the helper has to appear
        # in the checklist area (between "Sweep checklist" and the next
        # major heading).
        try:
            checklist_idx = text.index("Sweep checklist")
        except ValueError:
            pytest.fail("janitor.md missing 'Sweep checklist' heading")
        # Find the next top-level section after the checklist.
        tail = text[checklist_idx:]
        end = tail.find("\n## ")
        section = tail if end == -1 else tail[:end]
        assert "redcheck-systemic" in section

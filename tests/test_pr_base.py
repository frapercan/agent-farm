"""Tests for scripts/lib/pr_base.py + pr-base.sh (FARM-1.3).

Covers:
- lookup() returns the canonical base for every known PROTEA stack repo
- lookup() returns 'main' for agent-farm and thesis
- lookup() tolerates owner/name slugs and `.git` suffixes
- lookup() is case-insensitive on a secondary pass
- lookup() raises UnknownRepoError on unknown repos (no silent fallback)
- extract_pr_refs() finds full URLs and owner/repo#N shortrefs
- extract_pr_refs() deduplicates and preserves order
- bash CLI `pr-base.sh lookup` exits 0/2 correctly
- bash CLI `pr-base.sh list` dumps the table
- the prompts/*.md files mention the canonical bases
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PR_BASE_PY = REPO_ROOT / "scripts" / "lib" / "pr_base.py"
PR_BASE_SH = REPO_ROOT / "scripts" / "lib" / "pr-base.sh"

# Make scripts/lib/ importable without installing the package.
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import pr_base  # noqa: E402  (sys.path manipulation above is intentional)


# ---------------------------------------------------------------------------
# lookup() — canonical table
# ---------------------------------------------------------------------------


class TestLookup:
    @pytest.mark.parametrize(
        "repo",
        [
            "PROTEA",
            "protea-contracts",
            "protea-method",
            "protea-sources",
            "protea-runners",
            "protea-backends",
            "protea-reranker-lab",
            "cafaeval-protea",
        ],
    )
    def test_protea_stack_targets_develop(self, repo: str) -> None:
        assert pr_base.lookup(repo) == "develop"

    @pytest.mark.parametrize("repo", ["agent-farm", "thesis"])
    def test_meta_repos_target_main(self, repo: str) -> None:
        assert pr_base.lookup(repo) == "main"

    def test_owner_slash_repo_form(self) -> None:
        assert pr_base.lookup("frapercan/PROTEA") == "develop"
        assert pr_base.lookup("frapercan/agent-farm") == "main"

    def test_git_suffix_tolerated(self) -> None:
        assert pr_base.lookup("frapercan/PROTEA.git") == "develop"
        assert pr_base.lookup("thesis.git") == "main"

    def test_case_insensitive_secondary(self) -> None:
        # Primary table is case-sensitive (PROTEA), but human typo `protea`
        # should still resolve via the secondary case-insensitive pass.
        assert pr_base.lookup("protea") == "develop"
        assert pr_base.lookup("Agent-Farm") == "main"

    def test_unknown_repo_raises(self) -> None:
        with pytest.raises(pr_base.UnknownRepoError):
            pr_base.lookup("some-unknown-thing")

    def test_no_silent_fallback_to_main(self) -> None:
        # This is the bug we're preventing. If we ever default-to-main,
        # every PROTEA stack PR slips onto main and the incident recurs.
        with pytest.raises(pr_base.UnknownRepoError):
            pr_base.lookup("not-a-real-repo")

    def test_table_covers_eight_stack_repos_plus_two_meta(self) -> None:
        # Sanity: if someone adds a repo without adding to REPO_BASE,
        # tests should catch the regression in their PR.
        assert len(pr_base.REPO_BASE) == 10
        assert sum(1 for v in pr_base.REPO_BASE.values() if v == "develop") == 8
        assert sum(1 for v in pr_base.REPO_BASE.values() if v == "main") == 2


# ---------------------------------------------------------------------------
# extract_pr_refs() — heartbeat / summary scanner
# ---------------------------------------------------------------------------


class TestExtractPrRefs:
    def test_finds_full_url(self) -> None:
        text = "Opened https://github.com/frapercan/PROTEA/pull/418 successfully."
        assert pr_base.extract_pr_refs(text) == [("frapercan", "PROTEA", 418)]

    def test_finds_shortref(self) -> None:
        text = "See frapercan/protea-method#77 for details."
        assert pr_base.extract_pr_refs(text) == [
            ("frapercan", "protea-method", 77)
        ]

    def test_deduplicates(self) -> None:
        text = (
            "https://github.com/frapercan/PROTEA/pull/1 "
            "https://github.com/frapercan/PROTEA/pull/1 "
            "and frapercan/PROTEA#1 again."
        )
        assert pr_base.extract_pr_refs(text) == [("frapercan", "PROTEA", 1)]

    def test_preserves_order(self) -> None:
        text = (
            "First https://github.com/frapercan/PROTEA/pull/10 "
            "then https://github.com/frapercan/agent-farm/pull/29."
        )
        assert pr_base.extract_pr_refs(text) == [
            ("frapercan", "PROTEA", 10),
            ("frapercan", "agent-farm", 29),
        ]

    def test_ignores_unrelated_text(self) -> None:
        assert pr_base.extract_pr_refs("nothing interesting here") == []

    def test_finds_multiple_owners(self) -> None:
        # Even though we only PR against frapercan today, the extractor
        # should not hardcode the owner.
        text = (
            "upstream other-user/some-repo#42 plus our own "
            "https://github.com/frapercan/PROTEA/pull/7"
        )
        refs = pr_base.extract_pr_refs(text)
        assert ("other-user", "some-repo", 42) in refs
        assert ("frapercan", "PROTEA", 7) in refs


# ---------------------------------------------------------------------------
# bash CLI
# ---------------------------------------------------------------------------


class TestBashCli:
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(PR_BASE_SH), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_lookup_known(self) -> None:
        res = self._run("lookup", "PROTEA")
        assert res.returncode == 0
        assert res.stdout.strip() == "develop"

    def test_lookup_meta(self) -> None:
        res = self._run("lookup", "agent-farm")
        assert res.returncode == 0
        assert res.stdout.strip() == "main"

    def test_lookup_unknown_exits_nonzero(self) -> None:
        res = self._run("lookup", "no-such-repo")
        assert res.returncode != 0
        assert "no canonical base" in res.stderr

    def test_list_dumps_table(self) -> None:
        res = self._run("list")
        assert res.returncode == 0
        assert "PROTEA\tdevelop" in res.stdout
        assert "agent-farm\tmain" in res.stdout

    def test_help_when_no_args(self) -> None:
        res = self._run()
        assert res.returncode == 0
        assert "pr-base.sh" in res.stdout

    def test_unknown_command(self) -> None:
        res = self._run("frobnicate")
        assert res.returncode != 0
        assert "unknown command" in res.stderr


# ---------------------------------------------------------------------------
# Prompt-layer guarantee
# ---------------------------------------------------------------------------


class TestPromptsCiteBases:
    """The slice acceptance criterion: every prompt that opens a PR must
    mention its canonical base explicitly. We grep for the literal token
    in the prompt body so future edits cannot silently regress to
    `gh pr create` without a base flag.
    """

    def test_executor_cites_develop(self) -> None:
        text = (REPO_ROOT / "prompts" / "executor.md").read_text()
        # Must show the literal flag-form somewhere, AND must enumerate
        # the canonical table.
        assert "-B develop" in text or "--base develop" in text
        assert "agent-farm" in text and "main" in text

    def test_doc_writer_cites_develop(self) -> None:
        text = (REPO_ROOT / "prompts" / "doc-writer.md").read_text()
        assert "-B develop" in text or "--base develop" in text

    def test_thesis_writer_cites_main(self) -> None:
        text = (REPO_ROOT / "prompts" / "thesis-writer.md").read_text()
        assert "-B main" in text or "--base main" in text

    def test_janitor_cites_canonical_table(self) -> None:
        text = (REPO_ROOT / "prompts" / "janitor.md").read_text()
        # Janitor mostly pushes to existing branches; we just need the
        # rule cited so when it does open a PR it picks the right base.
        assert "pr_base" in text or "canonical" in text.lower()


# ---------------------------------------------------------------------------
# scan CLI (used by finalize-subagent.sh)
# ---------------------------------------------------------------------------


class TestScanCli:
    def test_scan_stdin_emits_json(self) -> None:
        proc = subprocess.run(
            ["python3", str(PR_BASE_PY), "scan", "--stdin"],
            input="PR opened: https://github.com/frapercan/PROTEA/pull/99",
            capture_output=True,
            text=True,
            check=True,
        )
        import json

        out = json.loads(proc.stdout)
        assert out == [
            {
                "owner": "frapercan",
                "repo": "PROTEA",
                "number": 99,
                "expected_base": "develop",
            }
        ]

    def test_scan_inline_text(self) -> None:
        proc = subprocess.run(
            [
                "python3",
                str(PR_BASE_PY),
                "scan",
                "--text",
                "see frapercan/agent-farm#12 and frapercan/PROTEA#34",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        import json

        out = json.loads(proc.stdout)
        bases = {(x["repo"], x["expected_base"]) for x in out}
        assert ("agent-farm", "main") in bases
        assert ("PROTEA", "develop") in bases

    def test_scan_unknown_repo_emits_null(self) -> None:
        proc = subprocess.run(
            ["python3", str(PR_BASE_PY), "scan", "--text", "weird/repo#1"],
            capture_output=True,
            text=True,
            check=True,
        )
        import json

        out = json.loads(proc.stdout)
        assert out == [
            {
                "owner": "weird",
                "repo": "repo",
                "number": 1,
                "expected_base": None,
            }
        ]

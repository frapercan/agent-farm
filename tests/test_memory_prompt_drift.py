"""Tests for scripts/memory-prompt-drift.py.

Covers:
- Fixture: stale entry when prompt lacks required phrase.
- Negative fixture: clean when prompt contains the phrase.
- Robustness: malformed memory file (no "How to apply") skipped, no crash.
- JSON mode output is valid and stale_count matches.
- Multiple How-to-apply styles (## heading, **bold**, etc.).
- File-reference pairing (update prompts/<file>).
- All-prompts fallback when no specific file is named.

Slice: FARM-2.6 (farm-platform loop).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "memory-prompt-drift.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "memory_prompt_drift", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_memory_file(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def make_prompt_file(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Core acceptance: stale vs clean
# ---------------------------------------------------------------------------


class TestStaleEntry:
    def test_stale_when_prompt_lacks_phrase(self, tmp_path: Path) -> None:
        """The acceptance fixture from FARM-2.6 spec:
        Memory says 'the prompt must include BAR_TOKEN in janitor.md';
        janitor.md does NOT contain BAR_TOKEN -> 1 stale entry.
        """
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        make_memory_file(
            mem_dir,
            "feedback_foo.md",
            "## How to apply\n\nThe prompt must include `BAR_TOKEN` in janitor.md\n",
        )
        make_prompt_file(prompts_dir, "janitor.md", "# janitor\n\nSome content.\n")

        result = mod.scan(memory_dir=mem_dir, prompts_dir=prompts_dir)
        assert result["stale_count"] == 1
        assert len(result["stale"]) == 1
        entry = result["stale"][0]
        assert "BAR_TOKEN" in entry["expected_phrase"]
        assert entry["prompt_file"] == "janitor.md"

    def test_clean_when_prompt_contains_phrase(self, tmp_path: Path) -> None:
        """Negative fixture: same setup but janitor.md includes BAR_TOKEN -> 0 stale."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        make_memory_file(
            mem_dir,
            "feedback_foo.md",
            "## How to apply\n\nThe prompt must include `BAR_TOKEN` in janitor.md\n",
        )
        make_prompt_file(
            prompts_dir,
            "janitor.md",
            "# janitor\n\nBAR_TOKEN is required here.\n",
        )

        result = mod.scan(memory_dir=mem_dir, prompts_dir=prompts_dir)
        assert result["stale_count"] == 0
        assert result["stale"] == []


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------


class TestRobustness:
    def test_malformed_no_how_to_apply_skipped(self, tmp_path: Path) -> None:
        """Memory file with no 'How to apply' section is skipped without crash."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        make_memory_file(
            mem_dir,
            "feedback_no_apply.md",
            "# Background\n\nThis memory file has no How to apply section.\n",
        )

        result = mod.scan(memory_dir=mem_dir, prompts_dir=prompts_dir)
        assert result["stale_count"] == 0
        assert result["memory_files_scanned"] == 1  # file was read, just skipped

    def test_empty_memory_dir(self, tmp_path: Path) -> None:
        """Empty memory dir produces zero stale entries, no crash."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        result = mod.scan(memory_dir=mem_dir, prompts_dir=prompts_dir)
        assert result["stale_count"] == 0
        assert result["memory_files_scanned"] == 0

    def test_missing_prompt_file_treated_as_stale(self, tmp_path: Path) -> None:
        """If the named prompt file doesn't exist, the phrase is treated as stale."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        make_memory_file(
            mem_dir,
            "feedback_bar.md",
            "## How to apply\n\nUpdate prompts/nonexistent.md with `SOME_TOKEN`.\n"
            "The prompt must include `SOME_TOKEN`.\n",
        )
        # nonexistent.md is NOT created in prompts_dir

        result = mod.scan(memory_dir=mem_dir, prompts_dir=prompts_dir)
        assert result["stale_count"] >= 1


# ---------------------------------------------------------------------------
# JSON mode
# ---------------------------------------------------------------------------


class TestJsonOutput:
    def test_json_valid_and_stale_count_matches(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """--json produces valid JSON; stale_count matches the stale list length."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        make_memory_file(
            mem_dir,
            "feedback_json_test.md",
            "## How to apply\n\nThe prompt must include `JSON_TEST_TOKEN`.\n",
        )
        make_prompt_file(prompts_dir, "executor.md", "# executor\n\nSome content.\n")

        rc = mod.main([
            "--memory-dir", str(mem_dir),
            "--prompts-dir", str(prompts_dir),
            "--json",
            "--quiet",
        ])
        assert rc == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "stale_count" in data
        assert "stale" in data
        assert data["stale_count"] == len(data["stale"])

    def test_quiet_suppresses_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """--quiet suppresses the human summary from stderr."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        rc = mod.main([
            "--memory-dir", str(mem_dir),
            "--prompts-dir", str(prompts_dir),
            "--quiet",
        ])
        assert rc == 0
        captured = capsys.readouterr()
        assert "memory-prompt drift" not in captured.err

    def test_default_has_human_summary(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Without --quiet, the human one-liner is present on stderr."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        rc = mod.main([
            "--memory-dir", str(mem_dir),
            "--prompts-dir", str(prompts_dir),
        ])
        assert rc == 0
        captured = capsys.readouterr()
        assert "memory-prompt drift" in captured.err


# ---------------------------------------------------------------------------
# Section heading styles
# ---------------------------------------------------------------------------


class TestHeadingStyles:
    """Verify that different 'How to apply' heading forms are all detected."""

    @pytest.mark.parametrize("heading", [
        "## How to apply",
        "### How to apply",
        "**How to apply:**",
        "**How to apply**",
        "**How to apply::**",
    ])
    def test_heading_style(self, tmp_path: Path, heading: str) -> None:
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        content = (
            f"{heading}\n\n"
            "The prompt must include `STYLE_TOKEN`.\n"
        )
        make_memory_file(mem_dir, "feedback_style.md", content)
        make_prompt_file(prompts_dir, "executor.md", "# no token here\n")

        result = mod.scan(memory_dir=mem_dir, prompts_dir=prompts_dir)
        assert result["stale_count"] == 1, (
            f"Heading '{heading}' was not detected; got stale_count=0"
        )


# ---------------------------------------------------------------------------
# File reference pairing
# ---------------------------------------------------------------------------


class TestFileReferencePairing:
    def test_update_prompts_file_reference(self, tmp_path: Path) -> None:
        """'Update prompts/janitor.md' directs the check to janitor.md only."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        make_memory_file(
            mem_dir,
            "feedback_ref.md",
            "## How to apply\n\n"
            "Update prompts/janitor.md so the no-stash rule lives next to a copy-pasteable alternative:\n"
            "The prompt must include `git worktree add`.\n",
        )
        # janitor.md does NOT contain the phrase
        make_prompt_file(prompts_dir, "janitor.md", "# janitor\n\nNo worktree add here.\n")
        # executor.md does contain it (should NOT cause a false negative)
        make_prompt_file(prompts_dir, "executor.md", "# executor\n\ngit worktree add example.\n")

        result = mod.scan(memory_dir=mem_dir, prompts_dir=prompts_dir)
        assert result["stale_count"] == 1
        entry = result["stale"][0]
        assert entry["prompt_file"] == "janitor.md"

    def test_file_reference_clean_when_present(self, tmp_path: Path) -> None:
        """No stale entry when the named file contains the phrase."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        make_memory_file(
            mem_dir,
            "feedback_ref_ok.md",
            "## How to apply\n\n"
            "Update prompts/janitor.md with the copy-pasteable alternative:\n"
            "The prompt must include `git worktree add`.\n",
        )
        make_prompt_file(
            prompts_dir,
            "janitor.md",
            "# janitor\n\ngit worktree add /tmp/baseline-$$ origin/develop\n",
        )

        result = mod.scan(memory_dir=mem_dir, prompts_dir=prompts_dir)
        assert result["stale_count"] == 0


# ---------------------------------------------------------------------------
# All-prompts fallback
# ---------------------------------------------------------------------------


class TestAllPromptsFallback:
    def test_found_in_any_prompt_is_clean(self, tmp_path: Path) -> None:
        """When no file is named, finding the phrase in ANY prompt = clean."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        make_memory_file(
            mem_dir,
            "feedback_no_file.md",
            "## How to apply\n\nThe prompt must include `SHARED_TOKEN`.\n",
        )
        make_prompt_file(prompts_dir, "conductor.md", "# conductor\n\nSHARED_TOKEN here.\n")
        make_prompt_file(prompts_dir, "executor.md", "# executor\n\nno token.\n")

        result = mod.scan(memory_dir=mem_dir, prompts_dir=prompts_dir)
        assert result["stale_count"] == 0

    def test_not_in_any_prompt_is_stale(self, tmp_path: Path) -> None:
        """When no file is named and phrase absent from all prompts -> stale."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        make_memory_file(
            mem_dir,
            "feedback_no_file.md",
            "## How to apply\n\nThe prompt must include `MISSING_EVERYWHERE`.\n",
        )
        make_prompt_file(prompts_dir, "executor.md", "# executor\n\nno token.\n")

        result = mod.scan(memory_dir=mem_dir, prompts_dir=prompts_dir)
        assert result["stale_count"] == 1
        assert result["stale"][0]["prompt_file"] is None

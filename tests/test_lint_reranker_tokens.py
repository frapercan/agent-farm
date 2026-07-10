"""Tests for scripts/lint-reranker-tokens.py.

Covers: allowlist semantics, word-boundary edge cases, file-extension
filtering, CLI exit codes, and the axis-tuple suggestion text.

Slice: FARM-EXP.6 (farm-platform loop).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "lint-reranker-tokens.py"
FIXTURES = Path(__file__).parent / "fixtures" / "lint_reranker_tokens"


# Load the script as a module so we can unit-test internals directly.
# The hyphen in the filename forbids a normal `import`.
def _load_module():
    spec = importlib.util.spec_from_file_location(
        "lint_reranker_tokens", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


linter = _load_module()


# ---------------------------------------------------------------------------
# Allowlist + regex unit tests
# ---------------------------------------------------------------------------


class TestAllowlist:
    def test_allowlist_has_exactly_ten_tokens(self) -> None:
        assert len(linter.GOA_ALLOWLIST) == 10

    def test_allowlist_exact_membership(self) -> None:
        expected = {
            "v160", "v200", "v210", "v215", "v220",
            "v225", "v226", "v227", "v229", "v230",
        }
        assert set(linter.GOA_ALLOWLIST) == expected

    def test_allowlist_excludes_v228(self) -> None:
        # v228 is a real GOA release but NOT in the slice spec; the
        # spec is the authority — flag it.
        assert "v228" not in linter.GOA_ALLOWLIST


class TestRegex:
    def test_matches_bare_token(self) -> None:
        assert linter.TOKEN_RE.findall("the v18 container") == ["v18"]

    def test_matches_at_line_boundaries(self) -> None:
        assert linter.TOKEN_RE.findall("v18") == ["v18"]
        assert linter.TOKEN_RE.findall("v9.") == ["v9"]

    def test_does_not_match_alpha_suffix(self) -> None:
        # `v18s` is a hypothetical plural — \d stops at `s`, then
        # \b fails because `s` is alnum. No match.
        assert linter.TOKEN_RE.findall("v18s plural") == []

    def test_does_not_match_underscore_neighbours(self) -> None:
        # `_` is a word character; the boundary fails on both sides.
        assert linter.TOKEN_RE.findall("service_v18") == []
        assert linter.TOKEN_RE.findall("v18_alias") == []

    def test_does_not_match_alpha_prefix(self) -> None:
        assert linter.TOKEN_RE.findall("av18") == []


# ---------------------------------------------------------------------------
# scan_file
# ---------------------------------------------------------------------------


class TestScanFile:
    def test_clean_file_with_allowlisted_tokens(self) -> None:
        offences = linter.scan_file(FIXTURES / "clean_allowlist.md")
        assert offences == []

    def test_dirty_file_flags_v18_and_v22(self) -> None:
        offences = linter.scan_file(FIXTURES / "dirty_v18_v22.md")
        tokens = [tok for _, _, tok in offences]
        assert tokens == ["v18", "v22"]
        # line numbers from the fixture: v18 on line 3, v22 on line 4.
        lines = [line for line, _, _ in offences]
        assert lines == [3, 4]

    def test_allowlist_boundary_v228_flagged(self) -> None:
        offences = linter.scan_file(FIXTURES / "allowlist_boundary.md")
        tokens = [tok for _, _, tok in offences]
        # v229 is allowlisted; v228 is not — exactly one offence.
        assert tokens == ["v228"]

    def test_word_boundary_fixture(self) -> None:
        offences = linter.scan_file(FIXTURES / "word_boundary.md")
        tokens = [tok for _, _, tok in offences]
        # `v18s` skipped, `v18.` matched, `v18 ` matched, `v9` matched.
        # That is three offences with tokens v18, v18, v9.
        assert tokens == ["v18", "v18", "v9"]

    # -- Q1: semver carve-out ------------------------------------------------

    def test_semver_file_is_clean(self) -> None:
        """Tokens like v2.1.13 and v0.3.0 must not fire."""
        offences = linter.scan_file(FIXTURES / "clean_semver.md")
        assert offences == [], offences

    def test_semver_inline(self) -> None:
        """Unit-level check: the carve-out fires for .digit suffix."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("Using eggNOG-mapper v2.1.13 for annotations.\n")
        try:
            offences = linter.scan_file(tmp)
            assert offences == [], f"Expected no offences; got {offences}"
        finally:
            tmp.unlink(missing_ok=True)

    def test_bare_v2_still_flagged(self) -> None:
        """A bare ``v2`` (no .digit following) must still be flagged."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("The re-ranker v2 model was used.\n")
        try:
            offences = linter.scan_file(tmp)
            tokens = [t for _, _, t in offences]
            assert "v2" in tokens
        finally:
            tmp.unlink(missing_ok=True)

    # -- Q2: bench-dataset carve-out -----------------------------------------

    def test_bench_dataset_file_is_clean(self) -> None:
        """Tokens like bench-v1-K5 must not fire."""
        offences = linter.scan_file(FIXTURES / "clean_bench_dataset.md")
        assert offences == [], offences

    def test_bench_prefix_inline(self) -> None:
        """Unit-level check: the carve-out fires for bench- prefix."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("Dataset bench-v1-K5-filtered was used.\n")
        try:
            offences = linter.scan_file(tmp)
            assert offences == [], f"Expected no offences; got {offences}"
        finally:
            tmp.unlink(missing_ok=True)

    def test_bare_v1_after_non_bench_still_flagged(self) -> None:
        """A bare ``v1`` not preceded by bench- must still be flagged."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("Re-ranker v1 trains on per-aspect data.\n")
        try:
            offences = linter.scan_file(tmp)
            tokens = [t for _, _, t in offences]
            assert "v1" in tokens
        finally:
            tmp.unlink(missing_ok=True)

    # -- Q4: LAFA-container (knn-) carve-out ---------------------------------

    def test_knn_container_prefix_inline(self) -> None:
        """Tokens like protea-knn-v1 / knn-v18 must not fire."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("The protea-knn-v1 image and knn-v18 ship to ghcr.\n")
        try:
            offences = linter.scan_file(tmp)
            assert offences == [], f"Expected no offences; got {offences}"
        finally:
            tmp.unlink(missing_ok=True)

    def test_bare_v1_after_non_knn_still_flagged(self) -> None:
        """A bare ``v1`` not preceded by knn- must still be flagged."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("Re-ranker v1 trains on per-aspect data.\n")
        try:
            offences = linter.scan_file(tmp)
            tokens = [t for _, _, t in offences]
            assert "v1" in tokens
        finally:
            tmp.unlink(missing_ok=True)

    # -- method-token allowlist (v6) -----------------------------------------

    def test_v6_method_token_allowed(self) -> None:
        """``v6`` (--no_v6 flag / "v6 features" stage) must not fire."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("Runs KNN + v6 features; pass --no_v6 to disable.\n")
        try:
            offences = linter.scan_file(tmp)
            assert offences == [], f"Expected no offences; got {offences}"
        finally:
            tmp.unlink(missing_ok=True)

    def test_bare_v22_still_flagged_with_v6_allowlist(self) -> None:
        """A reranker study version like ``v22`` must still be flagged."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("The re-ranker v22 lambdarank model.\n")
        try:
            offences = linter.scan_file(tmp)
            tokens = [t for _, _, t in offences]
            assert "v22" in tokens
        finally:
            tmp.unlink(missing_ok=True)

    # -- Q3: URL-path carve-out ----------------------------------------------

    def test_url_path_file_is_clean(self) -> None:
        """Tokens like /v1/jobs and /api/v1/jobs must not fire."""
        offences = linter.scan_file(FIXTURES / "clean_url_path.md")
        assert offences == [], offences

    def test_url_path_bare(self) -> None:
        """Bare slash-prefixed path: ``/v1/jobs`` must be carved out."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("POST /v1/jobs is the canonical entry.\n")
        try:
            offences = linter.scan_file(tmp)
            assert offences == [], f"Expected no offences; got {offences}"
        finally:
            tmp.unlink(missing_ok=True)

    def test_url_path_inside_backticks(self) -> None:
        """Inline code span ``/v1/jobs`` must be carved out."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("Use ``/v1/jobs`` to submit jobs.\n")
        try:
            offences = linter.scan_file(tmp)
            assert offences == [], f"Expected no offences; got {offences}"
        finally:
            tmp.unlink(missing_ok=True)

    def test_url_path_sphinx_http_directive(self) -> None:
        """``.. http:get:: /v1/jobs`` Sphinx directives must be carved out."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".rst"))
        tmp.write_text(".. http:get:: /v1/jobs\n.. http:post:: /v1/datasets\n")
        try:
            offences = linter.scan_file(tmp)
            assert offences == [], f"Expected no offences; got {offences}"
        finally:
            tmp.unlink(missing_ok=True)

    def test_url_path_nested_prefix(self) -> None:
        """Nested prefixes like ``/api/v1/jobs`` must be carved out."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("Internal alias: /api/v1/jobs (legacy).\n")
        try:
            offences = linter.scan_file(tmp)
            assert offences == [], f"Expected no offences; got {offences}"
        finally:
            tmp.unlink(missing_ok=True)

    def test_standalone_v1_still_flagged_after_q3(self) -> None:
        """Standalone ``v1`` (no leading slash) must still fire."""
        import tempfile, pathlib
        tmp = pathlib.Path(tempfile.mktemp(suffix=".md"))
        tmp.write_text("The v1 reranker was trained on per-aspect data.\n")
        try:
            offences = linter.scan_file(tmp)
            tokens = [t for _, _, t in offences]
            assert "v1" in tokens
        finally:
            tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Default-target walk + extension filter
# ---------------------------------------------------------------------------


class TestExtensionFilter:
    def test_default_walk_skips_non_prose_extensions(self) -> None:
        # Scanning the fixtures directory as a tree must skip the .py
        # fixture even though it contains `v18`.
        targets = linter.iter_scan_targets([FIXTURES])
        suffixes = {p.suffix.lower() for p in targets}
        assert ".py" not in suffixes
        # All targets are prose extensions
        assert suffixes.issubset(linter.PROSE_EXTENSIONS)

    def test_explicit_file_kept_regardless_of_extension(self) -> None:
        # When a caller names a file by hand, the linter trusts the
        # caller and scans it.
        targets = linter.iter_scan_targets([FIXTURES / "not_prose.py"])
        assert (FIXTURES / "not_prose.py") in targets

    def test_dedup(self) -> None:
        targets = linter.iter_scan_targets([
            FIXTURES / "clean_allowlist.md",
            FIXTURES / "clean_allowlist.md",
        ])
        assert len(targets) == 1


# ---------------------------------------------------------------------------
# main() exit codes
# ---------------------------------------------------------------------------


class TestMain:
    def test_exit_0_on_clean_file(self, capsys: pytest.CaptureFixture) -> None:
        rc = linter.main([str(FIXTURES / "clean_allowlist.md")])
        assert rc == 0

    def test_exit_1_on_dirty_file(self, capsys: pytest.CaptureFixture) -> None:
        rc = linter.main([str(FIXTURES / "dirty_v18_v22.md")])
        assert rc == 1
        captured = capsys.readouterr()
        assert "v18" in captured.err
        assert "v22" in captured.err

    def test_paths_flag_explicit_files(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        rc = linter.main([
            "--paths",
            str(FIXTURES / "clean_allowlist.md"),
            str(FIXTURES / "dirty_v18_v22.md"),
        ])
        assert rc == 1
        captured = capsys.readouterr()
        # Both files mentioned in offence lines (dirty file flagged).
        assert "dirty_v18_v22.md" in captured.err

    def test_suggestion_text_contains_axis_tuple_form(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        rc = linter.main([str(FIXTURES / "dirty_v18_v22.md")])
        assert rc == 1
        captured = capsys.readouterr()
        assert "axis-tuple" in captured.err
        # Allowlist is enumerated in the suggestion footer.
        assert "v226" in captured.err
        assert "v230" in captured.err

    def test_quiet_suppresses_footer_not_offences(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        rc = linter.main([
            "--quiet",
            str(FIXTURES / "dirty_v18_v22.md"),
        ])
        assert rc == 1
        captured = capsys.readouterr()
        # Offences still printed; suggestion footer suppressed.
        assert "v18" in captured.err
        assert "axis-tuple" not in captured.err


# ---------------------------------------------------------------------------
# CLI subprocess smoke test (covers shebang + permissions)
# ---------------------------------------------------------------------------


class TestSubprocess:
    def test_cli_exit_codes(self) -> None:
        # Clean
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH),
             str(FIXTURES / "clean_allowlist.md")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Dirty
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH),
             str(FIXTURES / "dirty_v18_v22.md")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "v18" in result.stderr

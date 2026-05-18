"""Tests for plans/render.py — SECTION_RX + discovery error paths + --check.

FARM-FEAT.9 acceptance: cover SECTION_RX matching, duplicate-id
failure, loop mismatch failure, --check stale detection.

The companion test_render_check.py focuses on the --check flag end-to-
end; this file zooms in on the parser internals (the regex itself, the
Slice.parse contract, the two SystemExit guards) so a regression to
either error path is caught with a precise failure rather than a
diffuse "render is wrong" symptom.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RENDER_PY = REPO_ROOT / "plans" / "render.py"

# Import the render module by path so tests work regardless of cwd.
sys.path.insert(0, str(REPO_ROOT / "plans"))
import render  # noqa: E402


# ---------------------------------------------------------------------------
# SECTION_RX matching
# ---------------------------------------------------------------------------


class TestSectionRx:
    def test_matches_minimal_slice(self) -> None:
        text = (
            "### S.1 minimal\n"
            "```yaml\n"
            "id: S.1\nphase: F\nloop: L\nstatus: pending\n"
            "```\n"
            "Body text.\n"
        )
        matches = list(render.SECTION_RX.finditer(text))
        assert len(matches) == 1
        title, frontmatter, body = matches[0].groups()
        assert title == "S.1 minimal"
        assert "id: S.1" in frontmatter
        assert "Body text." in body

    def test_matches_multiple_slices(self) -> None:
        text = (
            "# preamble\n\n"
            "### A.1 one\n"
            "```yaml\n"
            "id: A.1\nphase: F\nloop: L\nstatus: pending\n"
            "```\n"
            "First body.\n\n"
            "### A.2 two\n"
            "```yaml\n"
            "id: A.2\nphase: F\nloop: L\nstatus: done\n"
            "```\n"
            "Second body.\n"
        )
        matches = list(render.SECTION_RX.finditer(text))
        ids = [m.group(1).split()[0] for m in matches]
        assert ids == ["A.1", "A.2"]

    def test_skips_h2_and_h4_headings(self) -> None:
        # Only `### ` headings introduce slices; ## and #### are noise.
        text = (
            "## Not a slice\n\n"
            "```yaml\n"
            "id: NOPE\n"
            "```\n\n"
            "#### Also not a slice\n\n"
            "```yaml\n"
            "id: NOPE2\n"
            "```\n"
        )
        assert list(render.SECTION_RX.finditer(text)) == []

    def test_title_is_first_line_only(self) -> None:
        # SECTION_RX captures the title with a non-greedy ``.+?`` so a
        # following blank line cuts the capture short. The frontmatter
        # fence must come immediately after the title line.
        text = (
            "### A.1 first\n"
            "```yaml\n"
            "id: A.1\nphase: F\nloop: L\nstatus: pending\n"
            "```\n"
            "body\n"
        )
        matches = list(render.SECTION_RX.finditer(text))
        assert len(matches) == 1
        # No embedded newlines in the title capture.
        assert "\n" not in matches[0].group(1)

    def test_captures_body_up_to_next_section(self) -> None:
        text = (
            "### One slice\n"
            "```yaml\n"
            "id: A\nphase: F\nloop: L\nstatus: pending\n"
            "```\n"
            "Body for A continues here.\n"
            "Still A.\n\n"
            "### Two slice\n"
            "```yaml\n"
            "id: B\nphase: F\nloop: L\nstatus: pending\n"
            "```\n"
            "Body for B.\n"
        )
        matches = list(render.SECTION_RX.finditer(text))
        assert len(matches) == 2
        a_body = matches[0].group(3)
        assert "Body for A" in a_body
        assert "Still A" in a_body
        assert "Body for B" not in a_body

    def test_captures_body_up_to_end_of_file(self) -> None:
        text = (
            "### Last slice\n"
            "```yaml\n"
            "id: Z\nphase: F\nloop: L\nstatus: pending\n"
            "```\n"
            "Trailing body, no successor.\n"
        )
        matches = list(render.SECTION_RX.finditer(text))
        assert len(matches) == 1
        assert "Trailing body" in matches[0].group(3)


# ---------------------------------------------------------------------------
# Slice.parse contract
# ---------------------------------------------------------------------------


class TestSliceParse:
    def test_parse_minimal_frontmatter(self, tmp_path: Path) -> None:
        src = tmp_path / "PLAN.md"
        src.touch()
        s = render.Slice.parse(
            "A.1 first",
            "id: A.1\nphase: F\nloop: loop_a\nstatus: pending",
            "body",
            src,
        )
        assert s.id == "A.1"
        assert s.title == "A.1 first"
        assert s.loop == "loop_a"
        assert s.phase == "F"
        assert s.status == "pending"
        assert s.deps == []
        assert s.priority == "P2"  # default
        assert s.requires_human is False  # default

    def test_parse_full_frontmatter(self, tmp_path: Path) -> None:
        src = tmp_path / "PLAN.md"
        src.touch()
        s = render.Slice.parse(
            "X.1 the slice",
            (
                "id: X.1\nphase: F1\nloop: lp\nstatus: blocked\n"
                "deps: [Y.1, Z.2]\nacceptance: |\n  one line\nestimated_hours: 4\n"
                "priority: P0\ntags: [stability, ci]\nrequires_human: true\n"
            ),
            "free-form prose",
            src,
        )
        assert s.deps == ["Y.1", "Z.2"]
        assert s.acceptance.strip() == "one line"
        assert s.estimated_hours == 4
        assert s.priority == "P0"
        assert s.tags == ["stability", "ci"]
        assert s.requires_human is True

    def test_parse_strips_title_whitespace(self, tmp_path: Path) -> None:
        src = tmp_path / "PLAN.md"
        src.touch()
        s = render.Slice.parse(
            "  trailing space  ",
            "id: T.1\nphase: F\nloop: L\nstatus: pending",
            "",
            src,
        )
        assert s.title == "trailing space"


# ---------------------------------------------------------------------------
# discover() error paths
# ---------------------------------------------------------------------------


@pytest.fixture()
def render_fresh(tmp_path: Path):
    """Reload render with PLANS_DIR pointing at tmp_path so each test
    gets its own isolated plan store.
    """
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()
    # Pre-create one loop_dir per call so LOOP_DIRS isn't empty.

    def _reload(loop_dirs: list[Path]) -> object:
        # Reload from the module already imported above.
        mod = importlib.reload(render)
        mod.PLANS_DIR = plans_dir
        mod.LOOP_DIRS = loop_dirs
        mod.MASTER = plans_dir / "PLAN.md"
        return mod

    return _reload, plans_dir


class TestDiscoverDuplicateIdFails:
    def test_duplicate_id_in_same_loop_raises(
        self, render_fresh
    ) -> None:
        _reload, plans_dir = render_fresh
        loop = plans_dir / "loop_dup"
        loop.mkdir()
        (loop / "PLAN.md").write_text(
            "### DUP.1 first\n"
            "```yaml\n"
            "id: DUP.1\nphase: F\nloop: loop_dup\nstatus: pending\n"
            "```\n"
            "first body.\n\n"
            "### DUP.1 second\n"
            "```yaml\n"
            "id: DUP.1\nphase: F\nloop: loop_dup\nstatus: pending\n"
            "```\n"
            "second body.\n"
        )
        mod = _reload([loop])
        with pytest.raises(SystemExit) as exc:
            mod.discover()
        assert "duplicate slice id" in str(exc.value)
        assert "DUP.1" in str(exc.value)

    def test_duplicate_id_across_loops_raises(
        self, render_fresh
    ) -> None:
        _reload, plans_dir = render_fresh
        loop_a = plans_dir / "loop_a"
        loop_b = plans_dir / "loop_b"
        loop_a.mkdir()
        loop_b.mkdir()
        slice_block = (
            "### SHARED.1 in loop {name}\n"
            "```yaml\n"
            "id: SHARED.1\nphase: F\nloop: {name}\nstatus: pending\n"
            "```\n"
        )
        (loop_a / "PLAN.md").write_text(slice_block.format(name="loop_a"))
        (loop_b / "PLAN.md").write_text(slice_block.format(name="loop_b"))
        mod = _reload([loop_a, loop_b])
        with pytest.raises(SystemExit) as exc:
            mod.discover()
        assert "duplicate slice id" in str(exc.value)
        assert "SHARED.1" in str(exc.value)


class TestDiscoverLoopMismatchFails:
    def test_frontmatter_loop_must_match_dir_name(
        self, render_fresh
    ) -> None:
        _reload, plans_dir = render_fresh
        loop = plans_dir / "loop_real"
        loop.mkdir()
        (loop / "PLAN.md").write_text(
            "### W.1 wrong loop label\n"
            "```yaml\n"
            "id: W.1\nphase: F\nloop: loop_pretend\nstatus: pending\n"
            "```\n"
        )
        mod = _reload([loop])
        with pytest.raises(SystemExit) as exc:
            mod.discover()
        msg = str(exc.value)
        assert "W.1" in msg
        assert "loop_pretend" in msg
        assert "loop_real" in msg

    def test_correct_loop_label_passes(self, render_fresh) -> None:
        _reload, plans_dir = render_fresh
        loop = plans_dir / "loop_ok"
        loop.mkdir()
        (loop / "PLAN.md").write_text(
            "### OK.1 well-formed\n"
            "```yaml\n"
            "id: OK.1\nphase: F\nloop: loop_ok\nstatus: pending\n"
            "```\n"
        )
        mod = _reload([loop])
        slices = mod.discover()
        assert [s.id for s in slices] == ["OK.1"]


# ---------------------------------------------------------------------------
# --check stale detection (CLI smoke)
# ---------------------------------------------------------------------------


def _write_fixture_loop(plans_dir: Path, loop_name: str, slice_id: str,
                        status: str = "pending") -> None:
    loop = plans_dir / loop_name
    loop.mkdir()
    (loop / "PLAN.md").write_text(
        f"### {slice_id} fixture\n"
        f"```yaml\n"
        f"id: {slice_id}\nphase: F\nloop: {loop_name}\nstatus: {status}\n"
        f"```\n"
        f"body.\n"
    )


def _run_render(plans_dir: Path, *args: str) -> subprocess.CompletedProcess:
    """Run plans/render.py as a subprocess in a temp tree.

    We stage a tmp plans/ that mirrors the real layout (plans/<loop>/PLAN.md
    + render.py) so the script's module-level PLANS_DIR resolution lands
    inside tmp_path.
    """
    target = plans_dir / "render.py"
    if not target.exists():
        target.write_text(RENDER_PY.read_text())
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    return subprocess.run(
        [sys.executable, str(target), *args],
        check=False, capture_output=True, text=True, env=env,
    )


class TestCheckStaleDetection:
    def test_check_passes_when_plan_md_is_fresh(
        self, tmp_path: Path
    ) -> None:
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        _write_fixture_loop(plans_dir, "loop_a", "C.1")
        # First write the master.
        res_write = _run_render(plans_dir)
        assert res_write.returncode == 0, res_write.stderr
        # Then --check should agree it's fresh.
        res_check = _run_render(plans_dir, "--check")
        assert res_check.returncode == 0, res_check.stderr
        assert "up to date" in res_check.stdout

    def test_check_fails_when_plan_md_missing(
        self, tmp_path: Path
    ) -> None:
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        _write_fixture_loop(plans_dir, "loop_a", "C.2")
        # No master written; --check must fail.
        res = _run_render(plans_dir, "--check")
        assert res.returncode == 1
        assert "stale" in res.stderr

    def test_check_fails_when_loop_plan_modified(
        self, tmp_path: Path
    ) -> None:
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        _write_fixture_loop(plans_dir, "loop_a", "C.3", status="pending")
        # Render the master.
        assert _run_render(plans_dir).returncode == 0
        # Mutate the loop's PLAN.md so the master is now stale.
        loop_md = plans_dir / "loop_a" / "PLAN.md"
        loop_md.write_text(
            loop_md.read_text().replace("status: pending", "status: done")
        )
        res = _run_render(plans_dir, "--check")
        assert res.returncode == 1
        assert "stale" in res.stderr

    def test_check_fails_when_master_truncated(
        self, tmp_path: Path
    ) -> None:
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        _write_fixture_loop(plans_dir, "loop_a", "C.4")
        assert _run_render(plans_dir).returncode == 0
        # Corrupt the master and re-check.
        (plans_dir / "PLAN.md").write_text("partial\n")
        res = _run_render(plans_dir, "--check")
        assert res.returncode == 1
        assert "stale" in res.stderr

    def test_check_exits_zero_when_rerender_is_noop(
        self, tmp_path: Path
    ) -> None:
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        _write_fixture_loop(plans_dir, "loop_a", "C.5")
        _write_fixture_loop(plans_dir, "loop_b", "D.5")
        assert _run_render(plans_dir).returncode == 0
        # Two consecutive --check runs both pass — render is deterministic.
        for _ in range(2):
            res = _run_render(plans_dir, "--check")
            assert res.returncode == 0

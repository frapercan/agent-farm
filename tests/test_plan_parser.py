"""Tests for agent-farm plan_parser.py.

Covers the internal plan store (plans/<loop>/PLAN.md) walker: slice
discovery, schema enforcement (loop mismatch, duplicate id), the
cross-loop --next picker, sqlite executor task overlay, render_text,
and the legacy `parse_phases(plan_text)` compatibility shim.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.lib.plan_parser import (
    PHASE_HEADER_RE,
    PLAIN_ITEM_RE,
    SLICE_RE,
    Slice,
    discover_slices,
    fetch_task_status,
    find_next,
    group_by_phase,
    parse_phases,
    render_text,
)

FIXTURES = Path(__file__).parent / "fixtures"
PLANS_FIXTURE = FIXTURES / "plans"
DUP_FIXTURE = FIXTURES / "plans_dup"


# ---------------------------------------------------------------------------
# discover_slices — internal plan store walker
# ---------------------------------------------------------------------------


class TestDiscoverSlices:
    def test_walks_every_loop_and_reads_frontmatter(self) -> None:
        slices = discover_slices(PLANS_FIXTURE)
        ids = sorted(s.id for s in slices)
        assert ids == ["A.1", "A.2", "A.3", "A.4", "B.1", "B.2"]

    def test_loop_label_taken_from_directory(self) -> None:
        slices = discover_slices(PLANS_FIXTURE)
        by_id = {s.id: s for s in slices}
        assert by_id["A.1"].loop == "loop_a"
        assert by_id["B.1"].loop == "loop_b"

    def test_priority_and_requires_human_propagated(self) -> None:
        slices = discover_slices(PLANS_FIXTURE)
        by_id = {s.id: s for s in slices}
        assert by_id["A.1"].priority == "P0"
        assert by_id["A.4"].requires_human is True
        assert by_id["A.2"].requires_human is False

    def test_deps_are_lists(self) -> None:
        slices = discover_slices(PLANS_FIXTURE)
        by_id = {s.id: s for s in slices}
        assert by_id["A.2"].deps == ["A.1"]
        assert by_id["A.3"].deps == ["A.1", "MISSING.1"]
        assert by_id["A.1"].deps == []

    def test_duplicate_slice_id_rejected(self) -> None:
        with pytest.raises(SystemExit) as exc:
            discover_slices(DUP_FIXTURE)
        assert "duplicate slice id" in str(exc.value)
        assert "X.1" in str(exc.value)

    def test_loop_mismatch_rejected(self, tmp_path: Path) -> None:
        wrong = tmp_path / "loop_real"
        wrong.mkdir()
        (wrong / "PLAN.md").write_text(
            "### W.1 — wrong loop\n\n```yaml\nid: W.1\nphase: F1\n"
            "loop: somewhere_else\nstatus: pending\ndeps: []\n"
            "acceptance: x\npriority: P2\n```\n"
        )
        with pytest.raises(SystemExit) as exc:
            discover_slices(tmp_path)
        assert "declares loop=" in str(exc.value)


# ---------------------------------------------------------------------------
# find_next — cross-loop pickable selection
# ---------------------------------------------------------------------------


class TestFindNext:
    def test_picks_highest_priority_pickable_across_loops(self) -> None:
        slices = discover_slices(PLANS_FIXTURE)
        nxt = find_next(slices)
        # B.1 is P1 pickable; A.2 is P2 pickable; A.3 is P1 but blocked
        # on MISSING.1; A.4 is P0 but requires_human. Expect B.1.
        assert nxt is not None
        assert nxt["id"] == "B.1"
        assert nxt["loop"] == "loop_b"
        assert nxt["priority"] == "P1"

    def test_skips_requires_human_even_if_p0(self) -> None:
        slices = [
            Slice(id="X", title="t", loop="L", phase="F", status="pending",
                  priority="P0", requires_human=True),
            Slice(id="Y", title="t", loop="L", phase="F", status="pending",
                  priority="P2"),
        ]
        nxt = find_next(slices)
        assert nxt is not None
        assert nxt["id"] == "Y"

    def test_skips_slices_with_unmet_deps(self) -> None:
        slices = [
            Slice(id="A", title="t", loop="L", phase="F", status="pending",
                  deps=["MISSING"], priority="P0"),
            Slice(id="B", title="t", loop="L", phase="F", status="pending",
                  priority="P2"),
        ]
        nxt = find_next(slices)
        assert nxt is not None
        assert nxt["id"] == "B"

    def test_dep_done_unblocks(self) -> None:
        slices = [
            Slice(id="A", title="t", loop="L", phase="F", status="done",
                  priority="P0"),
            Slice(id="B", title="t", loop="L", phase="F", status="pending",
                  deps=["A"], priority="P0"),
        ]
        nxt = find_next(slices)
        assert nxt is not None
        assert nxt["id"] == "B"

    def test_returns_none_when_nothing_pickable(self) -> None:
        slices = [
            Slice(id="A", title="t", loop="L", phase="F", status="done",
                  priority="P0"),
            Slice(id="B", title="t", loop="L", phase="F", status="blocked",
                  priority="P0"),
        ]
        assert find_next(slices) is None

    def test_tie_break_priority_then_loop_then_phase_then_id(self) -> None:
        # Two slices same priority P1: tie-broken by loop alphabetical.
        slices = [
            Slice(id="B.1", title="t", loop="loop_z", phase="G",
                  status="pending", priority="P1"),
            Slice(id="A.1", title="t", loop="loop_a", phase="G",
                  status="pending", priority="P1"),
        ]
        nxt = find_next(slices)
        assert nxt is not None
        assert nxt["loop"] == "loop_a"

    def test_picks_across_two_loops_higher_priority_wins(self) -> None:
        # Stub two loops, one pending each, P1 should beat P2.
        slices = [
            Slice(id="A.1", title="loA p2", loop="loop_a", phase="F",
                  status="pending", priority="P2"),
            Slice(id="B.1", title="loB p1", loop="loop_b", phase="F",
                  status="pending", priority="P1"),
        ]
        nxt = find_next(slices)
        assert nxt is not None
        assert nxt["id"] == "B.1"
        assert nxt["priority"] == "P1"


# ---------------------------------------------------------------------------
# group_by_phase — JSON output shape compatibility
# ---------------------------------------------------------------------------


class TestGroupByPhase:
    def test_phase_grouping_preserves_order(self) -> None:
        slices = discover_slices(PLANS_FIXTURE)
        phases = group_by_phase(slices)
        phase_ids = [p["phase"] for p in phases]
        assert "F1" in phase_ids
        assert "F2" in phase_ids
        assert "G" in phase_ids

    def test_phase_dict_has_legacy_keys(self) -> None:
        slices = discover_slices(PLANS_FIXTURE)
        phases = group_by_phase(slices)
        for ph in phases:
            assert "phase" in ph
            assert "name" in ph
            assert "slices" in ph
            for s in ph["slices"]:
                # Existing JSON dashboards rely on these keys.
                assert "id" in s
                assert "title" in s
                assert "raw" in s  # legacy alias
                assert "loop" in s  # new per-slice loop label
                assert "status" in s
                assert "priority" in s


# ---------------------------------------------------------------------------
# fetch_task_status — sqlite executor history overlay
# ---------------------------------------------------------------------------


class TestFetchTaskStatus:
    @pytest.fixture
    def db_path(self, tmp_path: Path) -> str:
        p = tmp_path / "test.db"
        conn = sqlite3.connect(str(p))
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                agent_name TEXT,
                status TEXT,
                spawn_args TEXT,
                created_at TEXT,
                started_at TEXT,
                ended_at TEXT
            );
            INSERT INTO tasks VALUES
                ('exec-1', 'executor', 'succeeded', '{"slice":"A.1"}', '2026-05-01T00:00:00', '2026-05-01T00:00:00', '2026-05-01T01:00:00'),
                ('exec-2', 'executor', 'failed',    '{"slice":"A.2"}', '2026-05-01T02:00:00', '2026-05-01T02:00:00', '2026-05-01T02:30:00'),
                ('exec-3', 'executor', 'running',   '{"slice":"B.1"}', '2026-05-01T03:00:00', '2026-05-01T03:00:00', NULL),
                ('jan-1',  'janitor',  'succeeded', '{"slice":"J1.1"}', '2026-05-01T00:00:00', '2026-05-01T00:00:00', '2026-05-01T00:05:00');
            """
        )
        conn.commit()
        conn.close()
        return str(p)

    def test_returns_executor_only(self, db_path: str) -> None:
        state = fetch_task_status(db_path)
        assert "A.1" in state
        assert "A.2" in state
        assert "B.1" in state
        assert "J1.1" not in state

    def test_status_mapping(self, db_path: str) -> None:
        state = fetch_task_status(db_path)
        assert state["A.1"]["latest_status"] == "succeeded"
        assert state["A.2"]["latest_status"] == "failed"
        assert state["B.1"]["latest_status"] == "running"

    def test_takes_latest_by_timestamp(self, db_path: str) -> None:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO tasks VALUES ('exec-4', 'executor', 'succeeded', "
            "'{\"slice\":\"A.1\"}', '2026-05-02T00:00:00', "
            "'2026-05-02T00:00:00', '2026-05-02T01:00:00')"
        )
        conn.commit()
        conn.close()
        state = fetch_task_status(db_path)
        assert state["A.1"]["latest_task_id"] == "exec-4"
        assert state["A.1"]["count"] == 2

    def test_missing_spawn_args(self, db_path: str) -> None:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO tasks VALUES ('exec-5', 'executor', 'succeeded', "
            "NULL, '2026-05-01T00:00:00', NULL, NULL)"
        )
        conn.commit()
        conn.close()
        state = fetch_task_status(db_path)
        assert "A.1" in state  # no crash


# ---------------------------------------------------------------------------
# render_text — human progress table
# ---------------------------------------------------------------------------


class TestRenderText:
    def test_includes_priority_and_loop_columns(self) -> None:
        slices = discover_slices(PLANS_FIXTURE)
        out = render_text(slices, task_state={}, phase_filter=None)
        # Spot-check that priority + loop made it into the rendering.
        assert "[P0]" in out
        assert "(loop_a)" in out
        assert "(loop_b)" in out
        assert "A.1" in out

    def test_phase_filter(self) -> None:
        slices = discover_slices(PLANS_FIXTURE)
        out = render_text(slices, task_state={}, phase_filter="F2")
        assert "F2" in out
        assert "A.3" in out
        # B.1 lives under phase G; should be filtered out.
        assert "B.1" not in out

    def test_task_state_overlay(self) -> None:
        slices = [Slice(id="A.1", title="x", loop="L", phase="F", status="done")]
        out = render_text(slices, task_state={
            "A.1": {
                "latest_status": "succeeded",
                "latest_task_id": "tid-1",
                "latest_at": "2026-05-01",
                "count": 1,
            }
        }, phase_filter=None)
        assert "succeeded" in out
        assert "tid-1" in out


# ---------------------------------------------------------------------------
# legacy compatibility shims
# ---------------------------------------------------------------------------


class TestLegacyShims:
    def test_parse_phases_with_inline_markdown(self) -> None:
        text = (
            "### Inline.1 — title\n\n```yaml\nid: Inline.1\nphase: P\n"
            "status: pending\ndeps: []\nacceptance: ok\npriority: P2\n```\n"
        )
        phases = parse_phases(text)
        assert len(phases) == 1
        assert phases[0]["phase"] == "P"
        assert phases[0]["slices"][0]["id"] == "Inline.1"

    def test_parse_phases_with_plans_root(self) -> None:
        phases = parse_phases(PLANS_FIXTURE)
        all_ids = [s["id"] for ph in phases for s in ph["slices"]]
        assert "A.1" in all_ids
        assert "B.1" in all_ids

    def test_legacy_regex_constants_exported(self) -> None:
        # External tools grep for these; ensure they remain importable.
        assert PHASE_HEADER_RE.pattern
        assert SLICE_RE.pattern
        assert PLAIN_ITEM_RE.pattern


# ---------------------------------------------------------------------------
# CLI smoke
# ---------------------------------------------------------------------------


class TestCLISmoke:
    def test_json_output_shape(self, tmp_path: Path) -> None:
        from scripts.lib.plan_parser import main

        # Minimal sqlite db with the tasks schema.
        db = tmp_path / "tasks.sqlite"
        conn = sqlite3.connect(str(db))
        conn.executescript(
            "CREATE TABLE tasks (id TEXT, agent_name TEXT, status TEXT, "
            "spawn_args TEXT, created_at TEXT, started_at TEXT, "
            "ended_at TEXT);"
        )
        conn.commit()
        conn.close()

        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main([
                "--plans-root", str(PLANS_FIXTURE),
                "--db", str(db),
                "--json",
            ])
        assert rc == 0
        payload = json.loads(buf.getvalue())
        assert set(payload.keys()) >= {
            "phases", "task_state", "next", "slices_by_loop",
        }
        assert payload["slices_by_loop"]["loop_a"] == 4
        assert payload["slices_by_loop"]["loop_b"] == 2
        # next should be B.1 (P1 beats every other pickable)
        assert payload["next"]["id"] == "B.1"

    def test_next_flag_returns_zero_when_nothing_pickable(self, tmp_path: Path) -> None:
        from scripts.lib.plan_parser import main

        # Empty plan store: one loop dir with a PLAN.md that has no slices
        empty_root = tmp_path / "plans"
        loop_dir = empty_root / "no_slices_loop"
        loop_dir.mkdir(parents=True)
        (loop_dir / "PLAN.md").write_text("# no slices here\n")

        db = tmp_path / "tasks.sqlite"
        conn = sqlite3.connect(str(db))
        conn.executescript(
            "CREATE TABLE tasks (id TEXT, agent_name TEXT, status TEXT, "
            "spawn_args TEXT, created_at TEXT, started_at TEXT, "
            "ended_at TEXT);"
        )
        conn.commit()
        conn.close()

        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main([
                "--plans-root", str(empty_root),
                "--db", str(db),
                "--next",
            ])
        assert rc == 0
        assert "no pickable slices" in buf.getvalue()

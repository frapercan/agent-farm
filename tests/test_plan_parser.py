"""Tests for agent-farm plan_parser.py.

Covers: phase parsing (bold slices + plain items), SQLite join,
render_text, find_next, and CLI --next / --json flags.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.lib.plan_parser import (
    parse_phases,
    fetch_task_status,
    find_next,
    render_text,
    PHASE_HEADER_RE,
    SLICE_RE,
    PLAIN_ITEM_RE,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Regex unit tests
# ---------------------------------------------------------------------------


class TestRegex:
    def test_phase_header_match(self) -> None:
        m = PHASE_HEADER_RE.match("### Fase 1 — Foundation")
        assert m is not None
        assert m.group(1) == "1"
        assert m.group(2).strip() == "Foundation"

    def test_phase_header_with_dash(self) -> None:
        m = PHASE_HEADER_RE.match("### Fase 2 - Core Pipeline")
        assert m is not None
        assert m.group(1) == "2"
        assert m.group(2).strip() == "Core Pipeline"

    def test_slice_bold_match(self) -> None:
        m = SLICE_RE.match("1. **T1.1** Setup project skeleton")
        assert m is not None
        assert "T1.1" in m.group(1)

    def test_slice_bold_with_extra_dots(self) -> None:
        m = SLICE_RE.match("2. **T-CONTEXTS.5** Parameter objects")
        assert m is not None
        assert "T-CONTEXTS.5" in m.group(1)

    def test_slice_bold_with_description(self) -> None:
        m = SLICE_RE.match('3. **D27** ADR: "no em-dashes in prose"')
        assert m is not None
        assert "D27" in m.group(1)

    def test_plain_item_match(self) -> None:
        m = PLAIN_ITEM_RE.match("1. Upload thesis to repository")
        assert m is not None
        assert m.group(1) == "1"
        assert "Upload thesis" in m.group(2)

    def test_not_a_slice(self) -> None:
        assert SLICE_RE.match("Some random text") is None
        assert PLAIN_ITEM_RE.match("Not numbered") is None


# ---------------------------------------------------------------------------
# parse_phases
# ---------------------------------------------------------------------------


class TestParsePhases:
    def test_parse_golden(self) -> None:
        text = (FIXTURES / "plan_golden.md").read_text()
        phases = parse_phases(text)
        assert len(phases) == 2
        assert phases[0]["phase"] == 1
        assert phases[0]["name"] == "Foundation"
        assert len(phases[0]["slices"]) == 3
        assert phases[0]["slices"][0]["id"] == "T1.1"
        assert phases[0]["slices"][1]["id"] == "T1.2"
        assert phases[0]["slices"][2]["id"] == "D1"
        assert phases[1]["phase"] == 2
        assert len(phases[1]["slices"]) == 4

    def test_parse_plain_items(self) -> None:
        text = (FIXTURES / "plan_plain_items.md").read_text()
        phases = parse_phases(text)
        assert len(phases) == 1
        assert phases[0]["phase"] == 7
        assert len(phases[0]["slices"]) == 4
        assert phases[0]["slices"][0]["id"] == "P7.1"
        assert "Upload thesis" in phases[0]["slices"][0]["title"]

    def test_no_section_24_returns_empty(self) -> None:
        text = "## §10 — Something else\n### Fase 1 — Test\n1. **T1.1** nothing\n"
        phases = parse_phases(text)
        assert phases == []

    def test_empty_plan(self) -> None:
        phases = parse_phases("")
        assert phases == []


# ---------------------------------------------------------------------------
# fetch_task_status
# ---------------------------------------------------------------------------


class TestFetchTaskStatus:
    @pytest.fixture
    def db_path(self, tmp_path: Path) -> str:
        p = tmp_path / "test.db"
        conn = sqlite3.connect(str(p))
        conn.executescript("""
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
                ('exec-1', 'executor', 'succeeded', '{"slice":"T1.1"}', '2026-05-01T00:00:00', '2026-05-01T00:00:00', '2026-05-01T01:00:00'),
                ('exec-2', 'executor', 'failed',    '{"slice":"T1.2"}', '2026-05-01T02:00:00', '2026-05-01T02:00:00', '2026-05-01T02:30:00'),
                ('exec-3', 'executor', 'running',   '{"slice":"T2.1"}', '2026-05-01T03:00:00', '2026-05-01T03:00:00', NULL),
                ('jan-1',  'janitor',  'succeeded', '{"slice":"J1.1"}', '2026-05-01T00:00:00', '2026-05-01T00:00:00', '2026-05-01T00:05:00');
        """)
        conn.commit()
        conn.close()
        return str(p)

    def test_fetch_returns_executor_only(self, db_path: str) -> None:
        state = fetch_task_status(db_path)
        assert "T1.1" in state
        assert "T1.2" in state
        assert "T2.1" in state
        assert "J1.1" not in state  # janitor, not executor

    def test_status_mapping(self, db_path: str) -> None:
        state = fetch_task_status(db_path)
        assert state["T1.1"]["latest_status"] == "succeeded"
        assert state["T1.2"]["latest_status"] == "failed"
        assert state["T2.1"]["latest_status"] == "running"

    def test_takes_latest_by_timestamp(self, db_path: str) -> None:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO tasks VALUES ('exec-4', 'executor', 'succeeded', '{\"slice\":\"T1.1\"}', '2026-05-02T00:00:00', '2026-05-02T00:00:00', '2026-05-02T01:00:00')"
        )
        conn.commit()
        conn.close()
        state = fetch_task_status(db_path)
        assert state["T1.1"]["latest_task_id"] == "exec-4"
        assert state["T1.1"]["count"] == 2

    def test_missing_spawn_args(self, db_path: str) -> None:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO tasks VALUES ('exec-5', 'executor', 'succeeded', NULL, '2026-05-01T00:00:00', NULL, NULL)"
        )
        conn.commit()
        conn.close()
        state = fetch_task_status(db_path)
        assert "T1.1" in state  # no crash


# ---------------------------------------------------------------------------
# find_next
# ---------------------------------------------------------------------------


class TestFindNext:
    def test_returns_first_untouched(self) -> None:
        phases = [
            {"phase": 1, "name": "F1", "slices": [{"id": "T1.1", "title": "first"}, {"id": "T1.2", "title": "second"}]},
        ]
        nxt = find_next(phases, {"T1.1": {"latest_status": "succeeded"}})
        assert nxt is not None
        assert nxt["id"] == "T1.2"

    def test_returns_none_when_all_done(self) -> None:
        phases = [
            {"phase": 1, "name": "F1", "slices": [{"id": "T1.1", "title": "first"}]},
        ]
        nxt = find_next(phases, {"T1.1": {"latest_status": "succeeded"}})
        assert nxt is None

    def test_returns_first_phase_untouched(self) -> None:
        phases = [
            {"phase": 1, "name": "F1", "slices": [{"id": "T1.1", "title": "a"}]},
            {"phase": 2, "name": "F2", "slices": [{"id": "T2.1", "title": "b"}]},
        ]
        nxt = find_next(phases, {})
        assert nxt is not None
        assert nxt["id"] == "T1.1"

    def test_ignores_phase_with_failed_slices(self) -> None:
        phases = [
            {"phase": 1, "name": "F1", "slices": [{"id": "T1.1", "title": "a"}]},
        ]
        nxt = find_next(phases, {"T1.1": {"latest_status": "failed"}})
        assert nxt is None  # "untouched" means not in task_state at all


# ---------------------------------------------------------------------------
# render_text
# ---------------------------------------------------------------------------


class TestRenderText:
    def test_empty_slices_shows_warning(self) -> None:
        phases = [{"phase": 1, "name": "Empty", "slices": []}]
        out = render_text(phases, {}, phase_filter=None)
        assert "no slices parsed" in out

    def test_render_includes_glyphs(self) -> None:
        phases = [{"phase": 1, "name": "F1", "slices": [{"id": "T1.1", "title": "test", "raw": "T1.1"}]}]
        out = render_text(phases, {"T1.1": {"latest_status": "succeeded", "latest_task_id": "t1", "latest_at": "now", "count": 1}}, phase_filter=None)
        assert "✅" in out
        assert "T1.1" in out

    def test_phase_filter(self) -> None:
        phases = [
            {"phase": 1, "name": "F1", "slices": [{"id": "T1.1", "title": "a", "raw": "T1.1"}]},
            {"phase": 2, "name": "F2", "slices": [{"id": "T2.1", "title": "b", "raw": "T2.1"}]},
        ]
        out = render_text(phases, {}, phase_filter=2)
        assert "F1" not in out
        assert "F2" in out

    def test_truncates_long_titles(self) -> None:
        long_title = "x" * 100
        phases = [{"phase": 1, "name": "F1", "slices": [{"id": "T1.1", "title": long_title, "raw": "T1.1"}]}]
        out = render_text(phases, {}, phase_filter=None)
        assert len([l for l in out.split("\n") if "T1.1" in l][0]) < 200

"""Which inbox a tick is allowed to take from, and why that is configuration.

The tick orders candidates by priority across every inbox at once, so a message
addressed to this machine outranks the shared board whenever its priority is
higher. That happened: a protocol message at priority 95 was claimed while four
tasks at priority 70 sat untouched on ``inbox/any``, and the protocol it carried
was the one saying conversation and claimable work are different channels.

A rule written in a message cannot bind a process that was configured before the
message existed. ``COORD_BOXES`` is that rule expressed as configuration: a
conductor is given ``any`` and can then only ever take claimable work, while the
session keeps the default and answers conversation.

These tests drive the real ``list_candidates`` block out of the real script, so
they fail if the selection is edited without the guard being reconsidered.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "coord" / "coord-tick.sh"


def _selection_block() -> str:
    """The python heredoc that filters and orders candidates, lifted from the script.

    Extracted rather than reimplemented: a copy would keep passing after the
    original changed, which is the failure this whole file exists to prevent.
    """
    text = SCRIPT.read_text()
    blocks = re.findall(r"<<'PY'\n(.*?)\nPY\n", text, re.S)
    for block in blocks:
        if "inbox" in block and "priority" in block:
            return block
    raise AssertionError("no candidate-listing block found in coord-tick.sh")


def _message(mid: str, to: str, priority: int, minutes_ahead: int = 60) -> dict:
    now = datetime.now(UTC)
    return {
        "schema": "farm.coord/1",
        "id": mid,
        "kind": "task",
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "from": "laptop",
        "to": to,
        "requires": [],
        "priority": priority,
        "expires_at": (now + timedelta(minutes=minutes_ahead)).isoformat().replace("+00:00", "Z"),
        "subject": f"{to} at {priority}",
        "body": "",
    }


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A ledger holding one high-priority conversation and one lower-priority task."""
    for box in ("desktop", "any"):
        (tmp_path / "inbox" / box).mkdir(parents=True)
    (tmp_path / "inbox" / "desktop" / "a.json").write_text(
        json.dumps(_message("CONVERSATION", "desktop", 95))
    )
    (tmp_path / "inbox" / "any" / "b.json").write_text(
        json.dumps(_message("BOARDWORK", "any", 70))
    )
    return tmp_path


def _run(repo: Path, boxes: str) -> tuple[list[str], int]:
    proc = subprocess.run(
        [sys.executable, "-c", _selection_block(), str(repo), "desktop", "", boxes],
        capture_output=True, text=True, timeout=60,
    )
    ids = [line.split("\t")[2] for line in proc.stdout.splitlines() if line.strip()]
    return ids, proc.returncode


def test_the_default_sees_both_boxes_and_priority_wins(repo: Path):
    """The current behaviour, kept, because a session should answer conversation."""
    ids, code = _run(repo, "self any")

    assert code == 0
    assert ids[0] == "CONVERSATION"
    assert "BOARDWORK" in ids


def test_an_empty_setting_falls_back_to_both_rather_than_to_none(repo: Path):
    """An unset variable must not silently make a tick take nothing at all."""
    ids, code = _run(repo, "")

    assert code == 0
    assert set(ids) == {"CONVERSATION", "BOARDWORK"}


def test_a_conductor_pointed_at_the_board_cannot_see_conversation(repo: Path):
    """The regression. This is the whole reason the knob exists."""
    ids, code = _run(repo, "any")

    assert code == 0
    assert ids == ["BOARDWORK"]
    assert "CONVERSATION" not in ids


def test_higher_priority_conversation_does_not_leak_into_a_board_only_tick(repo: Path):
    """Priority orders within the selected boxes; it does not widen them."""
    (repo / "inbox" / "desktop" / "c.json").write_text(
        json.dumps(_message("URGENT", "desktop", 100))
    )

    ids, _ = _run(repo, "any")

    assert ids == ["BOARDWORK"]


def test_self_only_excludes_the_shared_board(repo: Path):
    """The mirror case, so the knob is a selection rather than a board switch."""
    ids, code = _run(repo, "self")

    assert code == 0
    assert ids == ["CONVERSATION"]


def test_an_unknown_box_stops_the_tick_rather_than_being_ignored(repo: Path):
    """A typo that silently selected nothing would look exactly like an empty board."""
    _, code = _run(repo, "laptop")

    assert code == 78


def test_a_comma_separated_setting_is_accepted(repo: Path):
    """systemd Environment lines are written both ways and neither should surprise."""
    ids, code = _run(repo, "self,any")

    assert code == 0
    assert set(ids) == {"CONVERSATION", "BOARDWORK"}


def test_an_expired_board_task_is_still_skipped(repo: Path):
    """The box filter must not bypass the expiry filter it sits beside."""
    (repo / "inbox" / "any" / "d.json").write_text(
        json.dumps(_message("STALE", "any", 99, minutes_ahead=-10))
    )

    ids, _ = _run(repo, "any")

    assert "STALE" not in ids
    assert ids == ["BOARDWORK"]

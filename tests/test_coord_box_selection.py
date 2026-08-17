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


def _message(mid: str, to: str, priority: int, minutes_ahead: int = 60,
             prefer: str | None = None, age_min: int = 0) -> dict:
    now = datetime.now(UTC)
    created = now - timedelta(minutes=age_min)
    doc = {
        "schema": "farm.coord/1",
        "id": mid,
        "kind": "task",
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "from": "laptop",
        "to": to,
        "requires": [],
        "priority": priority,
        "expires_at": (now + timedelta(minutes=minutes_ahead)).isoformat().replace("+00:00", "Z"),
        "subject": f"{to} at {priority}",
        "body": "",
    }
    if prefer:
        doc["prefer"] = prefer
    return doc


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


def _run(repo: Path, boxes: str, grace: str = "900",
         machine: str = "desktop") -> tuple[list[str], int]:
    proc = subprocess.run(
        [sys.executable, "-c", _selection_block(), str(repo), machine, "", boxes, grace],
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


# --------------------------------------------------------------------------- preference

def _board(tmp_path: Path, **kw) -> Path:
    (tmp_path / "inbox" / "any").mkdir(parents=True)
    (tmp_path / "inbox" / "desktop").mkdir(parents=True)
    (tmp_path / "inbox" / "any" / "p.json").write_text(
        json.dumps(_message("PREFERRED", "any", 70, **kw))
    )
    return tmp_path


def test_a_preference_defers_the_other_machine_while_it_is_fresh(tmp_path: Path):
    """The lane holds while both machines are up."""
    repo = _board(tmp_path, prefer="desktop")
    ids, code = _run(repo, "any", machine="laptop")

    assert code == 0
    assert ids == []


def test_the_preferred_machine_is_never_deferred(tmp_path: Path):
    repo = _board(tmp_path, prefer="desktop")
    ids, _ = _run(repo, "any", machine="desktop")

    assert ids == ["PREFERRED"]


def test_the_preference_expires_so_a_machine_being_down_costs_throughput(tmp_path: Path):
    """The whole reason this is a head start and not a filter.

    A capability list that lied about ability would leave the board unable to
    route anything when the preferred machine is off, and nothing would say why.
    """
    repo = _board(tmp_path, prefer="desktop", age_min=20)
    ids, _ = _run(repo, "any", machine="laptop")

    assert ids == ["PREFERRED"]


def test_a_zero_grace_disables_deferral_entirely(tmp_path: Path):
    repo = _board(tmp_path, prefer="desktop")
    ids, _ = _run(repo, "any", grace="0", machine="laptop")

    assert ids == ["PREFERRED"]


def test_a_message_without_a_preference_is_never_deferred(tmp_path: Path):
    repo = _board(tmp_path)
    ids, _ = _run(repo, "any", machine="laptop")

    assert ids == ["PREFERRED"]


def test_an_unparsable_grace_falls_back_rather_than_crashing(tmp_path: Path):
    repo = _board(tmp_path, prefer="desktop")
    _, code = _run(repo, "any", grace="soon", machine="laptop")

    assert code == 0


# --------------------------------------------------------------------------- supersedes

def _two_generations(tmp_path: Path, supersedes) -> Path:
    (tmp_path / "inbox" / "any").mkdir(parents=True)
    (tmp_path / "inbox" / "desktop").mkdir(parents=True)
    (tmp_path / "inbox" / "any" / "old.json").write_text(
        json.dumps(_message("FIRST_TRY", "any", 70))
    )
    fixed = _message("CORRECTED", "any", 70)
    if supersedes is not None:
        fixed["supersedes"] = supersedes
    (tmp_path / "inbox" / "any" / "new.json").write_text(json.dumps(fixed))
    return tmp_path


def test_a_repost_hides_the_generation_it_replaces(tmp_path: Path):
    """The regression, and it comes from a real board.

    Ten messages once sat on this board for three real tasks, every one of them
    live to a scanner, and the only thing marking the seven dead was prose in a
    different message.
    """
    repo = _two_generations(tmp_path, ["FIRST_TRY"])

    ids, code = _run(repo, "any")

    assert code == 0
    assert ids == ["CORRECTED"]


def test_without_the_field_both_generations_stay_visible(tmp_path: Path):
    """So the behaviour is opt-in and nothing already on a board changes."""
    repo = _two_generations(tmp_path, None)

    ids, _ = _run(repo, "any")

    assert set(ids) == {"FIRST_TRY", "CORRECTED"}


def test_a_bare_string_is_accepted_as_well_as_a_list(tmp_path: Path):
    """A sender replacing one message should not have to remember to wrap it."""
    repo = _two_generations(tmp_path, "FIRST_TRY")

    ids, _ = _run(repo, "any")

    assert ids == ["CORRECTED"]


def test_superseding_reaches_across_boxes(tmp_path: Path):
    """A task moved from a machine inbox to the board must not leave a twin behind."""
    (tmp_path / "inbox" / "any").mkdir(parents=True)
    (tmp_path / "inbox" / "desktop").mkdir(parents=True)
    (tmp_path / "inbox" / "desktop" / "old.json").write_text(
        json.dumps(_message("ADDRESSED", "desktop", 70))
    )
    fixed = _message("ON_THE_BOARD", "any", 70)
    fixed["supersedes"] = ["ADDRESSED"]
    (tmp_path / "inbox" / "any" / "new.json").write_text(json.dumps(fixed))

    ids, _ = _run(repo=tmp_path, boxes="self any")

    assert "ADDRESSED" not in ids
    assert "ON_THE_BOARD" in ids


def test_an_unreadable_neighbour_does_not_stop_the_scan(tmp_path: Path):
    """One corrupt file must not make the whole board invisible."""
    repo = _two_generations(tmp_path, ["FIRST_TRY"])
    (repo / "inbox" / "any" / "broken.json").write_text("{ not json")

    ids, code = _run(repo, "any")

    assert code == 0
    assert ids == ["CORRECTED"]

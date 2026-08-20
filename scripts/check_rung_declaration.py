"""The ladder has to be a claim something can refuse.

CAMPAIGN.md declares five rungs, each with one question and one gate, and
it has been right and unread. On 2026-08-19 a grid ran 48 arms of the
declared rung 1 while varying two of its three axes, the third pinned by
omission to the weakest available value. Four hundred jobs were then
tagged with a rung number invented at dispatch. Nothing objected to
either, because prose cannot refuse a job.

This checks the declaration itself: that it is well formed, that the
dependencies between rungs point backwards, and that nothing is held
without saying who decided it. The runtime half, checking a dispatched
job against the rung it claims, lives in PROTEA where the jobs are.

Exit 0 clean, 1 with the offences listed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

DECLARATION = Path(__file__).resolve().parents[1] / "plans" / "rungs.yaml"

_REQUIRED = ("number", "title", "question", "axes", "held", "gate", "winner", "status")
#: ``parked`` is deliberately not now, and it has to carry its reason:
#: the whole point of the distinction is that a parked rung reads as a
#: decision rather than as something nobody got to.
_STATUSES = {"declared", "running", "closed", "reopened", "parked"}
_WINNERS = {"per_cell", "global"}


def _offences(doc: dict[str, Any]) -> list[str]:
    out: list[str] = []
    rungs = doc.get("rungs") or []
    if not rungs:
        return ["no rungs declared"]

    numbers = [r.get("number") for r in rungs]
    if numbers != sorted(numbers):
        out.append(f"rungs are not in order: {numbers}")
    if len(set(numbers)) != len(numbers):
        out.append(f"duplicate rung numbers: {numbers}")

    for rung in rungs:
        n = rung.get("number", "?")
        for field in _REQUIRED:
            if field not in rung:
                out.append(f"rung {n}: missing {field}")

        if rung.get("status") not in _STATUSES:
            out.append(f"rung {n}: status {rung.get('status')!r} is not one of {sorted(_STATUSES)}")
        if rung.get("status") == "parked" and not (rung.get("parked") or {}).get("reason"):
            out.append(f"rung {n}: parked without a reason, which is indistinguishable from forgotten")
        if rung.get("winner") not in _WINNERS:
            out.append(f"rung {n}: winner {rung.get('winner')!r} is not one of {sorted(_WINNERS)}")

        for axis in rung.get("axes") or []:
            if "name" not in axis:
                out.append(f"rung {n}: an axis has no name")
                continue
            # An axis with no field cannot be checked against a job, so it
            # has to say why. Silence here is how an axis becomes a wish.
            if "field" not in axis:
                out.append(f"rung {n}: axis {axis['name']} declares no field")
            elif axis["field"] is None and not axis.get("note"):
                out.append(
                    f"rung {n}: axis {axis['name']} has no field and no note "
                    "saying why it cannot be checked"
                )

        for held in rung.get("held") or []:
            who = held.get("decided_by")
            if not who:
                out.append(f"rung {n}: holds {held.get('what')!r} without saying who decided it")
                continue
            if who in ("campaign",) or str(who).startswith("rungs"):
                continue
            # "rung 4" held by rung 5 would be a ladder that stands on its
            # own shoulders, and an answer that changes would not propagate.
            if str(who).startswith("rung "):
                try:
                    dep = int(str(who).split()[1])
                except (IndexError, ValueError):
                    out.append(f"rung {n}: cannot read dependency {who!r}")
                    continue
                if dep >= n:
                    out.append(f"rung {n}: depends on rung {dep}, which is not below it")
                if dep not in numbers:
                    out.append(f"rung {n}: depends on rung {dep}, which is not declared")
    return out


def main() -> int:
    if not DECLARATION.exists():
        print(f"missing declaration: {DECLARATION}")
        return 1
    doc = yaml.safe_load(DECLARATION.read_text())
    offences = _offences(doc)
    if offences:
        print(f"rung declaration: {len(offences)} offence(s)")
        for o in offences:
            print(f"  {o}")
        return 1
    print(f"rung declaration OK: {len(doc['rungs'])} rungs, dependencies point backwards")
    return 0


if __name__ == "__main__":
    sys.exit(main())

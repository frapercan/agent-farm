#!/usr/bin/env python3
"""Which revision each worker of this node sealed at each start, against what was declared.

node-sync makes the node follow the declaration; this reads afterwards whether it
did, from the three records the node already keeps, and touches none of them:

  - each worker's own log, whose "Worker started. queue=... revision=..." line is
    the only witness of what that process imported;
  - the history of plans/DECLARED-REVISION.txt on agent-farm's origin/main, which
    says what was declared from when;
  - the deploy slot's git reflog, which says when the tree moved, and node-sync's
    journal, which says when it installed a sibling into an environment.

For every run of every worker (one start line to the next start or stop) it
reports the revision stamped, the coordinator declared at that moment, and every
tree move or sibling install INSIDE the run, with how many operations or jobs
the worker dispatched after the first of them. That last number is the dangerous
one: a process keeps the modules it has imported and reads any later import from
the tree as it is now, so work dispatched after a move inside a run ran on a
revision nobody declared.

Written on 2026-11-04, when the first pass over 93 runs since 2026-10-08 found no
dispatch after a move, and two starts on a revision the declaration no longer
named, both stopped by node-sync within a minute without dispatching anything.

    python3 protea-node-revision-audit.py [--since 2026-10-10T00:00:00+02:00] [--json]

Paths follow the node's override: PROTEA_REPO, PROTEA_FARM, PROTEA_LOGDIR.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
TREE = Path(os.environ.get("PROTEA_REPO", HOME / "Thesis2/worktrees/protea-deploy"))
FARM = Path(os.environ.get("PROTEA_FARM", HOME / "Thesis2/agent-farm"))
LOGS = Path(os.environ.get("PROTEA_LOGDIR", HOME / "Thesis2/storage/logs"))
DECL = "plans/DECLARED-REVISION.txt"
START = re.compile(r"Worker started\. queue=(\S+) revision=(\S+)(.*)$")
END_MARKS = ("Worker stopped.", "outlived the broker heartbeat window")


def run(*cmd: str) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def declarations() -> list[tuple[datetime, str]]:
    """(effective time, coordinator) for every commit that touched the declaration."""
    out = []
    log = run("git", "-C", str(FARM), "log", "origin/main", "--format=%H %cI", "--", DECL)
    for line in log.splitlines():
        commit, when = line.split()
        try:
            body = run("git", "-C", str(FARM), "show", f"{commit}:{DECL}")
        except subprocess.CalledProcessError:
            continue  # the commit deleted the file
        coord = next((ln.split()[1] for ln in body.splitlines()
                      if ln.split()[:1] == ["coordinator"] and len(ln.split()) > 1), "?")
        out.append((datetime.fromisoformat(when), coord))
    return sorted(out)


def tree_moves() -> list[tuple[datetime, str]]:
    out = []
    reflog = run("git", "-C", str(TREE), "log", "-g", "--date=iso-strict", "--format=%gd|%H")
    for line in reflog.splitlines():
        selector, sha = line.split("|", 1)
        out.append((datetime.fromisoformat(selector[selector.index("{") + 1:selector.index("}")]), sha))
    return sorted(out)


def sibling_installs() -> list[tuple[datetime, str]]:
    try:
        text = run("journalctl", "--user", "-u", "protea-node-sync.service", "--no-pager", "-o", "cat")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    found = re.finditer(r"^(\S+) node-sync: installing (\S+)(?: into (\S+))?", text, re.M)
    return sorted((datetime.fromisoformat(m.group(1)), m.group(2)) for m in found)


def at(series, when):
    """The last entry of a time-sorted series at or before ``when``."""
    last = None
    for item in series:
        if item[0] > when:
            break
        last = item
    return last


def runs_of(log: Path) -> list[dict]:
    runs: list[dict] = []
    cur: dict | None = None
    with log.open("rb") as handle:
        for raw in handle:
            if b'"timestamp"' not in raw:
                continue
            try:
                rec = json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                continue
            msg, when = rec.get("message", ""), datetime.fromisoformat(rec["timestamp"])
            started = START.search(msg)
            if started:
                if cur:
                    cur.setdefault("end", when)
                    runs.append(cur)
                cur = {"start": when, "rev": started.group(2), "extra": started.group(3).strip(),
                       "dispatches": []}
            elif cur is not None:
                if msg.startswith(("Dispatching operation", "Dispatching job")):
                    cur["dispatches"].append(when)
                elif any(mark in msg for mark in END_MARKS):
                    cur.setdefault("end", when)
    if cur:
        runs.append(cur)
    return runs


def audit(since: datetime) -> list[dict]:
    decl, moves, installs = declarations(), tree_moves(), sibling_installs()
    now = datetime.now(timezone.utc)
    rows = []
    for log in sorted(LOGS.glob("protea-lab-worker-protea.*.log")):
        queue = log.name.removeprefix("protea-lab-worker-").removesuffix(".log")
        for r in runs_of(log):
            end = r.get("end", now)
            if end < since:
                continue
            declared = at(decl, r["start"])
            inside = [m for m in moves if r["start"] < m[0] < end]
            installed = [i for i in installs if r["start"] < i[0] < end]
            first = min([m[0] for m in inside] + [i[0] for i in installed], default=None)
            rows.append({
                "queue": queue,
                "start": r["start"].astimezone().isoformat(timespec="seconds"),
                "end": end.astimezone().isoformat(timespec="seconds") if "end" in r else None,
                "stamped": r["rev"] + (f" {r['extra']}" if r["extra"] else ""),
                "declared": declared[1] if declared else None,
                "as_declared": bool(declared) and r["rev"] == declared[1] and not r["extra"],
                "tree_moves_inside": [f"{m[0].isoformat()} {m[1][:12]}" for m in inside],
                "installs_inside": [f"{i[0].isoformat()} {i[1]}" for i in installed],
                "dispatches": len(r["dispatches"]),
                "dispatches_after_a_move": sum(1 for w in r["dispatches"] if first and w > first),
            })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--since", default="2026-10-10T00:00:00+02:00")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    rows = audit(datetime.fromisoformat(args.since))
    if args.json:
        print(json.dumps(rows, indent=1))
        return
    for r in rows:
        flags = []
        if not r["as_declared"]:
            flags.append("NOT AS DECLARED")
        if r["dispatches_after_a_move"]:
            flags.append(f"{r['dispatches_after_a_move']} DISPATCHED AFTER A MOVE")
        print(f"{r['queue']:28} {r['start']} -> {r['end'] or 'running':25} "
              f"stamped {r['stamped'][:12]} declared {(r['declared'] or 'none')[:12]} "
              f"dispatches {r['dispatches']:5}  {' '.join(flags)}")
    bad = [r for r in rows if r["dispatches_after_a_move"]
           or (not r["as_declared"] and r["dispatches"])]
    print(f"{len(rows)} runs; {len(bad)} did work on a revision nobody declared")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Parse master plan §24 + join with sqlite executor task history.

Outputs a progress table. Slice IDs in §24 follow the format `**T...**` at the
start of numbered list items inside `### Fase N` sections.

Status derivation:
- Slice ID present in `tasks.spawn_args.slice` AND most-recent task succeeded → ✅
- Slice ID present AND latest task running/pending                          → ⏳
- Slice ID present AND latest task failed/killed/crashed                    → ❌
- Slice ID not in any task                                                   → ⬜
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path


PHASE_HEADER_RE = re.compile(r"^### Fase (\d+)\s*[—-]\s*(.+?)\s*$")
SECTION_HEADER_RE = re.compile(r"^## §\d+")
# Numbered list item with bold slice id — accepts T (T1.7, T-CONTEXTS), F (F2C.5), D (D27)
SLICE_RE = re.compile(r"^\s*\d+\.\s*\*\*([TFD][^\*]+?)\*\*\s*(.*)$")
# Fallback: bare numbered item (Fase 7 uses these — describe deliverables)
PLAIN_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")


def parse_phases(plan_text: str) -> list[dict]:
    """Return [{phase: int, name: str, slices: [{id, title, raw}]}, ...]"""
    phases: list[dict] = []
    in_section_24 = False
    current_phase: dict | None = None
    # Track lines per phase so we can do a fallback pass for unbold-formatted phases
    phase_lines: dict[int, list[str]] = {}

    for line in plan_text.splitlines():
        if line.startswith("## §24"):
            in_section_24 = True
            continue
        if in_section_24 and SECTION_HEADER_RE.match(line):
            break
        if not in_section_24:
            continue

        m = PHASE_HEADER_RE.match(line)
        if m:
            current_phase = {
                "phase": int(m.group(1)),
                "name": m.group(2).strip(),
                "slices": [],
            }
            phases.append(current_phase)
            phase_lines[current_phase["phase"]] = []
            continue

        if current_phase is None:
            continue
        phase_lines[current_phase["phase"]].append(line)

        m = SLICE_RE.match(line)
        if m:
            slice_id_raw = m.group(1).strip()
            title_extra = m.group(2).strip()
            parts = slice_id_raw.split(None, 1)
            sid = parts[0].rstrip(".:")
            title = parts[1] if len(parts) > 1 else ""
            if title_extra and not title:
                title = title_extra
            current_phase["slices"].append({
                "id": sid,
                "title": title or "(no title in §24)",
                "raw": slice_id_raw,
            })

    # Fallback: phases with 0 bold-slices → synthesize from plain numbered items
    for ph in phases:
        if ph["slices"]:
            continue
        for line in phase_lines.get(ph["phase"], []):
            m = PLAIN_ITEM_RE.match(line)
            if not m:
                continue
            num, body = m.group(1), m.group(2).strip()
            sid = f"P{ph['phase']}.{num}"
            title = body[:80]
            ph["slices"].append({"id": sid, "title": title, "raw": body})
    return phases


def fetch_task_status(db_path: str) -> dict[str, dict]:
    """Return {slice_id: {latest_status, latest_task_id, latest_at, count}}."""
    out: dict[str, dict] = {}
    with sqlite3.connect(db_path) as c:
        cur = c.execute("""
            SELECT json_extract(spawn_args, '$.slice') AS slice,
                   id, status, COALESCE(ended_at, started_at, created_at) AS ts
            FROM tasks
            WHERE agent_name='executor' AND slice IS NOT NULL AND slice != ''
            ORDER BY ts DESC
        """)
        for slice_id, task_id, status, ts in cur.fetchall():
            if slice_id in out:
                out[slice_id]["count"] += 1
                continue
            out[slice_id] = {
                "latest_status": status,
                "latest_task_id": task_id,
                "latest_at": ts,
                "count": 1,
            }
    return out


STATUS_GLYPH = {
    "succeeded": "✅",
    "running":   "⏳",
    "pending":   "⏳",
    "failed":    "❌",
    "killed":    "❌",
    "crashed":   "❌",
}


def render_text(phases: list[dict], task_state: dict, phase_filter: int | None) -> str:
    out = []
    for ph in phases:
        if phase_filter and ph["phase"] != phase_filter:
            continue
        out.append(f"### Fase {ph['phase']} — {ph['name']}")
        if not ph["slices"]:
            out.append("  (no slices parsed; check §24 markdown)")
            continue
        for s in ph["slices"]:
            st = task_state.get(s["id"])
            glyph = STATUS_GLYPH.get(st["latest_status"], "🟡") if st else "⬜"
            tail = ""
            if st:
                tail = f"  [{st['latest_status']} via {st['latest_task_id']} @ {st['latest_at']}]"
            title = (s["title"][:60] + "…") if len(s["title"]) > 60 else s["title"]
            out.append(f"  {glyph}  {s['id']:18s}  {title}{tail}")
        out.append("")
    return "\n".join(out)


def find_next(phases: list[dict], task_state: dict) -> dict | None:
    """First slice with status=⬜ in earliest phase."""
    for ph in phases:
        for s in ph["slices"]:
            if s["id"] not in task_state:
                return {"phase": ph["phase"], **s}
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--phase", type=int, default=None)
    ap.add_argument("--next", action="store_true",
                    help="just the next unblocked slice, suitable for executor spawn")
    ap.add_argument("--json", action="store_true",
                    help="machine-readable JSON output")
    args = ap.parse_args()

    plan_text = Path(args.plan).read_text()
    phases = parse_phases(plan_text)
    task_state = fetch_task_status(args.db)

    if args.next:
        nxt = find_next(phases, task_state)
        if nxt is None:
            print("(no unblocked slices in §24 — plan may be complete or out-of-date)")
            return 0
        if args.json:
            print(json.dumps(nxt, indent=2))
        else:
            print(f"Next: phase {nxt['phase']}, slice {nxt['id']} — {nxt['title']}")
            print(f'Spawn:  /agent-farm-spawn executor \'{{"slice":"{nxt["id"]}","phase":{nxt["phase"]}}}\'')
        return 0

    if args.json:
        out = {
            "phases": phases,
            "task_state": task_state,
            "next": find_next(phases, task_state),
        }
        print(json.dumps(out, indent=2))
        return 0

    print(f"=== §24 progress (touched slices: {len(task_state)}) ===\n")
    print(render_text(phases, task_state, args.phase))
    nxt = find_next(phases, task_state)
    if nxt:
        print(f"NEXT UNTOUCHED: phase {nxt['phase']}, {nxt['id']} — {nxt['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

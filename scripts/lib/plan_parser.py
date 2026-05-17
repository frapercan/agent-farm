#!/usr/bin/env python3
"""Parse the internal plan store (plans/<loop>/PLAN.md) + join with sqlite executor task history.

Outputs a progress table. The canonical plan store is the per-loop
`plans/<loop>/PLAN.md` corpus. Each slice is a `### <title>` heading
immediately followed by a fenced ```yaml frontmatter block declaring
id / phase / loop / status / deps / priority / requires_human (see
`plans/README.md` for the full schema).

Status derivation:
- A slice's authoritative status is its frontmatter `status:` field
  (`pending` / `in_progress` / `blocked` / `done` / `deferred`).
- The sqlite executor task history is overlaid as an audit annotation
  (latest_status / latest_task_id / latest_at / count) when the slice
  id appears in `tasks.spawn_args.slice`.
- `find_next` returns the highest-priority pickable slice across ALL
  loops (status=pending, all deps done, not requires_human), tie-broken
  by (priority, loop, phase, id).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is a runtime dep
    sys.stderr.write("ERROR: PyYAML is required. pip install pyyaml\n")
    raise


# Match a `### <title>` heading followed by a ```yaml fenced frontmatter
# and the free-form body up to the next ### or end-of-file. Mirrors
# plans/render.py:SECTION_RX so the two stay in lockstep on discovery.
SECTION_RX = re.compile(
    r"^### (.+?)\n```yaml\n(.+?)\n```\n(.*?)(?=^### |\Z)",
    re.M | re.S,
)

STATUS_ORDER = ["in_progress", "blocked", "pending", "done", "deferred"]
STATUS_GLYPH = {
    "pending": "⬜",
    "in_progress": "🟡",
    "blocked": "🟥",
    "done": "✅",
    "deferred": "⬛",
}
TASK_STATUS_GLYPH = {
    "succeeded": "✅",
    "running": "⏳",
    "pending": "⏳",
    "failed": "❌",
    "killed": "❌",
    "crashed": "❌",
}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


@dataclass
class Slice:
    id: str
    title: str
    loop: str
    phase: str
    status: str
    deps: list[str] = field(default_factory=list)
    acceptance: str = ""
    estimated_hours: int | None = None
    priority: str = "P2"
    tags: list[str] = field(default_factory=list)
    requires_human: bool = False
    superseded_by: str | None = None
    source_file: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "loop": self.loop,
            "phase": self.phase,
            "status": self.status,
            "deps": list(self.deps),
            "acceptance": self.acceptance,
            "estimated_hours": self.estimated_hours,
            "priority": self.priority,
            "tags": list(self.tags),
            "requires_human": self.requires_human,
            "superseded_by": self.superseded_by,
        }


def discover_slices(plans_root: Path) -> list[Slice]:
    """Walk plans/<loop>/PLAN.md and parse every slice section.

    Raises SystemExit on schema violations (duplicate id, loop mismatch,
    malformed frontmatter) so plan-progress and render.py fail the same
    way on the same corpus.
    """
    slices: list[Slice] = []
    seen_ids: set[str] = set()
    loop_dirs = sorted(
        p for p in plans_root.iterdir()
        if p.is_dir() and (p / "PLAN.md").exists()
    )
    for loop_dir in loop_dirs:
        plan = loop_dir / "PLAN.md"
        text = plan.read_text()
        loop_name = loop_dir.name
        for match in SECTION_RX.finditer(text):
            title, frontmatter, _body = match.groups()
            try:
                meta = yaml.safe_load(frontmatter) or {}
            except yaml.YAMLError as e:
                raise SystemExit(
                    f"{plan}: malformed YAML in '### {title.strip()}' — {e}"
                )
            try:
                sid = str(meta["id"])
            except KeyError:
                raise SystemExit(
                    f"{plan}: '### {title.strip()}' frontmatter has no `id:`"
                )
            declared_loop = str(meta.get("loop", loop_name))
            if declared_loop != loop_name:
                raise SystemExit(
                    f"{plan}: slice {sid} declares loop={declared_loop!r} "
                    f"but lives under plans/{loop_name}/"
                )
            if sid in seen_ids:
                raise SystemExit(
                    f"duplicate slice id: {sid} (in {plan})"
                )
            seen_ids.add(sid)
            slices.append(Slice(
                id=sid,
                title=title.strip(),
                loop=loop_name,
                phase=str(meta.get("phase", "")),
                status=str(meta.get("status", "pending")),
                deps=list(meta.get("deps") or []),
                acceptance=str(meta.get("acceptance", "")),
                estimated_hours=meta.get("estimated_hours"),
                priority=str(meta.get("priority", "P2")),
                tags=list(meta.get("tags") or []),
                requires_human=bool(meta.get("requires_human", False)),
                superseded_by=meta.get("superseded_by"),
                source_file=str(plan),
            ))
    return slices


def group_by_phase(slices: list[Slice]) -> list[dict]:
    """Return a phase-grouped view compatible with the legacy --json shape.

    Each entry is `{phase: <str>, name: <str>, slices: [<dict>, ...]}`.
    `name` is the same as `phase` in the new schema (loops do not declare
    per-phase display names). Slice order is preserved from discovery.
    """
    by_phase: dict[str, dict] = {}
    order: list[str] = []
    for s in slices:
        ph = s.phase or "(unphased)"
        if ph not in by_phase:
            by_phase[ph] = {"phase": ph, "name": ph, "slices": []}
            order.append(ph)
        by_phase[ph]["slices"].append({
            **s.to_dict(),
            # legacy compat: existing JSON callers expect `title` to
            # double as a description; keep a `raw` alias
            "raw": s.title,
        })
    return [by_phase[p] for p in order]


def fetch_task_status(db_path: str) -> dict[str, dict]:
    """Return {slice_id: {latest_status, latest_task_id, latest_at, count}}.

    Shape preserved from the §24-era parser so shepherd / conductor
    consumers do not need to change.
    """
    out: dict[str, dict] = {}
    with sqlite3.connect(db_path) as c:
        cur = c.execute(
            """
            SELECT spawn_args, id, status, COALESCE(ended_at, started_at, created_at) AS ts
            FROM tasks
            WHERE agent_name='executor'
            ORDER BY ts DESC
            """
        )
        for spawn_args_raw, task_id, status, ts in cur.fetchall():
            if not spawn_args_raw:
                continue
            try:
                parsed = json.loads(spawn_args_raw)
            except json.JSONDecodeError:
                continue
            slice_id = parsed.get("slice")
            if not slice_id:
                continue
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


def find_next(slices: list[Slice], task_state: dict | None = None) -> dict | None:
    """Return the highest-priority pickable slice across all loops.

    Selection rules (FARM-2.7 spec):
      - status == "pending"
      - not requires_human
      - all deps are slices whose own status == "done"
      - tie-break by (priority P0<P1<P2<P3, loop alphabetical, phase, id)

    Returns a dict with id / title / loop / phase / priority / deps / status
    or None if no slice is pickable.
    """
    del task_state  # accepted for backwards-compatible callers; not used
    done_ids = {s.id for s in slices if s.status == "done"}
    candidates = [
        s for s in slices
        if s.status == "pending"
        and not s.requires_human
        and all(d in done_ids for d in s.deps)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda s: (
        PRIORITY_ORDER.get(s.priority, 99),
        s.loop,
        s.phase,
        s.id,
    ))
    top = candidates[0]
    return {
        # legacy compat keys
        "id": top.id,
        "title": top.title,
        "phase": top.phase,
        # new keys for the cross-loop world
        "loop": top.loop,
        "priority": top.priority,
        "deps": list(top.deps),
        "status": top.status,
    }


def render_text(slices: list[Slice], task_state: dict, phase_filter: str | None) -> str:
    """Render a human-readable progress table grouped by phase.

    Each row shows the canonical frontmatter status glyph and, when a
    matching executor task exists in sqlite, the latest task status as
    a secondary annotation.
    """
    by_phase: dict[str, list[Slice]] = {}
    order: list[str] = []
    for s in slices:
        ph = s.phase or "(unphased)"
        if ph not in by_phase:
            by_phase[ph] = []
            order.append(ph)
        by_phase[ph].append(s)

    out: list[str] = []
    for ph in order:
        if phase_filter and ph != phase_filter:
            continue
        out.append(f"### {ph}")
        for s in by_phase[ph]:
            glyph = STATUS_GLYPH.get(s.status, "🟡")
            tail = ""
            audit = task_state.get(s.id)
            if audit:
                tg = TASK_STATUS_GLYPH.get(audit["latest_status"], "")
                tail = (
                    f"  [{tg} {audit['latest_status']} via "
                    f"{audit['latest_task_id']} @ {audit['latest_at']}]"
                )
            title = (s.title[:60] + "…") if len(s.title) > 60 else s.title
            out.append(
                f"  {glyph}  {s.id:18s}  [{s.priority}]  ({s.loop})  {title}{tail}"
            )
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Legacy compatibility shims
#
# Older callers (and the test suite) used:
#   - parse_phases(plan_text) → list of phase dicts
#   - find_next(phases_list, task_state) over a legacy phase shape
# We keep these importable by adapting them on top of the new code.
# ---------------------------------------------------------------------------


def parse_phases(plan_text_or_root) -> list[dict]:
    """Compatibility shim.

    Accepts either:
      - a path-like / Path pointing at a plans/ root directory → walks
        every plans/<loop>/PLAN.md and returns phase-grouped dicts
      - a raw markdown string → parses ``` ### + yaml fence ``` slices
        inline (used by legacy unit tests that pass a fixture file)

    The returned shape is the same `[{phase, name, slices: [...]}, ...]`
    used by the original §24 parser.
    """
    if isinstance(plan_text_or_root, Path) or (
        isinstance(plan_text_or_root, str)
        and os.path.isdir(plan_text_or_root)
    ):
        return group_by_phase(discover_slices(Path(plan_text_or_root)))

    text = plan_text_or_root or ""
    slices: list[Slice] = []
    for match in SECTION_RX.finditer(text):
        title, frontmatter, _body = match.groups()
        try:
            meta = yaml.safe_load(frontmatter) or {}
        except yaml.YAMLError:
            continue
        if "id" not in meta:
            continue
        slices.append(Slice(
            id=str(meta["id"]),
            title=title.strip(),
            loop=str(meta.get("loop", "_inline")),
            phase=str(meta.get("phase", "")),
            status=str(meta.get("status", "pending")),
            deps=list(meta.get("deps") or []),
            acceptance=str(meta.get("acceptance", "")),
            estimated_hours=meta.get("estimated_hours"),
            priority=str(meta.get("priority", "P2")),
            tags=list(meta.get("tags") or []),
            requires_human=bool(meta.get("requires_human", False)),
            superseded_by=meta.get("superseded_by"),
        ))
    return group_by_phase(slices)


# Legacy regex stubs (the original §24 parser exported these as module
# constants; the test suite imports them). They no longer drive the
# discovery path but stay exported so older imports do not break.
PHASE_HEADER_RE = re.compile(r"^### Fase (\d+)\s*[—-]\s*(.+?)\s*$")
SLICE_RE = re.compile(r"^\s*\d+\.\s*\*\*([TFD][^\*]+?)\*\*\s*(.*)$")
PLAIN_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _default_plans_root() -> Path:
    """Resolve plans/ root from $AGENT_FARM_ROOT or relative to this file."""
    env = os.environ.get("AGENT_FARM_ROOT")
    if env:
        return Path(env) / "plans"
    # scripts/lib/plan_parser.py → ../../plans/
    return Path(__file__).resolve().parent.parent.parent / "plans"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--plans-root",
        default=None,
        help="path to plans/ directory (default: $AGENT_FARM_ROOT/plans)",
    )
    ap.add_argument(
        "--plan",
        default=None,
        help="deprecated; ignored. Plan store is walked from --plans-root.",
    )
    ap.add_argument("--db", required=True)
    ap.add_argument(
        "--phase",
        default=None,
        help="filter to one phase string (e.g. F-FARM-1, F1, TC)",
    )
    ap.add_argument(
        "--next",
        action="store_true",
        help="just the next pickable slice across all loops",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="machine-readable JSON output",
    )
    args = ap.parse_args(argv)

    plans_root = Path(args.plans_root) if args.plans_root else _default_plans_root()
    if args.plan and not args.plans_root:
        # Soft notice on stderr; do not break callers that still pass --plan.
        sys.stderr.write(
            "plan_parser: --plan is deprecated and ignored; "
            f"reading plans/<loop>/PLAN.md under {plans_root}\n"
        )

    if not plans_root.is_dir():
        sys.stderr.write(f"ERROR: plans root not a directory: {plans_root}\n")
        return 2

    slices = discover_slices(plans_root)
    task_state = fetch_task_status(args.db)
    phases = group_by_phase(slices)

    if args.next:
        nxt = find_next(slices, task_state)
        if nxt is None:
            print(
                "(no pickable slices — all loops have only blocked / "
                "requires-human / done slices)"
            )
            return 0
        if args.json:
            print(json.dumps(nxt, indent=2))
        else:
            print(
                f"Next: {nxt['loop']} loop, phase {nxt['phase']}, slice "
                f"{nxt['id']} ({nxt['priority']}) — {nxt['title']}"
            )
            spawn = json.dumps({"slice": nxt["id"], "phase": nxt["phase"]})
            print(
                f"Spawn:  bash scripts/spawn-subagent.sh executor '{spawn}'"
            )
        return 0

    if args.json:
        out = {
            "phases": phases,
            "task_state": task_state,
            "next": find_next(slices, task_state),
            "slices_by_loop": _count_by_loop(slices),
        }
        print(json.dumps(out, indent=2))
        return 0

    n_loops = len({s.loop for s in slices})
    print(
        f"=== plan progress (slices: {len(slices)} across {n_loops} loops; "
        f"touched by tasks: {len(task_state)}) ===\n"
    )
    print(render_text(slices, task_state, args.phase))
    nxt = find_next(slices, task_state)
    if nxt:
        print(
            f"NEXT PICKABLE: {nxt['loop']} loop, {nxt['id']} "
            f"({nxt['priority']}) — {nxt['title']}"
        )
    return 0


def _count_by_loop(slices: list[Slice]) -> dict[str, int]:
    out: dict[str, int] = {}
    for s in slices:
        out[s.loop] = out.get(s.loop, 0) + 1
    return out


if __name__ == "__main__":
    sys.exit(main())

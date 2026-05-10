#!/usr/bin/env python3
"""Build plans/PLAN.md from per-loop PLAN.md files.

Walks plans/<loop>/PLAN.md, parses every `### <title>` block whose body starts
with a fenced ```yaml frontmatter, and emits a master index with status
summary + per-loop / per-phase / per-priority / blocked / next-up views.

Usage:
  python plans/render.py             # write plans/PLAN.md
  python plans/render.py --check     # exit 1 if PLAN.md is stale (CI gate)
  python plans/render.py --next      # print next pickable slice per loop
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PLANS_DIR = Path(__file__).resolve().parent
LOOP_DIRS = [
    p for p in sorted(PLANS_DIR.iterdir())
    if p.is_dir() and (p / "PLAN.md").exists()
]
MASTER = PLANS_DIR / "PLAN.md"

SECTION_RX = re.compile(r"^### (.+?)\n```yaml\n(.+?)\n```\n(.*?)(?=^### |\Z)", re.M | re.S)
STATUS_ORDER = ["in_progress", "blocked", "pending", "done", "deferred"]
STATUS_GLYPH = {
    "pending": "⬜",
    "in_progress": "🟡",
    "blocked": "🟥",
    "done": "✅",
    "deferred": "⬛",
}


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
    body: str = ""
    source_file: Path | None = None

    @classmethod
    def parse(cls, title: str, frontmatter: str, body: str, source: Path) -> "Slice":
        meta = yaml.safe_load(frontmatter) or {}
        return cls(
            id=str(meta["id"]),
            title=title.strip(),
            loop=str(meta["loop"]),
            phase=str(meta.get("phase", "")),
            status=str(meta.get("status", "pending")),
            deps=list(meta.get("deps") or []),
            acceptance=str(meta.get("acceptance", "")),
            estimated_hours=meta.get("estimated_hours"),
            priority=str(meta.get("priority", "P2")),
            tags=list(meta.get("tags") or []),
            requires_human=bool(meta.get("requires_human", False)),
            superseded_by=meta.get("superseded_by"),
            body=body.strip(),
            source_file=source,
        )


def discover() -> list[Slice]:
    slices: list[Slice] = []
    seen_ids: set[str] = set()
    for loop_dir in LOOP_DIRS:
        plan = loop_dir / "PLAN.md"
        text = plan.read_text()
        loop_name = loop_dir.name
        for match in SECTION_RX.finditer(text):
            title, frontmatter, body = match.groups()
            try:
                s = Slice.parse(title, frontmatter, body, plan)
            except Exception as e:
                raise SystemExit(f"{plan}: failed to parse '### {title.strip()}' — {e}")
            if s.loop != loop_name:
                raise SystemExit(
                    f"{plan}: slice {s.id} declares loop={s.loop!r} "
                    f"but lives under loops/{loop_name}/"
                )
            if s.id in seen_ids:
                raise SystemExit(f"duplicate slice id: {s.id} (in {plan})")
            seen_ids.add(s.id)
            slices.append(s)
    return slices


def fmt_status_count(slices: list[Slice]) -> str:
    counts: dict[str, int] = {s: 0 for s in STATUS_ORDER}
    for s in slices:
        counts[s.status] = counts.get(s.status, 0) + 1
    parts = [f"{STATUS_GLYPH[k]} {v} {k}" for k, v in counts.items() if v]
    return " · ".join(parts) + f" · **total {len(slices)}**"


def view_by_loop(slices: list[Slice]) -> str:
    out = ["## By loop\n"]
    for loop_dir in LOOP_DIRS:
        loop = loop_dir.name
        loop_slices = [s for s in slices if s.loop == loop]
        if not loop_slices:
            continue
        out.append(f"### {loop} ({len(loop_slices)} slices)\n")
        out.append(fmt_status_count(loop_slices) + "\n")
        out.append("| id | phase | status | priority | title |")
        out.append("|---|---|---|---|---|")
        for s in sorted(loop_slices, key=lambda x: (STATUS_ORDER.index(x.status), x.phase, x.id)):
            link = f"[{s.id}]({loop}/PLAN.md#{slugify(s.title, s.id)})"
            out.append(f"| {link} | {s.phase} | {STATUS_GLYPH[s.status]} {s.status} | {s.priority} | {s.title} |")
        out.append("")
    return "\n".join(out)


def view_by_phase(slices: list[Slice]) -> str:
    by_phase: dict[str, list[Slice]] = {}
    for s in slices:
        by_phase.setdefault(s.phase or "(unphased)", []).append(s)
    out = ["## By phase\n"]
    for phase in sorted(by_phase.keys()):
        ss = by_phase[phase]
        out.append(f"### {phase} ({len(ss)} slices)\n")
        out.append(fmt_status_count(ss) + "\n")
    return "\n".join(out)


def view_next_up(slices: list[Slice]) -> str:
    done_ids = {s.id for s in slices if s.status == "done"}
    out = ["## Next up (per loop)\n"]
    for loop_dir in LOOP_DIRS:
        loop = loop_dir.name
        candidates = [
            s for s in slices
            if s.loop == loop
            and s.status == "pending"
            and not s.requires_human
            and all(d in done_ids for d in s.deps)
        ]
        candidates.sort(key=lambda x: (x.priority, x.phase, x.id))
        if not candidates:
            out.append(f"- **{loop}**: nothing pickable (blocked deps or all done / requires_human)\n")
            continue
        top = candidates[:3]
        out.append(f"- **{loop}**: " + " · ".join(f"`{s.id}` ({s.priority})" for s in top))
    return "\n".join(out)


def view_blocked(slices: list[Slice]) -> str:
    blocked = [s for s in slices if s.status == "blocked"]
    if not blocked:
        return "## Blocked\n\n_None._\n"
    out = ["## Blocked\n"]
    for s in blocked:
        out.append(f"- `{s.id}` ({s.loop}): {s.title}")
    return "\n".join(out)


def view_requires_human(slices: list[Slice]) -> str:
    rh = [s for s in slices if s.requires_human and s.status != "done"]
    if not rh:
        return ""
    out = ["## Requires human\n"]
    for s in sorted(rh, key=lambda x: (x.priority, x.id)):
        out.append(f"- `{s.id}` ({s.loop}, {s.priority}): {s.title}")
    return "\n".join(out)


def slugify(title: str, id_: str) -> str:
    """Match GitHub's auto-anchor: lower, strip punct, each space -> one hyphen."""
    raw = title.lower()
    raw = re.sub(r"[^\w\s-]", "", raw)
    raw = re.sub(r"\s", "-", raw)
    return raw.strip("-")


def render(slices: list[Slice]) -> str:
    parts = [
        "# agent-farm master plan",
        "",
        "_Auto-generated by `plans/render.py`. Do not edit by hand._",
        "_Edit per-loop PLAN.md files; rerun `python plans/render.py`._",
        "",
        f"**Status**: {fmt_status_count(slices)}",
        "",
        view_next_up(slices),
        "",
        view_by_loop(slices),
        view_by_phase(slices),
        view_blocked(slices),
        view_requires_human(slices),
    ]
    return "\n".join(parts).rstrip() + "\n"


def cmd_next(slices: list[Slice]) -> int:
    """Print next pickable slice per loop. Returns exit 0 always."""
    done = {s.id for s in slices if s.status == "done"}
    for loop_dir in LOOP_DIRS:
        loop = loop_dir.name
        cands = [
            s for s in slices
            if s.loop == loop and s.status == "pending"
            and not s.requires_human and all(d in done for d in s.deps)
        ]
        cands.sort(key=lambda x: (x.priority, x.phase, x.id))
        if cands:
            top = cands[0]
            print(f"{loop}: {top.id} | {top.priority} | phase={top.phase} | {top.title}")
        else:
            print(f"{loop}: <none>")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit 1 if PLAN.md is stale")
    parser.add_argument("--next", action="store_true", help="print next pickable slice per loop")
    args = parser.parse_args()

    slices = discover()

    if args.next:
        return cmd_next(slices)

    new_text = render(slices)
    if args.check:
        if not MASTER.exists() or MASTER.read_text() != new_text:
            print(f"{MASTER} is stale — run: python {Path(__file__).name}", file=sys.stderr)
            return 1
        print(f"{MASTER} up to date ({len(slices)} slices)")
        return 0

    MASTER.write_text(new_text)
    print(f"wrote {MASTER} ({len(slices)} slices)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

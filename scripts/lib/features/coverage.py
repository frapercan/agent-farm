"""Coverage check for the docs/features/ surface.

Algorithm:
1. Enumerate every "first-class capability" expected to have a feature
   page. The current sources of truth are:
     - agents/*.yaml (excluding _template.yaml)
     - scripts/services/*.sh
     - commands/agent-farm-*.md
     - the .github/workflows/*.yml CI gates
     - the top-level scripts entry points listed in
       `EXPECTED_TOP_LEVEL_SCRIPTS`
2. Enumerate every feature page under docs/features/*.md and its
   `source:` references.
3. A capability is covered if at least one feature page lists its path
   under `source:`.
4. Missing pages fail the check; unreferenced source paths in feature
   pages are warnings (some pages reference systemd units or
   third-party paths).

`EXPECTED_TOP_LEVEL_SCRIPTS` lists the scripts that must always have a
page. Adding a script: either add it here AND write the page, or get
explicit waiver in the PR (the gate is mechanical, the waiver is
operator judgment).
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


_FRONTMATTER_RX = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


# Scripts that must each have a feature page. Anything else under
# scripts/*.{sh,py} is allowed to live without a page (e.g. cron
# installers if we consciously choose not to surface them).
EXPECTED_TOP_LEVEL_SCRIPTS: tuple[str, ...] = (
    "scripts/init.sh",
    "scripts/spawn.sh",
    "scripts/spawn-subagent.sh",
    "scripts/finalize-subagent.sh",
    "scripts/status.sh",
    "scripts/kill.sh",
    "scripts/cleanup.sh",
    "scripts/launch-conductor.sh",
    "scripts/plan-progress.sh",
    "scripts/cost-report.sh",
    "scripts/install-dev-hooks.sh",
    "scripts/install-nightly-pgdump-cron.sh",
    "scripts/install-restore-drill-cron.sh",
    "scripts/restore-drill.sh",
    "scripts/apply-branch-protection.sh",
    "scripts/lint-reranker-tokens.py",
    "scripts/memory-prompt-drift.py",
    "scripts/janitor-systemic-check.sh",
    "scripts/render-features-index.sh",
    "scripts/check-features-coverage.sh",
)


def parse_sources(text: str) -> list[str]:
    match = _FRONTMATTER_RX.match(text)
    if not match:
        return []
    body = match.group(1)
    sources: list[str] = []
    in_source = False
    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        if not line:
            in_source = False
            continue
        if line.startswith("source:"):
            in_source = True
            tail = line[len("source:"):].strip()
            if tail and not tail.startswith("|"):
                sources.append(tail.strip('"'))
            continue
        if in_source and line.startswith("  - "):
            sources.append(line[4:].strip().strip('"'))
            continue
        if in_source and not line.startswith("  "):
            in_source = False
    return sources


def enumerate_capabilities(root: pathlib.Path) -> list[str]:
    caps: list[str] = []
    agents = sorted((root / "agents").glob("*.yaml"))
    for path in agents:
        if path.name == "_template.yaml":
            continue
        caps.append(f"agents/{path.name}")

    services = sorted((root / "scripts" / "services").glob("*.sh"))
    for path in services:
        caps.append(f"scripts/services/{path.name}")

    commands = sorted((root / "commands").glob("agent-farm-*.md"))
    for path in commands:
        caps.append(f"commands/{path.name}")

    workflows = sorted((root / ".github" / "workflows").glob("*.yml"))
    for path in workflows:
        caps.append(f".github/workflows/{path.name}")

    for entry in EXPECTED_TOP_LEVEL_SCRIPTS:
        if (root / entry).exists():
            caps.append(entry)

    return caps


def collect_sources(features_dir: pathlib.Path) -> dict[str, set[str]]:
    """Return {feature_page_filename: set(source_paths)}."""
    out: dict[str, set[str]] = {}
    for path in sorted(features_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        sources = parse_sources(path.read_text(encoding="utf-8"))
        out[path.name] = set(sources)
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Features coverage gate")
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    features_dir = args.root / "docs" / "features"
    if not features_dir.is_dir():
        print(f"coverage: {features_dir} not found", file=sys.stderr)
        return 1

    capabilities = enumerate_capabilities(args.root)
    page_sources = collect_sources(features_dir)
    all_sources: set[str] = set()
    for srcs in page_sources.values():
        all_sources.update(srcs)

    missing: list[str] = []
    for cap in capabilities:
        covered = any(cap.startswith(src.rstrip("/")) or src == cap or src.startswith(cap)
                      for src in all_sources)
        if not covered:
            missing.append(cap)

    # Reverse direction: source paths in feature pages that don't exist on disk
    orphan: list[tuple[str, str]] = []
    for page, srcs in page_sources.items():
        for src in srcs:
            stripped = src.rstrip("/")
            candidate = args.root / stripped
            if not candidate.exists():
                # Soft-allow paths that end with a slash (directories) or
                # paths under tests/ that exist (already covered above);
                # also allow README-hooks.md which lives under scripts/lib/.
                orphan.append((page, src))

    rc = 0
    if missing:
        print("coverage: missing feature pages for the following capabilities:")
        for cap in missing:
            print(f"  - {cap}")
        print(
            "\nAdd a docs/features/<name>.md referencing the path in its "
            "`source:` block, then re-run `bash scripts/render-features-index.sh`."
        )
        rc = 1

    if orphan:
        msg_kind = "ERROR" if args.strict else "warn"
        print(f"\ncoverage ({msg_kind}): source paths referenced by feature pages "
              "but missing on disk:")
        for page, src in orphan:
            print(f"  - {page}: {src}")
        if args.strict:
            rc = max(rc, 1)

    if rc == 0:
        print(f"coverage: ok ({len(capabilities)} capabilities, "
              f"{len(page_sources)} feature pages)")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""Tests for the docs/features/ surface and its CI gates."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import textwrap

import pytest


ROOT = pathlib.Path(__file__).resolve().parent.parent
FEATURES = ROOT / "docs" / "features"

# Importable helpers
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
from features import coverage as cov_mod  # noqa: E402
from features import render_index  # noqa: E402


def test_render_index_check_mode_passes():
    """The committed README must match what the renderer produces."""
    rc = subprocess.run(
        ["bash", str(ROOT / "scripts" / "render-features-index.sh"), "--check"],
        cwd=ROOT,
        check=False,
    ).returncode
    assert rc == 0, "docs/features/README.md is stale; run render-features-index.sh"


def test_coverage_gate_passes_on_main():
    """Coverage gate must pass on the committed state."""
    rc = subprocess.run(
        ["bash", str(ROOT / "scripts" / "check-features-coverage.sh")],
        cwd=ROOT,
        check=False,
    ).returncode
    assert rc == 0


def test_every_agent_has_a_feature_page():
    """Every non-template agent yaml has a feature page in source."""
    agents = sorted(p.stem for p in (ROOT / "agents").glob("*.yaml") if p.stem != "_template")
    page_sources: set[str] = set()
    for page in FEATURES.glob("*.md"):
        if page.name == "README.md":
            continue
        page_sources.update(cov_mod.parse_sources(page.read_text(encoding="utf-8")))
    missing = [a for a in agents if not any(f"agents/{a}.yaml" == src for src in page_sources)]
    assert not missing, f"agents without a feature page: {missing}"


def test_parse_frontmatter_handles_lists():
    sample = textwrap.dedent(
        """\
        ---
        name: x
        section: "1-agents"
        state: working
        source:
          - a.sh
          - b.py
        smoke: bash -n a.sh
        ---

        body
        """
    )
    meta = render_index.parse_frontmatter(sample)
    assert meta["name"] == "x"
    assert meta["section"] == "1-agents"
    assert meta["source"] == ["a.sh", "b.py"]


def test_parse_sources_returns_list_for_known_page():
    """Spot-check: the executor page lists agents/executor.yaml."""
    page = FEATURES / "executor.md"
    sources = cov_mod.parse_sources(page.read_text(encoding="utf-8"))
    assert "agents/executor.yaml" in sources


def test_coverage_flags_newly_dropped_agent(tmp_path):
    """If we add a fake agent yaml and don't write its page, the gate fails."""
    # Build a minimal copy of the relevant tree in tmp_path.
    fake_root = tmp_path / "farm"
    (fake_root / "agents").mkdir(parents=True)
    (fake_root / "scripts" / "services").mkdir(parents=True)
    (fake_root / "commands").mkdir(parents=True)
    (fake_root / ".github" / "workflows").mkdir(parents=True)
    (fake_root / "docs" / "features").mkdir(parents=True)

    (fake_root / "agents" / "_template.yaml").write_text("name: _template\n")
    (fake_root / "agents" / "ghost.yaml").write_text("name: ghost\n")
    # No feature page for ghost.

    rc = cov_mod.main(["--root", str(fake_root)])
    assert rc != 0, "coverage should fail when an agent lacks a feature page"


def test_coverage_passes_when_agent_has_page(tmp_path):
    """Sanity: with a matching feature page, the gate passes."""
    fake_root = tmp_path / "farm"
    (fake_root / "agents").mkdir(parents=True)
    (fake_root / "scripts" / "services").mkdir(parents=True)
    (fake_root / "commands").mkdir(parents=True)
    (fake_root / ".github" / "workflows").mkdir(parents=True)
    (fake_root / "docs" / "features").mkdir(parents=True)

    (fake_root / "agents" / "_template.yaml").write_text("name: _template\n")
    (fake_root / "agents" / "ghost.yaml").write_text("name: ghost\n")
    (fake_root / "docs" / "features" / "ghost.md").write_text(
        textwrap.dedent(
            """\
            ---
            name: ghost
            section: "1-agents"
            state: working
            source:
              - agents/ghost.yaml
            smoke: 'true'
            runbook: 'n/a'
            owner: 'n/a'
            ---

            body
            """
        )
    )

    rc = cov_mod.main(["--root", str(fake_root)])
    assert rc == 0


@pytest.mark.parametrize("page", sorted(FEATURES.glob("*.md")))
def test_no_em_dashes_in_publishable_prose(page):
    """CLAUDE.md hard constraint: no em-dashes in publishable prose."""
    if page.name == "README.md":
        # The README is auto-generated; double-check it too.
        text = page.read_text(encoding="utf-8")
    else:
        text = page.read_text(encoding="utf-8")
    # Allow the literal "--check" and "--apply" CLI flags + the YAML
    # frontmatter "---" delimiters.
    sanitised = text.replace("---", "").replace("--check", "").replace("--apply", "")
    sanitised = sanitised.replace("--strict", "").replace("--all", "")
    sanitised = sanitised.replace("--events", "").replace("--next", "")
    sanitised = sanitised.replace("--phase", "").replace("--dry-run", "")
    sanitised = sanitised.replace("--write", "").replace("--no-root", "")
    sanitised = sanitised.replace("--agent", "").replace("--help", "")
    assert "—" not in sanitised, f"em-dash in {page.name}"
    # The double-hyphen rule from CLAUDE.md: ban "--" in prose only.
    # Inline code (between backticks) and CLI examples are exempt; the
    # crude check above replaces the known flags, then asserts no stray.
    # Allow "--" inside fenced code blocks: strip them first.
    in_code = False
    leftover_lines: list[str] = []
    for line in sanitised.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        # Strip inline `code` runs.
        clean = ""
        in_inline = False
        for ch in line:
            if ch == "`":
                in_inline = not in_inline
                continue
            if not in_inline:
                clean += ch
        leftover_lines.append(clean)
    leftover = "\n".join(leftover_lines)
    assert "--" not in leftover, (
        f"double-hyphen in prose of {page.name} (CLAUDE.md hard rule)"
    )

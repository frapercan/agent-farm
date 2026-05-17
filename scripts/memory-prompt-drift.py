#!/usr/bin/env python3
"""Memory-to-prompt drift linter.

Scans the auto-memory directory for feedback_*.md and project_*.md files
that contain "How to apply" sections, then checks whether the actionable
phrases mentioned in those sections actually appear in the referenced
prompt files.

Purpose
-------
Memory files record lessons learned and write instructions like:

    "The prompt must include ..."
    "Update prompts/executor.md so ..."
    "Fold into prompts/janitor.md ..."

Over time, prompt files drift away from what the memory says they should
contain. This linter detects that drift and reports it as a JSON list of
stale entries.

Limitations
-----------
The detection is regex-based, not semantic. A memory entry that PARAPHRASES
what the prompt should say (rather than quoting an exact phrase or token)
will produce a false positive if the linter cannot match the paraphrase
to the actual prompt text. Convention going forward: when writing a "How to
apply" memory entry, use exact quoted phrases or inline code blocks for
tokens that MUST appear verbatim in the target prompt.

The linter is advisory-only (exit code 0 always). It does NOT modify any
memory or prompt file.

Slice: FARM-2.6 (farm-platform loop).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MEMORY_DIR = Path.home() / ".claude/projects/-home-frapercan-Thesis2/memory"
DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Section headings that mark a "How to apply" block.
# Matches: ## How to apply, **How to apply:**, **How to apply**, etc.
HOW_TO_APPLY_RE = re.compile(
    r"^(?:#{1,6}\s+|[*_]{1,2})how\s+to\s+apply[*_:]*",
    re.IGNORECASE | re.MULTILINE,
)

# The next heading or horizontal-rule marks the end of a "How to apply" section.
NEXT_SECTION_RE = re.compile(
    r"^(?:#{1,6}\s|\*{3,}|_{3,}|-{3,}|[*_]{1,2}\w)",
    re.MULTILINE,
)

# Patterns for actionable verb phrases.
# Group 1 = the phrase that must appear in the prompt (may be empty if only
# a file is named but no phrase is quoted).
# Group 2 = the prompt filename (may be empty if only a phrase is given).

# "the prompt must (include/contain/have) <phrase>"
# Optionally followed by "in <file>.md" or "in prompts/<file>.md"
# The regex captures: phrase (groups 1-4) + optional file reference (group 5).
MUST_PHRASE_RE = re.compile(
    r"the\s+prompt\s+must\s+(?:include|contain|have)?\s+"
    r"(?:[\"]([^\"]+)[\"]"        # double-quoted  (group 1)
    r"|[\']([^\']+)[\']"          # single-quoted  (group 2)
    r"|`([^`]+)`"                 # backtick       (group 3)
    r"|([A-Z_][A-Z0-9_]{2,}))"   # UPPER_CASE bare token (group 4)
    r"(?:[^.!\n]*?\bin\s+(?:prompts/)?(\w[\w.-]*\.md))?",  # optional "in <file>.md" (group 5)
    re.IGNORECASE,
)

# "update prompts/<file>" or "fold into prompts/<file>"
FILE_REF_RE = re.compile(
    r"(?:update|fold\s+into)\s+prompts/(\S+\.md)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_how_to_apply(text: str) -> str | None:
    """Return the text of the first 'How to apply' section, or None."""
    m = HOW_TO_APPLY_RE.search(text)
    if m is None:
        return None
    start = m.end()
    # Advance past the rest of that line.
    newline = text.find("\n", start)
    if newline == -1:
        return text[start:]
    body_start = newline + 1
    # Find where the next section heading begins.
    end_m = NEXT_SECTION_RE.search(text, body_start)
    if end_m is None:
        return text[body_start:]
    return text[body_start : end_m.start()]


def _extract_phrases(section_text: str) -> list[tuple[str, str | None]]:
    """Return list of (phrase, prompt_file_or_None) pairs from a section.

    Resolution priority for which prompt file to check:
    1. Inline "in <file>.md" on the same sentence as "the prompt must" (group 5).
    2. Section-level "update prompts/<file>" / "fold into prompts/<file>".
    3. None (scan all prompts).
    """
    results: list[tuple[str, str | None]] = []

    # Section-level file references: "update prompts/<file>" / "fold into prompts/<file>"
    section_file_refs = {m.group(1) for m in FILE_REF_RE.finditer(section_text)}

    # "the prompt must include X" patterns
    for m in MUST_PHRASE_RE.finditer(section_text):
        phrase = m.group(1) or m.group(2) or m.group(3) or m.group(4) or ""
        phrase = phrase.strip()
        if not phrase:
            continue

        # Priority 1: inline "in <file>.md" on the same sentence.
        inline_file = m.group(5)
        if inline_file:
            results.append((phrase, inline_file))
            continue

        # Priority 2: section-level file refs.
        if section_file_refs:
            for fp in sorted(section_file_refs):
                results.append((phrase, fp))
        else:
            results.append((phrase, None))

    return results


def _phrase_in_prompt(phrase: str, prompt_path: Path) -> bool:
    """Return True if phrase appears (case-insensitive) in prompt_path."""
    try:
        text = prompt_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return phrase.lower() in text.lower()


def _find_line_number(text: str, char_offset: int) -> int:
    """Return 1-based line number for a char offset in text."""
    return text.count("\n", 0, char_offset) + 1


# ---------------------------------------------------------------------------
# Core scan
# ---------------------------------------------------------------------------


def scan(memory_dir: Path, prompts_dir: Path) -> dict[str, Any]:
    """Run the full drift scan and return a result dict."""
    stale: list[dict[str, Any]] = []
    memory_files_scanned = 0
    prompts_checked: set[str] = set()

    patterns = list(memory_dir.glob("feedback_*.md")) + list(
        memory_dir.glob("project_*.md")
    )
    patterns.sort()

    for mem_path in patterns:
        try:
            text = mem_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(
                f"warning: cannot read {mem_path}: {exc}",
                file=sys.stderr,
            )
            continue

        memory_files_scanned += 1

        section = _extract_how_to_apply(text)
        if section is None:
            continue  # no "How to apply" block - skip gracefully

        pairs = _extract_phrases(section)
        if not pairs:
            continue

        # Find line offset of the "How to apply" heading for reporting.
        hta_match = HOW_TO_APPLY_RE.search(text)
        hta_line = _find_line_number(text, hta_match.start()) if hta_match else 0

        for phrase, prompt_file in pairs:
            if prompt_file:
                # Specific file named - check only that file.
                target_path = prompts_dir / prompt_file
                prompts_checked.add(prompt_file)
                found = _phrase_in_prompt(phrase, target_path)
                if not found:
                    stale.append(
                        {
                            "memory_file": str(mem_path),
                            "memory_line": hta_line,
                            "prompt_file": prompt_file,
                            "expected_phrase": phrase,
                        }
                    )
            else:
                # No specific file named - scan ALL prompts.
                any_found = False
                for candidate in sorted(prompts_dir.glob("*.md")):
                    prompts_checked.add(candidate.name)
                    if _phrase_in_prompt(phrase, candidate):
                        any_found = True
                        break
                if not any_found:
                    stale.append(
                        {
                            "memory_file": str(mem_path),
                            "memory_line": hta_line,
                            "prompt_file": None,
                            "expected_phrase": phrase,
                        }
                    )

    return {
        "stale_count": len(stale),
        "stale": stale,
        "memory_files_scanned": memory_files_scanned,
        "prompts_cross_checked": len(prompts_checked),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="memory-prompt-drift.py",
        description=(
            "Scan memory files for 'How to apply' blocks and report "
            "actionable phrases that are missing from the referenced "
            "prompt files."
        ),
    )
    parser.add_argument(
        "--memory-dir",
        type=Path,
        default=DEFAULT_MEMORY_DIR,
        metavar="DIR",
        help=(
            "Directory containing feedback_*.md and project_*.md memory "
            f"files. Default: {DEFAULT_MEMORY_DIR}"
        ),
    )
    parser.add_argument(
        "--prompts-dir",
        type=Path,
        default=DEFAULT_PROMPTS_DIR,
        metavar="DIR",
        help=(
            "Directory containing the prompt *.md files to check against. "
            f"Default: {DEFAULT_PROMPTS_DIR}"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON to stdout (always true; this flag is a no-op kept for compatibility).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the human one-line summary on stderr.",
    )
    args = parser.parse_args(argv)

    result = scan(
        memory_dir=args.memory_dir,
        prompts_dir=args.prompts_dir,
    )

    # JSON always goes to stdout.
    print(json.dumps(result, indent=2))

    # Human summary to stderr (unless --quiet).
    if not args.quiet:
        print(
            f"memory-prompt drift: {result['stale_count']} stale "
            f"entries; {result['memory_files_scanned']} memory files "
            f"scanned, {result['prompts_cross_checked']} prompts "
            f"cross-checked",
            file=sys.stderr,
        )

    # Advisory only - always exit 0.
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""scripts/lib/parse_claude_cost.py — FARM-2.2 cost-line parser.

Extracts token, cost, duration, and model info from a Claude CLI run.

The Claude CLI (`claude -p ... --output-format stream-json --verbose`)
emits a final JSONL line `{"type":"result", ...}` with everything we need:

    {
      "type": "result",
      "subtype": "success",
      "duration_ms": 2887,                    # wall clock
      "duration_api_ms": 3970,
      "session_id": "...",
      "total_cost_usd": 0.0882025,
      "usage": {
        "input_tokens": 6,
        "cache_creation_input_tokens": 12524,
        "cache_read_input_tokens": 18489,
        "output_tokens": 6,
        ...
      },
      "modelUsage": {
        "claude-opus-4-7": {"inputTokens": ..., "outputTokens": ...,
                            "costUSD": ..., "contextWindow": ...},
        "claude-haiku-4-5-...": {...}
      },
      ...
    }

This module also handles a legacy plain-text summary form (one Claude CLI
release surfaced a "Total cost: $X" / "Total duration (wall): Xs" block on
stderr; we keep a parser for it as a fallback for older capture files).

Output: a dict with these keys, omitting any that didn't parse:
  - input_tokens     (int)
  - output_tokens    (int)
  - cache_tokens     (int; cache_create + cache_read)
  - usd_estimate     (float)
  - duration_seconds (float; wall clock)
  - model            (str; the model that did the most output tokens, or
                      the only model if there's just one)

Usage from the CLI:
  python3 parse_claude_cost.py <file>
  python3 parse_claude_cost.py --stdin   # read text from stdin

Exit 0 always (best-effort; missing fields are silently omitted). Prints
the resulting JSON on stdout.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# JSONL stream-json parser (Claude CLI canonical output today)
# ---------------------------------------------------------------------------


def _find_result_json(text: str) -> dict[str, Any] | None:
    """Return the final {"type":"result"} object embedded in a Claude CLI
    stream-json capture, or None if none is present.

    Tolerates partial / interleaved output: scans line by line, picking the
    *last* parseable `type=result` JSON object.
    """
    last: dict[str, Any] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("{") or '"type"' not in line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("type") == "result":
            last = obj
    return last


def _pick_dominant_model(model_usage: dict[str, Any]) -> str | None:
    """Pick the model the user paid the most for.

    Subagents pin a single model in spec, but Claude CLI reports a tiny
    haiku side-call alongside the main opus/sonnet work (slash-command
    routing, status-line model, etc). The dominant-by-cost heuristic
    returns the model that owns the bulk of the spend, which is what the
    cost-rollup dashboard cares about.

    Falls back to output-tokens, then to first key, if costUSD is missing.
    """
    if not isinstance(model_usage, dict) or not model_usage:
        return None
    best_name: str | None = None
    best_cost: float = -1.0
    cost_seen = False
    for name, info in model_usage.items():
        if not isinstance(info, dict):
            continue
        cost = info.get("costUSD")
        if isinstance(cost, (int, float)):
            cost_seen = True
            if float(cost) > best_cost:
                best_cost = float(cost)
                best_name = name
    if cost_seen and best_name is not None:
        return best_name

    # Fallback: largest output_tokens.
    best_output: int = -1
    for name, info in model_usage.items():
        if not isinstance(info, dict):
            continue
        out = info.get("outputTokens")
        if isinstance(out, int) and out > best_output:
            best_output = out
            best_name = name
    return best_name if best_name is not None else next(iter(model_usage), None)


def _from_result_json(obj: dict[str, Any]) -> dict[str, Any]:
    """Project a Claude CLI `type=result` object into our metrics schema."""
    out: dict[str, Any] = {}

    usage = obj.get("usage")
    if isinstance(usage, dict):
        if isinstance(usage.get("input_tokens"), int):
            out["input_tokens"] = usage["input_tokens"]
        if isinstance(usage.get("output_tokens"), int):
            out["output_tokens"] = usage["output_tokens"]
        cache_create = usage.get("cache_creation_input_tokens")
        cache_read = usage.get("cache_read_input_tokens")
        cache_total: int | None = None
        if isinstance(cache_create, int):
            cache_total = cache_create
        if isinstance(cache_read, int):
            cache_total = (cache_total or 0) + cache_read
        if cache_total is not None:
            out["cache_tokens"] = cache_total

    if isinstance(obj.get("total_cost_usd"), (int, float)):
        out["usd_estimate"] = float(obj["total_cost_usd"])

    if isinstance(obj.get("duration_ms"), (int, float)):
        out["duration_seconds"] = round(obj["duration_ms"] / 1000.0, 3)

    model_usage = obj.get("modelUsage")
    if isinstance(model_usage, dict):
        m = _pick_dominant_model(model_usage)
        if m:
            out["model"] = m

    return out


# ---------------------------------------------------------------------------
# Plain-text fallback parser (legacy "Total cost: $X" CLI surface)
# ---------------------------------------------------------------------------


_RX_COST = re.compile(
    r"^\s*Total cost:?\s*\$?\s*([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE | re.MULTILINE,
)
_RX_WALL = re.compile(
    r"Total duration \(wall\):\s*([0-9]+(?:\.[0-9]+)?)\s*s",
    re.IGNORECASE,
)
_RX_USAGE_LINE = re.compile(
    # Pattern like:
    #   claude-opus-4-7: 5.2k input, 1.1k output, 23.4k cache create, 100k cache read
    r"^\s*([a-z0-9._-]+):\s*"
    r"([0-9.]+)\s*([kKmM]?)\s*input,?\s*"
    r"([0-9.]+)\s*([kKmM]?)\s*output"
    r"(?:,?\s*([0-9.]+)\s*([kKmM]?)\s*cache\s*create)?"
    r"(?:,?\s*([0-9.]+)\s*([kKmM]?)\s*cache\s*read)?",
    re.IGNORECASE,
)


def _expand_suffix(value: str, suffix: str) -> int:
    """Convert "5.2k" / "1.1m" to a plain int. Empty suffix means literal."""
    n = float(value)
    s = (suffix or "").lower()
    if s == "k":
        n *= 1_000
    elif s == "m":
        n *= 1_000_000
    return int(round(n))


def _from_text_summary(text: str) -> dict[str, Any]:
    """Parse the legacy plain-text Claude CLI summary block.

    Returns whatever fields we could read; tolerates missing/garbage lines.
    """
    out: dict[str, Any] = {}
    cost_m = _RX_COST.search(text)
    if cost_m:
        try:
            out["usd_estimate"] = float(cost_m.group(1))
        except ValueError:
            pass

    wall_m = _RX_WALL.search(text)
    if wall_m:
        try:
            out["duration_seconds"] = float(wall_m.group(1))
        except ValueError:
            pass

    # "Usage by model:" block — pick the dominant line (most output tokens).
    best: tuple[str, int, dict[str, int]] | None = None
    for line in text.splitlines():
        m = _RX_USAGE_LINE.match(line)
        if not m:
            continue
        model = m.group(1)
        # Filter common non-model header words.
        if model.lower() in {"usage", "total"}:
            continue
        try:
            in_tok = _expand_suffix(m.group(2), m.group(3))
            out_tok = _expand_suffix(m.group(4), m.group(5))
        except (TypeError, ValueError):
            continue
        cache_tok = 0
        if m.group(6):
            try:
                cache_tok += _expand_suffix(m.group(6), m.group(7) or "")
            except (TypeError, ValueError):
                pass
        if m.group(8):
            try:
                cache_tok += _expand_suffix(m.group(8), m.group(9) or "")
            except (TypeError, ValueError):
                pass
        fields = {
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cache_tokens": cache_tok,
        }
        if best is None or out_tok > best[1]:
            best = (model, out_tok, fields)

    if best is not None:
        out["model"] = best[0]
        out.update(best[2])

    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse(text: str) -> dict[str, Any]:
    """Best-effort parse. Tries the canonical stream-json result line
    first, then falls back to the legacy text summary if no JSON result
    was found.

    Returns a dict with whichever of these keys could be extracted:
      input_tokens, output_tokens, cache_tokens, usd_estimate,
      duration_seconds, model. Never raises.
    """
    if not text:
        return {}
    obj = _find_result_json(text)
    if obj is not None:
        parsed = _from_result_json(obj)
        if parsed:
            return parsed
    return _from_text_summary(text)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _read_input(argv: list[str]) -> str:
    if len(argv) >= 2 and argv[1] == "--stdin":
        return sys.stdin.read()
    if len(argv) >= 2 and argv[1] not in {"-h", "--help"}:
        path = Path(argv[1])
        if not path.is_file():
            print(f"error: not a file: {path}", file=sys.stderr)
            sys.exit(2)
        return path.read_text(errors="replace")
    print(__doc__, file=sys.stderr)
    sys.exit(2)


def main(argv: list[str]) -> int:
    text = _read_input(argv)
    result = parse(text)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

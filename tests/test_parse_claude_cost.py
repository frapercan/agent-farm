"""Tests for scripts/lib/parse_claude_cost.py (FARM-2.2).

Verifies the parser against:
1. A real Claude CLI stream-json capture (tests/fixtures/parse_claude_cost/
   stream_json_success.jsonl, captured live during slice development).
2. Synthetic stream-json fixtures (minimal, two-model dominance).
3. The legacy plain-text "Total cost: $X" summary form.
4. Garbage/empty input: parser never crashes, returns empty dict.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import parse_claude_cost as pcc  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "parse_claude_cost"
PARSER_PY = REPO_ROOT / "scripts" / "lib" / "parse_claude_cost.py"


# ---------------------------------------------------------------------------
# JSONL stream-json path
# ---------------------------------------------------------------------------


class TestStreamJsonParser:
    def test_real_capture_has_all_fields(self) -> None:
        text = (FIXTURES / "stream_json_success.jsonl").read_text()
        out = pcc.parse(text)
        # Every canonical field must be populated for a healthy real capture.
        for key in (
            "input_tokens",
            "output_tokens",
            "cache_tokens",
            "usd_estimate",
            "duration_seconds",
            "model",
        ):
            assert key in out, f"missing {key} in {out}"
        assert isinstance(out["input_tokens"], int)
        assert isinstance(out["output_tokens"], int)
        assert isinstance(out["cache_tokens"], int)
        assert isinstance(out["usd_estimate"], float)
        assert isinstance(out["duration_seconds"], float)
        assert isinstance(out["model"], str)
        # The captured fixture used opus (we asked Claude opus to reply
        # one-word). costUSD-dominance must pick opus, not the cheap
        # haiku side-call.
        assert "opus" in out["model"].lower()

    def test_minimal_single_model(self) -> None:
        text = (FIXTURES / "stream_json_minimal.jsonl").read_text()
        out = pcc.parse(text)
        assert out == {
            "input_tokens": 100,
            "output_tokens": 20,
            "cache_tokens": 2500,  # 500 create + 2000 read
            "usd_estimate": 0.05,
            "duration_seconds": 5.0,
            "model": "claude-opus-4-7",
        }

    def test_two_models_picks_dominant_by_cost(self) -> None:
        # The Haiku side-call has MORE output_tokens (11 vs 6) but COSTS
        # ~170x less. Dominant-by-cost must pick opus.
        text = (FIXTURES / "stream_json_two_models.jsonl").read_text()
        out = pcc.parse(text)
        assert out["model"] == "claude-opus-4-7"
        assert out["usd_estimate"] == pytest.approx(0.0882025)

    def test_picks_last_result_line(self) -> None:
        # If by accident two result-lines appear, the LAST one wins (it's
        # the actual end-of-run summary).
        text = (
            '{"type":"result","subtype":"success","duration_ms":1000,'
            '"total_cost_usd":0.01,"usage":{"input_tokens":1,"output_tokens":1,'
            '"cache_creation_input_tokens":0,"cache_read_input_tokens":0},'
            '"modelUsage":{"claude-x":{"inputTokens":1,"outputTokens":1,"costUSD":0.01}}}\n'
            '{"type":"result","subtype":"success","duration_ms":2000,'
            '"total_cost_usd":0.02,"usage":{"input_tokens":2,"output_tokens":2,'
            '"cache_creation_input_tokens":0,"cache_read_input_tokens":0},'
            '"modelUsage":{"claude-x":{"inputTokens":2,"outputTokens":2,"costUSD":0.02}}}\n'
        )
        out = pcc.parse(text)
        assert out["usd_estimate"] == 0.02
        assert out["duration_seconds"] == 2.0


# ---------------------------------------------------------------------------
# Text fallback path
# ---------------------------------------------------------------------------


class TestTextSummaryParser:
    def test_text_summary_full(self) -> None:
        text = (FIXTURES / "text_summary.txt").read_text()
        out = pcc.parse(text)
        assert out["usd_estimate"] == pytest.approx(0.1234)
        assert out["duration_seconds"] == pytest.approx(45.6)
        # opus dominates by output tokens (1.1k vs 50)
        assert out["model"] == "claude-opus-4-7"
        assert out["input_tokens"] == 5_200
        assert out["output_tokens"] == 1_100
        # 23.4k create + 100k read = 123_400
        assert out["cache_tokens"] == 123_400

    def test_text_summary_partial(self) -> None:
        text = "Total cost: $0.5\nnothing else useful\n"
        out = pcc.parse(text)
        assert out == {"usd_estimate": 0.5}


# ---------------------------------------------------------------------------
# Robustness: never crashes
# ---------------------------------------------------------------------------


class TestRobustness:
    def test_empty(self) -> None:
        assert pcc.parse("") == {}

    def test_garbage(self) -> None:
        text = (FIXTURES / "garbage.txt").read_text()
        # Must not crash; returns empty dict (no usable signal).
        out = pcc.parse(text)
        assert out == {}

    def test_result_missing_usage(self) -> None:
        # CLI returned a result line but no usage block — parse what's
        # there, omit what isn't.
        text = (
            '{"type":"result","subtype":"success","duration_ms":1500,'
            '"total_cost_usd":0.03,"modelUsage":'
            '{"claude-haiku":{"inputTokens":10,"outputTokens":5,"costUSD":0.03}}}'
        )
        out = pcc.parse(text)
        assert out["duration_seconds"] == 1.5
        assert out["usd_estimate"] == 0.03
        assert out["model"] == "claude-haiku"
        assert "input_tokens" not in out
        assert "output_tokens" not in out
        assert "cache_tokens" not in out

    def test_result_no_modelusage(self) -> None:
        text = (
            '{"type":"result","subtype":"success","duration_ms":1000,'
            '"total_cost_usd":0.01,"usage":{"input_tokens":5,"output_tokens":5,'
            '"cache_creation_input_tokens":0,"cache_read_input_tokens":0}}'
        )
        out = pcc.parse(text)
        assert "model" not in out
        assert out["input_tokens"] == 5

    def test_non_dict_result_ignored(self) -> None:
        # `type: result` but the JSON isn't an object — must not crash.
        text = '[1, 2, 3]\n{"not_result": true}\n'
        assert pcc.parse(text) == {}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


class TestCli:
    def _run(self, *args: str, stdin_text: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(PARSER_PY), *args],
            check=False,
            capture_output=True,
            text=True,
            input=stdin_text,
        )

    def test_cli_file(self) -> None:
        res = self._run(str(FIXTURES / "stream_json_minimal.jsonl"))
        assert res.returncode == 0, res.stderr
        out = json.loads(res.stdout)
        assert out["usd_estimate"] == 0.05
        assert out["model"] == "claude-opus-4-7"

    def test_cli_stdin(self) -> None:
        text = (FIXTURES / "stream_json_minimal.jsonl").read_text()
        res = self._run("--stdin", stdin_text=text)
        assert res.returncode == 0, res.stderr
        assert json.loads(res.stdout)["usd_estimate"] == 0.05

    def test_cli_no_args_errors(self) -> None:
        res = self._run()
        assert res.returncode == 2

    def test_cli_missing_file(self) -> None:
        res = self._run(str(FIXTURES / "does-not-exist.jsonl"))
        assert res.returncode == 2

    def test_cli_empty_input(self) -> None:
        res = self._run("--stdin", stdin_text="")
        assert res.returncode == 0
        assert json.loads(res.stdout) == {}

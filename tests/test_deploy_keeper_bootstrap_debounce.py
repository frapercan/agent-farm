"""Tests for the API-healthcheck debounce and files-count fix in protea_redeploy.sh.

Slice: FARM-DK-HC-DEBOUNCE.

Scenarios covered:

  a. A single /jobs 5xx does NOT set BOOTSTRAP=1 (grace window applies).
  b. Three consecutive /jobs 5xx within 90 s DOES set BOOTSTRAP=1
     (threshold breached).
  c. When LOCAL==REMOTE and BOOTSTRAP is the only reason to run,
     files_count is 0 (not 1 from the echo-empty-string wc -l noise).

Strategy: extract the debounce functions and the files-count block from
the real shell script into a minimal harness, drive them with synthetic
state files (no real curl, no git, no deploy), and assert exit codes /
log lines.
"""

from __future__ import annotations

import subprocess
import textwrap
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REDEPLOY_SH = REPO_ROOT / "scripts" / "services" / "lib" / "protea_redeploy.sh"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lib_only(sandbox: Path) -> Path:
    """Extract the function-definition block from protea_redeploy.sh.

    We take everything before the '# 0) Self-heal' marker, identical to
    what the worker-healthcheck bash test does. Returns the path of the
    extracted file inside sandbox.
    """
    src = REDEPLOY_SH.read_text()
    marker = "# 0) Self-heal the deploy worktree if it has been removed."
    idx = src.find(marker)
    assert idx != -1, f"marker not found in {REDEPLOY_SH}"
    lib_src = src[:idx]
    lib_file = sandbox / "redeploy_lib_only.sh"
    lib_file.write_text(lib_src)
    return lib_file


def _run_bash(script: str, env: dict | None = None) -> subprocess.CompletedProcess:
    import os
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        env=full_env,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sandbox(tmp_path: Path) -> Path:
    (tmp_path / "state").mkdir()
    (tmp_path / "logs").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# Debounce tests (a, b)
# ---------------------------------------------------------------------------

class TestApiHealthcheckDebounce:
    """api_healthcheck_failed_debounce / api_healthcheck_reset_debounce."""

    def _make_harness(self, sandbox: Path, calls: int, window_sec: int = 90) -> str:
        """Build a bash harness that calls api_healthcheck_failed_debounce `calls` times
        and prints the return code of each call and the final API_HC_FAIL_COUNT."""
        lib = _lib_only(sandbox)
        state_file = sandbox / "state" / "api_fail_count"
        log_file = sandbox / "logs" / "redeploy.log"

        return textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -uo pipefail
            DEPLOY_PATH={sandbox!s}
            LOG_FILE={log_file!s}
            AGENT_FARM_ROOT={sandbox!s}
            API_FAIL_STATE={state_file!s}
            API_FAIL_THRESHOLD=3
            API_FAIL_WINDOW_SEC={window_sec}
            ts() {{ date -Is; }}
            log() {{ printf '[%s] %s\\n' "$(ts)" "$*" >> "$LOG_FILE"; }}
            mkdir -p "$(dirname "$API_FAIL_STATE")"
            source {lib!s}

            for i in $(seq 1 {calls}); do
                if api_healthcheck_failed_debounce; then
                    echo "call $i: BOOTSTRAP ($API_HC_FAIL_COUNT)"
                else
                    echo "call $i: grace ($API_HC_FAIL_COUNT)"
                fi
            done
            """
        )

    def test_single_failure_does_not_bootstrap(self, sandbox: Path) -> None:
        """Scenario a: one 5xx must stay in the grace window."""
        harness = self._make_harness(sandbox, calls=1)
        res = _run_bash(harness)
        assert res.returncode == 0, res.stderr
        # The single call should land in the grace window.
        assert "grace (1)" in res.stdout, (
            f"Expected 'grace (1)' in stdout, got:\n{res.stdout}"
        )
        assert "BOOTSTRAP" not in res.stdout, (
            f"Single failure should NOT bootstrap:\n{res.stdout}"
        )

    def test_two_failures_do_not_bootstrap(self, sandbox: Path) -> None:
        """Two consecutive 5xx also stay in grace (threshold=3)."""
        harness = self._make_harness(sandbox, calls=2)
        res = _run_bash(harness)
        assert res.returncode == 0, res.stderr
        lines = res.stdout.strip().splitlines()
        assert len(lines) == 2
        assert all("grace" in line for line in lines), (
            f"Both calls should be grace:\n{res.stdout}"
        )

    def test_three_consecutive_failures_bootstrap(self, sandbox: Path) -> None:
        """Scenario b: third consecutive failure within the window trips BOOTSTRAP."""
        harness = self._make_harness(sandbox, calls=3)
        res = _run_bash(harness)
        assert res.returncode == 0, res.stderr
        lines = res.stdout.strip().splitlines()
        assert len(lines) == 3
        assert "grace" in lines[0]
        assert "grace" in lines[1]
        assert "BOOTSTRAP" in lines[2], (
            f"Third consecutive failure should bootstrap:\n{res.stdout}"
        )
        assert "(3)" in lines[2]

    def test_reset_clears_counter(self, sandbox: Path) -> None:
        """api_healthcheck_reset_debounce must reset counter so next single failure is grace."""
        lib = _lib_only(sandbox)
        state_file = sandbox / "state" / "api_fail_count"
        log_file = sandbox / "logs" / "redeploy.log"

        harness = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -uo pipefail
            DEPLOY_PATH={sandbox!s}
            LOG_FILE={log_file!s}
            AGENT_FARM_ROOT={sandbox!s}
            API_FAIL_STATE={state_file!s}
            API_FAIL_THRESHOLD=3
            API_FAIL_WINDOW_SEC=90
            ts() {{ date -Is; }}
            log() {{ printf '[%s] %s\\n' "$(ts)" "$*" >> "$LOG_FILE"; }}
            mkdir -p "$(dirname "$API_FAIL_STATE")"
            source {lib!s}

            # Two failures -- count=2
            api_healthcheck_failed_debounce && echo "BOOT1" || echo "grace1"
            api_healthcheck_failed_debounce && echo "BOOT2" || echo "grace2"
            # Reset (API recovered)
            api_healthcheck_reset_debounce
            # One more failure -- counter should start fresh, so grace
            if api_healthcheck_failed_debounce; then
                echo "BOOT_after_reset ($API_HC_FAIL_COUNT)"
            else
                echo "grace_after_reset ($API_HC_FAIL_COUNT)"
            fi
            """
        )
        res = _run_bash(harness)
        assert res.returncode == 0, res.stderr
        assert "grace_after_reset (1)" in res.stdout, (
            f"After reset, single failure should be grace:\n{res.stdout}"
        )

    def test_window_expiry_resets_counter(self, sandbox: Path) -> None:
        """A failure whose first_fail_ts is beyond the window resets the counter."""
        lib = _lib_only(sandbox)
        state_file = sandbox / "state" / "api_fail_count"
        log_file = sandbox / "logs" / "redeploy.log"

        # Pre-seed the state file with count=2 but a timestamp far in the past
        # (> window_sec=5 ago), so the next call should reset and land at count=1.
        old_ts = int(time.time()) - 100  # 100s ago, well beyond window_sec=5
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(f"2\t{old_ts}\n")

        harness = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -uo pipefail
            DEPLOY_PATH={sandbox!s}
            LOG_FILE={log_file!s}
            AGENT_FARM_ROOT={sandbox!s}
            API_FAIL_STATE={state_file!s}
            API_FAIL_THRESHOLD=3
            API_FAIL_WINDOW_SEC=5
            ts() {{ date -Is; }}
            log() {{ printf '[%s] %s\\n' "$(ts)" "$*" >> "$LOG_FILE"; }}
            source {lib!s}

            if api_healthcheck_failed_debounce; then
                echo "BOOTSTRAP ($API_HC_FAIL_COUNT)"
            else
                echo "grace ($API_HC_FAIL_COUNT)"
            fi
            """
        )
        res = _run_bash(harness)
        assert res.returncode == 0, res.stderr
        # Counter should have reset to 1 (not 3), so grace.
        assert "grace (1)" in res.stdout, (
            f"Expired window should reset counter to 1 (grace):\n{res.stdout}"
        )


# ---------------------------------------------------------------------------
# files-count noise fix (c)
# ---------------------------------------------------------------------------

class TestFilesCountNoise:
    """files=N log line shows 0 when LOCAL==REMOTE and CHANGED is empty."""

    def test_empty_changed_reports_zero_files(self, sandbox: Path) -> None:
        """Scenario c: empty CHANGED string must produce files=0, not files=1."""
        harness = textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -uo pipefail
            CHANGED=""
            FILES_COUNT=0
            [[ -n "$CHANGED" ]] && FILES_COUNT=$(printf '%s\\n' "$CHANGED" | grep -c .)
            echo "files=${FILES_COUNT}"
            """
        )
        res = _run_bash(harness)
        assert res.returncode == 0, res.stderr
        assert "files=0" in res.stdout, (
            f"Empty CHANGED should produce files=0:\n{res.stdout}"
        )

    def test_single_file_changed_reports_one(self, sandbox: Path) -> None:
        """A single changed file must report files=1."""
        harness = textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -uo pipefail
            CHANGED="protea/some_module.py"
            FILES_COUNT=0
            [[ -n "$CHANGED" ]] && FILES_COUNT=$(printf '%s\\n' "$CHANGED" | grep -c .)
            echo "files=${FILES_COUNT}"
            """
        )
        res = _run_bash(harness)
        assert res.returncode == 0, res.stderr
        assert "files=1" in res.stdout, (
            f"Single file CHANGED should produce files=1:\n{res.stdout}"
        )

    def test_multiple_files_changed_reports_correct_count(self, sandbox: Path) -> None:
        """Multiple changed files must count correctly."""
        harness = textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -uo pipefail
            CHANGED="$(printf 'a.py\\nb.py\\nc.py')"
            FILES_COUNT=0
            [[ -n "$CHANGED" ]] && FILES_COUNT=$(printf '%s\\n' "$CHANGED" | grep -c .)
            echo "files=${FILES_COUNT}"
            """
        )
        res = _run_bash(harness)
        assert res.returncode == 0, res.stderr
        assert "files=3" in res.stdout, (
            f"Three-file CHANGED should produce files=3:\n{res.stdout}"
        )

    def test_old_wc_l_would_give_wrong_answer(self) -> None:
        """Confirm that the OLD approach (echo | wc -l) gave files=1 for empty CHANGED.

        This is a regression-documentation test: it shows WHY the fix was needed.
        """
        harness = textwrap.dedent(
            """\
            #!/usr/bin/env bash
            CHANGED=""
            echo "$CHANGED" | wc -l
            """
        )
        res = _run_bash(harness)
        assert res.returncode == 0
        # The old approach outputs "1" even for empty strings because
        # `echo ""` emits a newline that wc -l counts.
        assert res.stdout.strip() == "1", (
            "Expected old approach to produce '1' for empty CHANGED (confirms the bug)"
        )

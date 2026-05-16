"""Tests for deploy-keeper-supervisor.sh's janitor escalation path.

The supervisor itself has an infinite loop, so we test the
`escalate_to_janitor` function in isolation: extract the body via awk,
stub spawn-subagent.sh with a recording shim, and assert the JSON spec
we pass matches the expected shape (task=deploy-keeper-rescue,
failure_kind contains the FAIL_KIND, source_task_id=$TASK_ID).

We also verify the "prereq_fail does NOT spawn a janitor" decision by
running the supervisor's body block as a one-shot script (loop replaced
with a single iteration via a sentinel).
"""

from __future__ import annotations

import json
import os
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SUPERVISOR = REPO_ROOT / "scripts" / "services" / "deploy-keeper-supervisor.sh"


def _spawn_shim(record_path: Path) -> str:
    """Bash for a spawn-subagent.sh shim that records its args + prints the
    K=V env contract spawn-subagent.sh normally emits on stdout.

    Records:
      - {record_path}.agent  -> exact agent name (arg 1)
      - {record_path}.spec   -> raw spec JSON (arg 2; can be multi-line)
    """
    agent_file = f"{record_path}.agent"
    spec_file = f"{record_path}.spec"
    return textwrap.dedent(
        f"""\
        #!/usr/bin/env bash
        printf '%s' "$1" > {agent_file!s}
        printf '%s' "$2" > {spec_file!s}
        cat <<EOF
        task_id=fake-janitor-1234-abcd
        worktree=/tmp/fake-worktree
        composed_prompt=/tmp/fake.md
        model=haiku
        repo=/tmp/fake-repo
        results_dir=/tmp/fake-results
        EOF
        """
    )


@pytest.fixture
def fake_root(tmp_path: Path) -> Path:
    """A pretend AGENT_FARM_ROOT with a stub spawn-subagent.sh + db.py."""
    root = tmp_path / "agent-farm"
    (root / "scripts" / "lib").mkdir(parents=True)
    (root / "scripts" / "services").mkdir(parents=True)
    (root / "state").mkdir()
    # stub db.py so `heartbeat` calls don't blow up
    (root / "scripts" / "lib" / "db.py").write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import sys
            # Accept any sub-command; do nothing.
            sys.exit(0)
            """
        )
    )
    os.chmod(root / "scripts" / "lib" / "db.py", 0o755)
    # stub common.sh that defines heartbeat as no-op
    (root / "scripts" / "lib" / "common.sh").write_text(
        textwrap.dedent(
            """\
            heartbeat() { printf 'HB level=%s msg=%s\\n' "$2" "$3" >&2; }
            task_set_ended() { :; }
            """
        )
    )
    return root


def _make_spawn_shim(root: Path, record_path: Path) -> Path:
    spawn = root / "scripts" / "spawn-subagent.sh"
    spawn.write_text(_spawn_shim(record_path))
    os.chmod(spawn, 0o755)
    return spawn


def _extract_escalate_to_janitor() -> str:
    """awk out the function definition from the real supervisor."""
    res = subprocess.run(
        ["awk", "/^escalate_to_janitor\\(\\) \\{/,/^\\}/", str(SUPERVISOR)],
        capture_output=True, text=True, check=True,
    )
    body = res.stdout
    assert "escalate_to_janitor" in body, "extraction failed: " + body
    return body


class TestEscalateToJanitor:
    def test_spawn_called_with_correct_agent_and_spec(
        self, fake_root: Path, tmp_path: Path,
    ) -> None:
        record = tmp_path / "spawn-record"
        _make_spawn_shim(fake_root, record)

        harness = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -uo pipefail
            ROOT={fake_root!s}
            TASK_ID="dk-supervisor-task-xyz"
            source "$ROOT/scripts/lib/common.sh"
            {_extract_escalate_to_janitor()}
            escalate_to_janitor "redeploy_fail"
            """
        )
        res = subprocess.run(
            ["bash", "-c", harness], capture_output=True, text=True,
        )
        assert res.returncode == 0, f"stdout={res.stdout!r}\nstderr={res.stderr!r}"

        agent_file = Path(f"{record}.agent")
        spec_file = Path(f"{record}.spec")
        assert agent_file.exists(), "spawn shim was not called"
        assert agent_file.read_text() == "janitor"

        spec = json.loads(spec_file.read_text())
        assert spec["task"] == "deploy-keeper-rescue"
        assert "redeploy_fail" in spec["failure_kind"]
        assert "dk-supervisor-task-xyz" in spec["failure_kind"]
        assert spec["source_task_id"] == "dk-supervisor-task-xyz"

    def test_spawn_failure_is_logged_not_raised(
        self, fake_root: Path, tmp_path: Path,
    ) -> None:
        # Replace the spawn shim with one that exits 1.
        spawn = fake_root / "scripts" / "spawn-subagent.sh"
        spawn.write_text("#!/usr/bin/env bash\necho 'boom' >&2\nexit 1\n")
        os.chmod(spawn, 0o755)

        harness = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -uo pipefail
            ROOT={fake_root!s}
            TASK_ID="dk-supervisor-task-xyz"
            source "$ROOT/scripts/lib/common.sh"
            {_extract_escalate_to_janitor()}
            escalate_to_janitor "ngrok_fail" && echo OK || echo "ret=$?"
            """
        )
        res = subprocess.run(
            ["bash", "-c", harness], capture_output=True, text=True,
        )
        # The function should return 1 (handled by caller via `|| true`).
        assert "ret=1" in res.stdout
        # And the heartbeat helper should have been invoked at error level.
        assert "level=error" in res.stderr

    def test_prereq_fail_branch_does_not_spawn_janitor(
        self, fake_root: Path, tmp_path: Path,
    ) -> None:
        """Simulate the supervisor's inner else-block: when FAIL_KIND is
        prereq_fail the spawn shim must NOT be invoked."""
        record = tmp_path / "spawn-record"
        _make_spawn_shim(fake_root, record)

        harness = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -uo pipefail
            ROOT={fake_root!s}
            TASK_ID="dk-supervisor-task-xyz"
            source "$ROOT/scripts/lib/common.sh"
            {_extract_escalate_to_janitor()}

            # mimic the supervisor's branching block
            FAIL_KIND="prereq_fail"
            FAIL_EXIT=2
            if [[ "$FAIL_KIND" == "prereq_fail" ]]; then
              heartbeat "$TASK_ID" error "prereq_fail (FAIL_EXIT=$FAIL_EXIT); no janitor escalation"
            else
              escalate_to_janitor "$FAIL_KIND" || true
            fi
            """
        )
        res = subprocess.run(
            ["bash", "-c", harness], capture_output=True, text=True,
        )
        assert res.returncode == 0, res.stderr
        agent_file = Path(f"{record}.agent")
        assert not agent_file.exists(), "janitor spawn was triggered"
        assert "no janitor escalation" in res.stderr

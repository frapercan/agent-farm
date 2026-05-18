"""Pytest shim for tests/test_deploy_keeper_worker_healthcheck.sh.

Slice: FARM-DK-WORKER-HEALTHCHECK.

The actual assertions live in the bash test (it builds a synthetic
pids dir + sources the redeploy script's function block, which is
naturally a shell test). This shim just shells out so the pytest sweep
run by agent-farm CI picks the test up too.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASH_TEST = HERE / "test_deploy_keeper_worker_healthcheck.sh"


def test_bash_test_passes():
    assert BASH_TEST.is_file(), f"missing bash test: {BASH_TEST}"
    rc = subprocess.run(
        ["bash", str(BASH_TEST)],
        capture_output=True,
        text=True,
        check=False,
    )
    if rc.returncode != 0:
        raise AssertionError(
            f"bash test failed (rc={rc.returncode}):\n"
            f"--- stdout ---\n{rc.stdout}\n"
            f"--- stderr ---\n{rc.stderr}"
        )

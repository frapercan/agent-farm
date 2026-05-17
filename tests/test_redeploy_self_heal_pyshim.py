"""Pytest shim for tests/test_redeploy_self_heal.sh (FARM-1.6).

The actual assertions live in the bash test (it builds a synthetic git
remote + clone + worktree and the redeploy script under test is bash,
so shell is the natural test bed). This shim just shells out so the
pytest sweep run by agent-farm CI picks the test up too.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASH_TEST = HERE / "test_redeploy_self_heal.sh"


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

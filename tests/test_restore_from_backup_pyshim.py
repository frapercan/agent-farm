"""Pytest shim for tests/test_restore_from_backup.sh.

The actual assertions live in the bash test (flag parsing and dry-run
verification are easier to verify there without touching a live postgres).
This shim shells out so the pytest sweep run by agent-farm CI picks
them up too.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASH_TEST = HERE / "test_restore_from_backup.sh"


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

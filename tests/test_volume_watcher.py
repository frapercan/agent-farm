"""Tests for scripts/services/volume-watcher.sh (FARM-1.7).

These tests do not stat real docker volumes. They construct a fake
volumes root populated with regular directories, then run the watcher
with WATCHED_VOLUMES / VOLUMES_ROOT pointed at it. We assert that:

  * a first reading writes a `first-reading` row and emits no alert,
  * a subsequent reading at >= 50% of prior writes an `ok` row,
  * a reading at < 10% of prior writes a `shrink-alert` row,
  * a missing volume writes a `missing` row without crashing.

Heartbeats are stubbed by routing AGENT_FARM_ROOT to a temp dir where
the watcher cannot find scripts/lib/db.py (so it falls back to the
stderr branch). That keeps the test hermetic against the real
state/tasks.sqlite.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WATCHER = REPO_ROOT / "scripts" / "services" / "volume-watcher.sh"


def _make_volume(volumes_root: Path, name: str, size_bytes: int) -> Path:
    """Create a fake docker-volume dir with `_data/payload` of size_bytes."""
    data = volumes_root / name / "_data"
    data.mkdir(parents=True, exist_ok=True)
    payload = data / "payload"
    # `du -sb` adds directory-entry overhead; we only care that the
    # value is monotonic with `size_bytes`. Use a sparse write to keep
    # CI quick on tiny files and to scale up for the alert case.
    with payload.open("wb") as f:
        if size_bytes > 0:
            f.seek(size_bytes - 1)
            f.write(b"\0")
        else:
            # Zero-byte file still creates the inode.
            pass
    return data


def _run_watcher(tmp_path: Path, volumes_root: Path, volumes: str,
                 log_file: Path, shrink_ratio: str = "0.10") -> subprocess.CompletedProcess:
    env = os.environ.copy()
    # Point AGENT_FARM_ROOT at the tmp dir so the watcher's heartbeat
    # branch falls back to stderr (no real DB writes).
    env["AGENT_FARM_ROOT"] = str(tmp_path / "fake_farm_root")
    env["VOLUME_SIZES_LOG"] = str(log_file)
    env["VOLUMES_ROOT"] = str(volumes_root)
    env["WATCHED_VOLUMES"] = volumes
    env["SHRINK_RATIO"] = shrink_ratio
    env["AGENT_TASK_ID"] = "test-volume-watcher"
    return subprocess.run(
        ["bash", str(WATCHER)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _read_log_rows(log_file: Path) -> list[list[str]]:
    if not log_file.exists():
        return []
    rows = []
    for line in log_file.read_text().splitlines():
        rows.append(line.split("\t"))
    return rows


def test_watcher_script_exists_and_is_executable():
    assert WATCHER.is_file(), f"watcher script missing at {WATCHER}"
    # bash -n syntax check
    rc = subprocess.run(["bash", "-n", str(WATCHER)], capture_output=True)
    assert rc.returncode == 0, rc.stderr.decode()


def test_first_reading_writes_first_reading_row(tmp_path):
    volumes_root = tmp_path / "volumes"
    volumes_root.mkdir()
    _make_volume(volumes_root, "protea_postgres_data", 4096)
    log_file = tmp_path / "volume_sizes.log"

    proc = _run_watcher(tmp_path, volumes_root,
                        "protea_postgres_data", log_file)
    assert proc.returncode == 0, proc.stderr

    rows = _read_log_rows(log_file)
    assert len(rows) == 1
    # cols: ts, volume, bytes, prev_bytes, ratio, status
    assert rows[0][1] == "protea_postgres_data"
    assert rows[0][3] == ""
    assert rows[0][4] == "NA"
    assert rows[0][5] == "first-reading"


def test_steady_state_writes_ok_row(tmp_path):
    volumes_root = tmp_path / "volumes"
    volumes_root.mkdir()
    _make_volume(volumes_root, "protea_postgres_data", 8 * 1024 * 1024)
    log_file = tmp_path / "volume_sizes.log"

    # Prime + measure: two runs without any shrink.
    _run_watcher(tmp_path, volumes_root, "protea_postgres_data", log_file)
    _run_watcher(tmp_path, volumes_root, "protea_postgres_data", log_file)

    rows = _read_log_rows(log_file)
    assert len(rows) == 2
    assert rows[0][5] == "first-reading"
    assert rows[1][5] == "ok"
    # ratio should be close to 1.0 (identical content).
    assert abs(float(rows[1][4]) - 1.0) < 0.05


def test_shrink_triggers_alert_row(tmp_path):
    volumes_root = tmp_path / "volumes"
    volumes_root.mkdir()
    vol_data = _make_volume(volumes_root, "protea_postgres_data",
                            10 * 1024 * 1024)  # 10 MiB
    log_file = tmp_path / "volume_sizes.log"

    # Prime: large volume.
    _run_watcher(tmp_path, volumes_root, "protea_postgres_data", log_file)

    # Simulate wipe: drop payload to ~1 KiB.
    shutil.rmtree(vol_data)
    _make_volume(volumes_root, "protea_postgres_data", 1024)

    # Re-measure; threshold is default 10%, so 1 KiB / 10 MiB << 0.10.
    proc = _run_watcher(tmp_path, volumes_root,
                        "protea_postgres_data", log_file)
    assert proc.returncode == 0

    rows = _read_log_rows(log_file)
    assert rows[-1][5] == "shrink-alert"
    ratio = float(rows[-1][4])
    assert ratio < 0.10
    # Heartbeat fallback writes to stderr because AGENT_FARM_ROOT in the
    # test points at a dir with no scripts/lib/db.py. Either the warn
    # ("heartbeat call failed") or the level-prefix line is acceptable.
    combined = proc.stderr or ""
    assert ("P0:" in combined) or ("volume-watcher" in combined)


def test_missing_volume_writes_missing_row(tmp_path):
    volumes_root = tmp_path / "volumes"
    volumes_root.mkdir()
    log_file = tmp_path / "volume_sizes.log"

    # Do not create any volume dirs.
    proc = _run_watcher(tmp_path, volumes_root,
                        "protea_postgres_data protea_minio_data", log_file)
    assert proc.returncode == 0

    rows = _read_log_rows(log_file)
    statuses = {row[5] for row in rows}
    assert statuses == {"missing"}
    # Two volumes -> two rows.
    assert len(rows) == 2


def test_small_shrink_does_not_alert(tmp_path):
    """A 50% drop must not fire at the default 10% threshold."""
    volumes_root = tmp_path / "volumes"
    volumes_root.mkdir()
    vol_data = _make_volume(volumes_root, "protea_postgres_data",
                            8 * 1024 * 1024)
    log_file = tmp_path / "volume_sizes.log"

    _run_watcher(tmp_path, volumes_root, "protea_postgres_data", log_file)

    # Shrink to ~50%: above the 10% alert floor.
    shutil.rmtree(vol_data)
    _make_volume(volumes_root, "protea_postgres_data", 4 * 1024 * 1024)

    _run_watcher(tmp_path, volumes_root, "protea_postgres_data", log_file)

    rows = _read_log_rows(log_file)
    assert rows[-1][5] == "ok"


@pytest.mark.parametrize("ratio,shrunk_bytes,expect_alert", [
    # Threshold 50%; shrink to ~6% of prior -> alert.
    ("0.50", 512 * 1024, True),
    # Threshold 5%; shrink to ~50% of prior -> no alert (still above 5%).
    ("0.05", 4 * 1024 * 1024, False),
])
def test_threshold_override(tmp_path, ratio, shrunk_bytes, expect_alert):
    volumes_root = tmp_path / "volumes"
    volumes_root.mkdir()
    vol_data = _make_volume(volumes_root, "protea_postgres_data",
                            8 * 1024 * 1024)
    log_file = tmp_path / "volume_sizes.log"

    _run_watcher(tmp_path, volumes_root, "protea_postgres_data",
                 log_file, shrink_ratio=ratio)

    shutil.rmtree(vol_data)
    _make_volume(volumes_root, "protea_postgres_data", shrunk_bytes)

    _run_watcher(tmp_path, volumes_root, "protea_postgres_data",
                 log_file, shrink_ratio=ratio)

    rows = _read_log_rows(log_file)
    if expect_alert:
        assert rows[-1][5] == "shrink-alert"
    else:
        assert rows[-1][5] == "ok"

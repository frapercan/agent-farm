"""Tests for /worktrees endpoint."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def _seed_wt(root: Path, name: str, payload_bytes: int) -> None:
    wt = root / "worktrees" / name
    wt.mkdir(parents=True)
    (wt / "file.bin").write_bytes(b"x" * payload_bytes)


class TestWorktrees:
    def test_empty_dir_returns_empty_list(self, client: TestClient) -> None:
        r = client.get("/worktrees")
        assert r.status_code == 200
        assert r.json() == []

    def test_lists_subdirectories(
        self, settings_env: Path, seeded_db: Path,
    ) -> None:
        # Seed worktrees before constructing the client so the in-process
        # cache starts fresh.
        _seed_wt(settings_env, "executor-xyz", 1024)
        _seed_wt(settings_env, "janitor-abc", 2048)

        # Build the client fresh after seeding.
        from farm_api.app import create_app  # noqa: PLC0415
        from farm_api.routes import worktrees as wt_route  # noqa: PLC0415
        wt_route._clear_cache_for_tests()
        c = TestClient(create_app())
        r = c.get("/worktrees")
        assert r.status_code == 200
        body = r.json()
        names = {entry["name"] for entry in body}
        assert names == {"executor-xyz", "janitor-abc"}
        for entry in body:
            # size_bytes may be None if du is unavailable but on a
            # Linux test runner it should always succeed.
            if entry["size_bytes"] is not None:
                assert entry["size_bytes"] >= 1024

    def test_missing_worktrees_dir(
        self,
        settings_env: Path,
        seeded_db: Path,
        monkeypatch,
    ) -> None:
        # Point FARM_API_WORKTREES at a non-existent path.
        monkeypatch.setenv(
            "FARM_API_WORKTREES", str(settings_env / "nope"),
        )
        from farm_api.app import create_app  # noqa: PLC0415
        from farm_api.routes import worktrees as wt_route  # noqa: PLC0415
        wt_route._clear_cache_for_tests()
        c = TestClient(create_app())
        r = c.get("/worktrees")
        assert r.status_code == 200
        assert r.json() == []

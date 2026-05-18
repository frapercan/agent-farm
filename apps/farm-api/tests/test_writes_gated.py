"""Tests for the write endpoints (spawn, kill, cleanup).

Two layers:
1. Gating: routes only exist when FARM_API_WRITE=1 + FARM_API_AUTH_TOKEN
   are both set, and the X-Farm-Token header matches. These tests run
   against the default write_client fixture which has no override
   scripts directory, so they only exercise the auth surface.
2. Behaviour: a separate `script_stub_*` fixture replaces
   scripts/spawn-subagent.sh, scripts/kill.sh, scripts/cleanup.sh,
   scripts/plan-progress.sh with bash stubs that emit deterministic
   output. The tests then assert the sidecar parses K=V correctly,
   forwards arguments verbatim, and surfaces non-zero exit codes.
"""

from __future__ import annotations

import os
import shutil
import stat
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _write_script(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


@pytest.fixture()
def script_stubs(farm_root: Path) -> Path:
    """Drop bash stubs into <farm_root>/scripts/ for the write tests.

    Each stub echoes a deterministic payload and exits 0 unless the
    test explicitly overrides the stub afterwards.
    """
    scripts = farm_root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    _write_script(
        scripts / "spawn-subagent.sh",
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            # stub: emit canonical K=V lines so the parser sees a valid task.
            echo "task_id=executor-1779000000-stub"
            echo "worktree=/tmp/wt/executor-1779000000-stub"
            echo "composed_prompt=/tmp/rs/executor-1779000000-stub/composed_prompt.md"
            echo "model=opus"
            echo "repo=/home/test/PROTEA"
            echo "results_dir=/tmp/rs/executor-1779000000-stub"
            # stash the args so tests can inspect what we got
            printf '%s\\n' "$@" > /tmp/spawn-subagent-args.txt
            """
        ),
    )
    _write_script(
        scripts / "kill.sh",
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            echo "killed: $1"
            printf '%s\\n' "$@" > /tmp/kill-args.txt
            """
        ),
    )
    _write_script(
        scripts / "cleanup.sh",
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            if [[ "${1:-}" == "--apply" ]]; then
              echo "cleanup pass (apply=1)"
            else
              echo "cleanup pass (apply=0)"
            fi
            printf '%s\\n' "$@" > /tmp/cleanup-args.txt
            """
        ),
    )
    _write_script(
        scripts / "plan-progress.sh",
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            # stub: emit a deterministic next-pickable JSON.
            cat <<'JSON'
            {"id": "FARM-UI.6", "loop": "farm-platform", "phase": "F-UI",
             "priority": "P2", "deps": [], "status": "pending",
             "title": "CommandPalette farm verbs"}
            JSON
            """
        ),
    )
    return scripts


@pytest.fixture()
def write_client_stubbed(
    settings_env: Path,
    seeded_db: Path,
    script_stubs: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    monkeypatch.setenv("FARM_API_WRITE", "1")
    monkeypatch.setenv("FARM_API_AUTH_TOKEN", "test-token-abc")
    monkeypatch.setenv("FARM_API_SCRIPTS", str(script_stubs))
    from farm_api.app import create_app  # noqa: PLC0415

    return TestClient(create_app())


class TestWriteGating:
    def test_writes_not_registered_by_default(self, client: TestClient) -> None:
        # FARM_API_WRITE is unset in the default fixture; spawn should
        # return 404 (route not registered) rather than 403/501.
        r = client.post("/spawn", json={"agent": "executor", "task": "x"})
        assert r.status_code == 404

    def test_kill_not_registered_by_default(self, client: TestClient) -> None:
        r = client.post("/tasks/exec-001/kill")
        assert r.status_code == 404

    def test_cleanup_not_registered_by_default(self, client: TestClient) -> None:
        r = client.post("/cleanup", json={"apply": True})
        assert r.status_code == 404


class TestWriteEnabledNoToken:
    def test_misconfigured_keeps_routes_off(
        self, settings_env, seeded_db, monkeypatch,
    ) -> None:
        # FARM_API_WRITE=1 but no token: routes still NOT registered
        # (defence in depth), and /healthz advertises the misconfig.
        monkeypatch.setenv("FARM_API_WRITE", "1")
        monkeypatch.delenv("FARM_API_AUTH_TOKEN", raising=False)
        from farm_api.app import create_app  # noqa: PLC0415
        c = TestClient(create_app())
        r = c.post("/spawn", json={"agent": "executor", "task": "x"})
        assert r.status_code == 404
        h = c.get("/healthz").json()
        assert h["writes"]["enabled"] is False
        assert "FARM_API_AUTH_TOKEN" in (h["writes"]["reason"] or "")


class TestWriteAuth:
    def test_spawn_without_token_403(self, write_client: TestClient) -> None:
        r = write_client.post("/spawn", json={"agent": "executor", "task": "x"})
        assert r.status_code == 403

    def test_spawn_with_wrong_token_403(self, write_client: TestClient) -> None:
        r = write_client.post(
            "/spawn",
            json={"agent": "executor", "task": "x"},
            headers={"X-Farm-Token": "wrong"},
        )
        assert r.status_code == 403

    def test_kill_requires_token(self, write_client: TestClient) -> None:
        r = write_client.post("/tasks/exec-001/kill")
        assert r.status_code == 403

    def test_cleanup_requires_token(self, write_client: TestClient) -> None:
        r = write_client.post("/cleanup", json={"apply": False})
        assert r.status_code == 403


class TestSpawn:
    def test_spawn_explicit_returns_task_id(
        self, write_client_stubbed: TestClient,
    ) -> None:
        r = write_client_stubbed.post(
            "/spawn",
            json={"agent": "executor", "task": "FARM-1.9"},
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["task_id"] == "executor-1779000000-stub"
        assert body["agent"] == "executor"
        assert body["model"] == "opus"
        # The stub stashed the argv it received; verify the spec JSON
        # contains the slice id under "task".
        argv = Path("/tmp/spawn-subagent-args.txt").read_text().strip().splitlines()
        assert argv[0] == "executor"
        assert '"task": "FARM-1.9"' in argv[1]

    def test_spawn_next_pickable_resolves_slice(
        self, write_client_stubbed: TestClient,
    ) -> None:
        r = write_client_stubbed.post(
            "/spawn",
            json={"next_pickable": True},
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["task_id"] == "executor-1779000000-stub"
        assert body["slice_id"] == "FARM-UI.6"
        assert body["loop"] == "farm-platform"
        # agent resolved from loop default (farm-platform -> executor).
        assert body["agent"] == "executor"

    def test_spawn_requires_agent_when_not_next(
        self, write_client_stubbed: TestClient,
    ) -> None:
        r = write_client_stubbed.post(
            "/spawn",
            json={"task": "FARM-1.9"},
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 400
        assert "agent" in r.text.lower()

    def test_spawn_requires_task_when_not_next(
        self, write_client_stubbed: TestClient,
    ) -> None:
        r = write_client_stubbed.post(
            "/spawn",
            json={"agent": "executor"},
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 400
        assert "task" in r.text.lower()

    def test_spawn_propagates_script_failure(
        self,
        write_client_stubbed: TestClient,
        script_stubs: Path,
    ) -> None:
        # Replace the spawn stub with one that exits 1.
        _write_script(
            script_stubs / "spawn-subagent.sh",
            "#!/usr/bin/env bash\necho 'agent yaml missing' >&2\nexit 1\n",
        )
        r = write_client_stubbed.post(
            "/spawn",
            json={"agent": "ghost", "task": "FARM-1.9"},
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 502
        assert "agent yaml missing" in r.text

    def test_spawn_502_when_no_task_id_emitted(
        self,
        write_client_stubbed: TestClient,
        script_stubs: Path,
    ) -> None:
        _write_script(
            script_stubs / "spawn-subagent.sh",
            "#!/usr/bin/env bash\necho 'no task_id here'\nexit 0\n",
        )
        r = write_client_stubbed.post(
            "/spawn",
            json={"agent": "executor", "task": "x"},
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 502
        assert "no task_id" in r.text


class TestKill:
    def test_kill_invokes_script(
        self, write_client_stubbed: TestClient,
    ) -> None:
        r = write_client_stubbed.post(
            "/tasks/exec-001/kill",
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["task_id"] == "exec-001"
        assert body["killed"] is True
        assert "killed: exec-001" in body["stdout"]
        argv = Path("/tmp/kill-args.txt").read_text().strip().splitlines()
        assert argv == ["exec-001"]

    def test_kill_rejects_shell_metachars(
        self, write_client_stubbed: TestClient,
    ) -> None:
        # A task_id with characters outside [A-Za-z0-9_-] must never
        # reach the subprocess argv (defence against shell-injection
        # via a malicious or buggy client). Backticks are routable
        # in starlette so we get to the handler and then the allowlist
        # rejects with 400.
        r = write_client_stubbed.post(
            "/tasks/exec-001`whoami`/kill",
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 400, r.text

    def test_kill_404_when_task_missing(
        self,
        write_client_stubbed: TestClient,
        script_stubs: Path,
    ) -> None:
        _write_script(
            script_stubs / "kill.sh",
            "#!/usr/bin/env bash\necho 'task not found: ghost' >&2\nexit 1\n",
        )
        r = write_client_stubbed.post(
            "/tasks/ghost/kill",
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 404


class TestCleanup:
    def test_cleanup_dry_run_default(
        self, write_client_stubbed: TestClient,
    ) -> None:
        r = write_client_stubbed.post(
            "/cleanup",
            json={"apply": False},
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["apply"] is False
        assert "apply=0" in body["stdout"]
        argv = Path("/tmp/cleanup-args.txt").read_text().strip().splitlines()
        # Dry-run sends no --apply flag at all.
        assert argv == [""] or argv == []

    def test_cleanup_apply_passes_flag(
        self, write_client_stubbed: TestClient,
    ) -> None:
        r = write_client_stubbed.post(
            "/cleanup",
            json={"apply": True},
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["apply"] is True
        assert "apply=1" in body["stdout"]
        argv = Path("/tmp/cleanup-args.txt").read_text().strip().splitlines()
        assert argv == ["--apply"]


class TestOpenAPI:
    def test_openapi_json_served(self, client: TestClient) -> None:
        r = client.get("/openapi.json")
        assert r.status_code == 200
        spec = r.json()
        assert spec["info"]["title"] == "agent-farm API"
        paths = spec["paths"]
        for p in ("/tasks", "/tasks/{task_id}", "/tasks/{task_id}/heartbeats",
                  "/tasks/{task_id}/results", "/events", "/plan", "/cost",
                  "/worktrees", "/healthz"):
            assert p in paths, f"missing {p} in OpenAPI"
        # Write routes are NOT in the default spec (no FARM_API_WRITE).
        assert "/spawn" not in paths

    def test_openapi_includes_writes_when_enabled(
        self, write_client: TestClient,
    ) -> None:
        spec = write_client.get("/openapi.json").json()
        for p in ("/spawn", "/tasks/{task_id}/kill", "/cleanup"):
            assert p in spec["paths"]

    def test_docs_swagger_ui(self, client: TestClient) -> None:
        r = client.get("/docs")
        assert r.status_code == 200
        assert "swagger" in r.text.lower()

    def test_healthz_default(self, client: TestClient) -> None:
        r = client.get("/healthz")
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["db_present"] is True
        assert body["writes"]["enabled"] is False


# Keep shutil importable; module-level cleanup hook removes stub argv
# files between runs to avoid stale assertions on sibling tests.
def teardown_module(_module: object) -> None:  # pragma: no cover
    for stash in (
        "/tmp/spawn-subagent-args.txt",
        "/tmp/kill-args.txt",
        "/tmp/cleanup-args.txt",
    ):
        try:
            os.unlink(stash)
        except OSError:
            pass
    _ = shutil  # noqa: F841

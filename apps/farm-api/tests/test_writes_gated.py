"""Tests confirming write endpoints are gated behind env + auth."""

from __future__ import annotations

from fastapi.testclient import TestClient


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
        r = client.post("/cleanup", json={"dry_run": True})
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

    def test_spawn_with_correct_token_returns_501(
        self, write_client: TestClient,
    ) -> None:
        r = write_client.post(
            "/spawn",
            json={"agent": "executor", "task": "x"},
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 501
        body = r.json()
        # FastAPI wraps HTTPException(detail=dict) under "detail".
        detail = body["detail"]
        assert detail["error"] == "not_implemented"
        assert detail["runbook"] == "docs/runbook-farm-api.md"
        assert detail["payload_echo"]["agent"] == "executor"

    def test_kill_requires_token(self, write_client: TestClient) -> None:
        r = write_client.post("/tasks/exec-001/kill")
        assert r.status_code == 403

    def test_kill_authenticated_returns_501(
        self, write_client: TestClient,
    ) -> None:
        r = write_client.post(
            "/tasks/exec-001/kill",
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 501

    def test_cleanup_authenticated_returns_501(
        self, write_client: TestClient,
    ) -> None:
        r = write_client.post(
            "/cleanup",
            json={"dry_run": True, "older_than_hours": 24},
            headers={"X-Farm-Token": "test-token-abc"},
        )
        assert r.status_code == 501


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

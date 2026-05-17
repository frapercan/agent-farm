"""Tests for /tasks endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestListTasks:
    def test_returns_all_tasks_unfiltered(self, client: TestClient) -> None:
        r = client.get("/tasks")
        assert r.status_code == 200
        body = r.json()
        ids = {row["id"] for row in body}
        assert ids == {"exec-001", "exec-002", "janitor-003"}

    def test_filter_by_status(self, client: TestClient) -> None:
        r = client.get("/tasks", params={"status": "running"})
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 1
        assert body[0]["id"] == "exec-001"

    def test_filter_by_agent(self, client: TestClient) -> None:
        r = client.get("/tasks", params={"agent": "janitor"})
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 1
        assert body[0]["agent_name"] == "janitor"

    def test_filter_by_since_relative(self, client: TestClient) -> None:
        # Only tasks active within the last hour: exec-001 (running)
        # and exec-002 (ended 90m ago) — exec-002 is OUTSIDE, so only
        # exec-001 should come back.
        r = client.get("/tasks", params={"since": "1h"})
        assert r.status_code == 200
        body = r.json()
        ids = {row["id"] for row in body}
        assert ids == {"exec-001"}

    def test_filter_by_since_wider_window(self, client: TestClient) -> None:
        r = client.get("/tasks", params={"since": "1d"})
        body = r.json()
        ids = {row["id"] for row in body}
        # janitor-003 ended 2 days ago; should NOT show up.
        assert "janitor-003" not in ids
        assert {"exec-001", "exec-002"}.issubset(ids)

    def test_limit_param_caps_results(self, client: TestClient) -> None:
        r = client.get("/tasks", params={"limit": 1})
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_invalid_limit_rejected(self, client: TestClient) -> None:
        r = client.get("/tasks", params={"limit": 0})
        assert r.status_code == 422


class TestGetTask:
    def test_existing_task(self, client: TestClient) -> None:
        r = client.get("/tasks/exec-002")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == "exec-002"
        assert body["status"] == "succeeded"
        assert body["exit_code"] == 0

    def test_unknown_task_404(self, client: TestClient) -> None:
        r = client.get("/tasks/does-not-exist")
        assert r.status_code == 404


class TestHeartbeats:
    def test_lists_in_descending_order(self, client: TestClient) -> None:
        r = client.get("/tasks/exec-001/heartbeats")
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 3
        # ORDER BY ts DESC -> newest first
        timestamps = [row["ts"] for row in body]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_heartbeats_for_unknown_task_404(self, client: TestClient) -> None:
        r = client.get("/tasks/nope/heartbeats")
        assert r.status_code == 404

    def test_heartbeats_empty_list_for_task_with_none(
        self, client: TestClient
    ) -> None:
        r = client.get("/tasks/exec-002/heartbeats")
        assert r.status_code == 200
        assert r.json() == []


class TestResults:
    def test_existing_results_row(self, client: TestClient) -> None:
        r = client.get("/tasks/exec-002/results")
        assert r.status_code == 200
        body = r.json()
        assert body["task_id"] == "exec-002"
        assert body["summary"] == "ok"
        assert "opus-4.7" in (body["metrics_json"] or "")

    def test_no_results_row_returns_404(self, client: TestClient) -> None:
        r = client.get("/tasks/exec-001/results")
        assert r.status_code == 404

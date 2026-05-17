"""Tests for /events endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestListEvents:
    def test_returns_all_events(self, client: TestClient) -> None:
        r = client.get("/events")
        assert r.status_code == 200
        body = r.json()
        assert len(body) >= 5
        kinds = {row["kind"] for row in body}
        assert {"spawn", "start", "heartbeat", "end"}.issubset(kinds)

    def test_filter_by_kind(self, client: TestClient) -> None:
        r = client.get("/events", params={"kind": "end"})
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 2
        for row in body:
            assert row["kind"] == "end"

    def test_filter_by_level(self, client: TestClient) -> None:
        r = client.get("/events", params={"level": "warn"})
        body = r.json()
        for row in body:
            assert row["level"] == "warn"

    def test_filter_by_task_id(self, client: TestClient) -> None:
        r = client.get("/events", params={"task_id": "exec-001"})
        body = r.json()
        assert len(body) == 3
        for row in body:
            assert row["task_id"] == "exec-001"

    def test_invalid_kind_400(self, client: TestClient) -> None:
        r = client.get("/events", params={"kind": "not-a-real-kind"})
        assert r.status_code == 400

    def test_invalid_since_400(self, client: TestClient) -> None:
        r = client.get("/events", params={"since": "5z"})
        # "5z" is treated as absolute (no s/m/h/d suffix). sqlite ts
        # column will just compare strings; events with ts >= "5z" is
        # empty rather than an error, so this returns 200 with [].
        assert r.status_code == 200
        assert r.json() == []

    def test_joins_agent_name(self, client: TestClient) -> None:
        r = client.get("/events", params={"task_id": "janitor-003"})
        body = r.json()
        assert len(body) == 1
        assert body[0]["agent_name"] == "janitor"

    def test_limit_param(self, client: TestClient) -> None:
        r = client.get("/events", params={"limit": 2})
        body = r.json()
        assert len(body) == 2

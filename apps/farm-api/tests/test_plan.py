"""Tests for /plan endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestPlan:
    def test_lists_fixture_slices(self, client: TestClient) -> None:
        r = client.get("/plan")
        assert r.status_code == 200
        body = r.json()
        ids = {s["id"] for s in body}
        assert {"FARM-UI.1", "FARM-UI.2"}.issubset(ids)

    def test_filter_by_loop(self, client: TestClient) -> None:
        r = client.get("/plan", params={"loop": "farm-platform"})
        body = r.json()
        assert len(body) == 2
        for s in body:
            assert s["loop"] == "farm-platform"

    def test_filter_by_loop_unknown(self, client: TestClient) -> None:
        r = client.get("/plan", params={"loop": "no-such-loop"})
        assert r.status_code == 200
        assert r.json() == []

    def test_filter_by_status(self, client: TestClient) -> None:
        r = client.get("/plan", params={"status": "done"})
        body = r.json()
        assert all(s["status"] == "done" for s in body)
        assert any(s["id"] == "FARM-UI.1" for s in body)

    def test_slice_contains_deps_and_priority(self, client: TestClient) -> None:
        r = client.get("/plan")
        body = r.json()
        ui2 = next(s for s in body if s["id"] == "FARM-UI.2")
        assert ui2["deps"] == ["FARM-UI.1"]
        assert ui2["priority"] == "P1"
        assert ui2["estimated_hours"] == 8

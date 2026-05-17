"""Tests for /cost endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestCost:
    def test_returns_bucket_for_succeeded_task(self, client: TestClient) -> None:
        r = client.get("/cost", params={"days": 7})
        assert r.status_code == 200
        body = r.json()
        # Only exec-002 has a metrics_json row in the fixture.
        assert len(body) == 1
        bucket = body[0]
        assert bucket["agent"] == "executor"
        assert bucket["model"] == "opus-4.7"
        assert bucket["tasks"] == 1
        assert bucket["input_tokens"] == 1000
        assert bucket["output_tokens"] == 500
        assert abs(bucket["usd"] - 0.0125) < 1e-9

    def test_agent_filter(self, client: TestClient) -> None:
        r = client.get("/cost", params={"agent": "janitor"})
        # janitor has no metrics row in the fixture.
        assert r.json() == []

    def test_model_filter(self, client: TestClient) -> None:
        r = client.get("/cost", params={"model": "haiku-4.5"})
        assert r.json() == []

    def test_days_zero_window(self, client: TestClient) -> None:
        r = client.get("/cost", params={"days": 0})
        # exec-002 ended 90m ago which is within today's window,
        # depending on the boundary. We just assert it returns 200
        # and a list (could be empty or 1).
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_negative_days_rejected(self, client: TestClient) -> None:
        r = client.get("/cost", params={"days": -1})
        assert r.status_code == 422

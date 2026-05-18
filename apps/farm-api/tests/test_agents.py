"""Tests for /agents endpoint.

Reads the per-agent advisory cost budgets from agents/*.yaml. Fixtures
seed two well-formed agent specs (executor, janitor) and one broken
file that must be silently skipped.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestAgentBudgets:
    def test_returns_seeded_budgets(self, client: TestClient) -> None:
        r = client.get("/agents/budgets")
        assert r.status_code == 200
        body = r.json()
        # Two well-formed agents, the malformed yaml is silently skipped.
        names = {row["name"] for row in body}
        assert names == {"executor", "janitor"}

    def test_executor_budget_shape(self, client: TestClient) -> None:
        r = client.get("/agents/budgets")
        body = r.json()
        executor = next(row for row in body if row["name"] == "executor")
        assert executor["kind"] == "subagent"
        assert executor["model"] == "opus-4.7"
        assert executor["expected_tokens"] == 120000
        assert abs(executor["max_usd_per_day"] - 12.0) < 1e-9

    def test_response_sorted_by_name(self, client: TestClient) -> None:
        # Stable order is part of the dashboard contract so the bar
        # chart never reshuffles between polls.
        r = client.get("/agents/budgets")
        names = [row["name"] for row in r.json()]
        assert names == sorted(names)

    def test_missing_agents_dir_returns_empty(
        self,
        client: TestClient,
        farm_root,
    ) -> None:
        import shutil

        shutil.rmtree(farm_root / "agents")
        r = client.get("/agents/budgets")
        assert r.status_code == 200
        assert r.json() == []

"""Pydantic response models for farm-api.

These mirror the sqlite columns 1:1 and exist mostly so the OpenAPI
schema served at /openapi.json is informative for the future Next.js
client. Optional fields use None defaults so unset columns serialise to
JSON null.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Task(BaseModel):
    id: str
    agent_name: str
    kind: str
    persistent: int
    status: str
    spawn_args: str | None = None
    worktree: str | None = None
    tmux_window: str | None = None
    pid: int | None = None
    model: str | None = None
    created_at: str
    started_at: str | None = None
    ended_at: str | None = None
    exit_code: int | None = None
    worktree_owner_repo: str | None = None


class Heartbeat(BaseModel):
    id: int
    task_id: str
    ts: str
    level: str
    message: str


class Result(BaseModel):
    task_id: str
    summary: str | None = None
    sha_before: str | None = None
    sha_after: str | None = None
    artifacts_dir: str | None = None
    metrics_json: str | None = None


class Event(BaseModel):
    id: int
    task_id: str
    ts: str
    kind: str
    level: str | None = None
    message: str | None = None
    payload_json: str | None = None
    agent_name: str | None = None


class CostBucket(BaseModel):
    date: str
    agent: str
    model: str
    tasks: int
    input_tokens: int
    output_tokens: int
    cache_tokens: int
    usd: float


class AgentBudget(BaseModel):
    """Per-agent cost budget read from agents/<name>.yaml.

    `max_usd_per_day` is the advisory daily cap the operator sets in the
    agent's spec (cost_budget.max_usd_per_day). The dashboard overlays
    it against actual spend reported by /cost so over-budget agents are
    flagged at a glance.
    """

    name: str
    kind: str | None = None
    model: str | None = None
    expected_tokens: int | None = None
    max_usd_per_day: float | None = None


class WorktreeInfo(BaseModel):
    name: str
    path: str
    size_bytes: int | None = None
    exists: bool = True


class PlanSlice(BaseModel):
    id: str
    title: str
    loop: str
    phase: str
    status: str
    deps: list[str] = Field(default_factory=list)
    priority: str | None = None
    estimated_hours: float | None = None
    tags: list[str] = Field(default_factory=list)
    requires_human: bool = False
    acceptance: str | None = None


class WriteScaffold(BaseModel):
    """Common 501 body for the scaffolded write endpoints."""

    error: str = "not_implemented"
    runbook: str = "docs/runbook-farm-api.md"
    detail: str
    payload_echo: dict[str, Any] | None = None

-- state/migrations/001_events.sql — FARM-2.1 events table.
--
-- Append-only audit trail of lifecycle transitions across the farm.
-- Powers status.sh --events and the dashboard timeline (FARM-UI.2).
--
-- Apply against the live WAL-mode tasks.sqlite:
--   sqlite3 ~/Thesis2/agent-farm/state/tasks.sqlite < 001_events.sql
--
-- Idempotent (IF NOT EXISTS on every DDL), safe to re-apply.
--
-- The events row references tasks(id) (the PK on tasks is `id`, not
-- `task_id`); we keep the heartbeats-style local column name `task_id`
-- for symmetry with that table.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS events (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id      TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  ts           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  kind         TEXT NOT NULL CHECK (kind IN
                ('spawn','start','end','kill','heartbeat','cleanup')),
  level        TEXT,
  message      TEXT,
  payload_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_task_ts ON events(task_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_kind_ts ON events(kind, ts DESC);

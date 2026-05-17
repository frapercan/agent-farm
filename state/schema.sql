-- loop2/state/schema.sql — single source of truth for runtime state.
-- Created by scripts/init.sh into state/tasks.sqlite.
-- WAL mode so readers (status.sh) don't block writers (heartbeats).

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tasks (
  id           TEXT PRIMARY KEY,            -- ulid-ish: <agent>-<unix>-<rand4>
  agent_name   TEXT NOT NULL,               -- references agents/<name>.yaml
  kind         TEXT NOT NULL CHECK(kind IN ('subagent','headless')),
  persistent   INTEGER NOT NULL DEFAULT 0,  -- 0/1; only meaningful for headless
  status       TEXT NOT NULL CHECK(status IN
                ('pending','running','succeeded','failed','killed','crashed')),
  spawn_args   TEXT,                        -- JSON blob, free-form per agent
  worktree     TEXT,                        -- abs path or NULL
  tmux_window  TEXT,                        -- "<session>:<window>" or NULL
  pid          INTEGER,                     -- supervisor pid for headless
  model        TEXT,                        -- haiku-4.5 / sonnet-4.6 / opus-4.7
  created_at   TEXT NOT NULL,               -- ISO-8601
  started_at   TEXT,
  ended_at     TEXT,
  exit_code    INTEGER
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent  ON tasks(agent_name, created_at);

CREATE TABLE IF NOT EXISTS heartbeats (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id   TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  ts        TEXT NOT NULL,
  level     TEXT NOT NULL CHECK(level IN ('info','warn','error')),
  message   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_heartbeats_task ON heartbeats(task_id, ts DESC);

CREATE TABLE IF NOT EXISTS results (
  task_id        TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
  summary        TEXT,                      -- one-paragraph human summary
  sha_before     TEXT,
  sha_after      TEXT,
  artifacts_dir  TEXT,                      -- results/<task_id>/
  metrics_json   TEXT                       -- free-form JSON (tokens, time, etc.)
);

-- FARM-2.1: append-only lifecycle audit trail.
-- Mirrors state/migrations/001_events.sql so a fresh init.sh DB also has it.
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

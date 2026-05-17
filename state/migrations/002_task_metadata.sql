-- state/migrations/002_task_metadata.sql — FARM-2.3 + FARM-2.4 task metadata.
--
-- Two slice goals fused into one migration because they share the same
-- spawn/finalize integration surface:
--
--   FARM-2.3: tasks.worktree_owner_repo TEXT — records the owning repo for a
--             worktree at spawn time so finalize/cleanup/kill skip the
--             O(repos x worktrees) scan during teardown.
--
--   FARM-2.4: results.sha_before / sha_after — already declared in
--             state/schema.sql but never written. No DDL change here; this
--             file documents the contract and stays idempotent so a fresh
--             init.sh + a re-run of every migration ends in the same state.
--
-- Apply via the apply_migrations.py helper which guards each statement with
-- a PRAGMA table_info(tasks) check (sqlite has no ADD COLUMN IF NOT EXISTS).
--   python3 scripts/lib/apply_migrations.py
--
-- Direct executescript() will fail on the second apply because the ALTER
-- raises "duplicate column name: worktree_owner_repo". Use the helper.

PRAGMA foreign_keys = ON;

-- FARM-2.3
ALTER TABLE tasks ADD COLUMN worktree_owner_repo TEXT;

-- FARM-2.4: sha_before / sha_after already present on results in schema.sql.
-- This migration intentionally has no DDL for them; the work is in db.py
-- (set-sha command) + spawn-subagent.sh + finalize-subagent.sh.

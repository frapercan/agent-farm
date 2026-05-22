#!/usr/bin/env bash
# finalize-subagent.sh — close out a subagent task atomically.
#
# Companion to spawn-subagent.sh. Call from the conductor right after the
# Agent tool returns (or fails). Does all the cleanup the conductor was
# previously doing inline:
#
#   1. Mark task ended in sqlite (status + exit code)
#   2. Optionally store a results row with the agent's summary
#   3. Remove the ephemeral worktree from its owning repo
#      (skipped if the agent's worktree.cleanup == none, or the worktree
#       path is in the agents/*.yaml protected set)
#
# Usage:
#   bash finalize-subagent.sh <task_id> <succeeded|failed> [exit_code] [summary]
#       [--metrics-file PATH]   parse Claude CLI cost output captured to PATH
#       [--metrics-json STR]    raw metrics JSON (pre-parsed by caller)
#
# Output: K=V on stdout (final task state for the conductor to surface).
#
# The conductor MUST call this — it replaces the manual `db.py set-ended`
# pattern. Forgetting to call it leaves worktrees orphan, which is the
# bug that produced the _siblings/* leak in the previous session.
#
# FARM-2.2: when --metrics-file or --metrics-json is supplied (or when
# results/<task_id>/stream.jsonl exists as a default capture path), parse
# the Claude CLI cost line and call db.py set-metrics. The conductor may
# pre-stage results/<task_id>/stream.jsonl by piping Agent tool output
# through tee; the default capture path is honoured without an explicit
# flag.

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
# shellcheck source=lib/common.sh
source "$ROOT/scripts/lib/common.sh"
# shellcheck source=lib/worktree.sh
source "$ROOT/scripts/lib/worktree.sh"

TASK_ID=""
STATUS="succeeded"
EXIT="0"
SUMMARY=""
METRICS_FILE=""
METRICS_JSON=""

# Positional args (task_id, status, exit, summary) interleave with flags.
positional_idx=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --metrics-file) METRICS_FILE="${2:?--metrics-file needs PATH}"; shift 2 ;;
    --metrics-json) METRICS_JSON="${2:?--metrics-json needs JSON}"; shift 2 ;;
    --) shift; break ;;
    -*) die "unknown flag: $1" ;;
    *)
      case "$positional_idx" in
        0) TASK_ID="$1" ;;
        1) STATUS="$1" ;;
        2) EXIT="$1" ;;
        3) SUMMARY="$1" ;;
        *) die "too many positional args (extra: $1)" ;;
      esac
      positional_idx=$((positional_idx + 1))
      shift
      ;;
  esac
done

[[ -z "$TASK_ID" ]] && die "usage: finalize-subagent.sh <task_id> <succeeded|failed> [exit] [summary] [--metrics-file PATH] [--metrics-json STR]"

case "$STATUS" in
  succeeded|failed|crashed) ;;
  *) die "status must be succeeded|failed|crashed (got '$STATUS')" ;;
esac

# Read task metadata we need. FARM-2.3 adds worktree_owner_repo to the
# read so the teardown path can skip the O(repos x worktrees) scan when
# the column is populated. Null for historical tasks → fallback to scan.
ROW=$(db_query "SELECT agent_name, worktree, COALESCE(worktree_owner_repo,'') FROM tasks WHERE id='$TASK_ID' LIMIT 1;" || true)
[[ -z "$ROW" ]] && die "task not found in sqlite: $TASK_ID"

AGENT_NAME=$(printf '%s' "$ROW" | awk -F'\t' '{print $1}')
WORKTREE=$(printf '%s' "$ROW" | awk -F'\t' '{print $2}')
OWNER_REPO=$(printf '%s' "$ROW" | awk -F'\t' '{print $3}')

# FARM-2.4: capture sha_after right before teardown so the executor trail
# is introspectable end-to-end. Best-effort — failure must not block the
# rest of finalize, since the audit value is observability, not control.
if [[ -n "$WORKTREE" && -d "$WORKTREE" ]]; then
  if SHA_AFTER=$(git -C "$WORKTREE" rev-parse HEAD 2>/dev/null); then
    if ! python3 "$ROOT/scripts/lib/db.py" set-sha \
          "$TASK_ID" after "$SHA_AFTER" 2>/tmp/set-sha-after.err; then
      heartbeat "$TASK_ID" warn "set-sha after failed: $(cat /tmp/set-sha-after.err 2>/dev/null)"
    fi
  fi
fi

# Mark task ended in sqlite
task_set_ended "$TASK_ID" "$STATUS" "$EXIT"

# FARM-1.3: scan the task's heartbeats + summary for PR URLs and verify
# each PR's base branch matches the canonical table in
# scripts/lib/pr_base.py. Mismatch → emit warn heartbeat and try to
# rebase via `gh pr edit --base`. Best-effort; failure here never
# blocks finalize (the worktree must still be cleaned up).
PR_BASE_SH="$ROOT/scripts/lib/pr-base.sh"
if [[ -x "$PR_BASE_SH" ]]; then
  # Pull all heartbeat messages + summary in one go (NUL-separated to
  # survive embedded newlines in messages).
  SCAN_TEXT=$(db_query "SELECT message FROM heartbeats WHERE task_id='$TASK_ID' UNION ALL SELECT '$(printf '%s' "$SUMMARY" | sed "s/'/''/g")';" 2>/dev/null || true)
  if [[ -n "$SCAN_TEXT" ]]; then
    # JSON list of {owner,repo,number,expected_base}
    PR_JSON=$(printf '%s' "$SCAN_TEXT" | python3 "$ROOT/scripts/lib/pr_base.py" scan --stdin 2>/dev/null || echo '[]')
    if [[ "$PR_JSON" != "[]" && -n "$PR_JSON" ]]; then
      # Iterate via python so jq isn't a hard dep
      while IFS=$'\t' read -r OWNER REPO_SHORT NUMBER EXPECTED; do
        [[ -z "$NUMBER" ]] && continue
        if [[ "$EXPECTED" == "None" || -z "$EXPECTED" ]]; then
          heartbeat "$TASK_ID" warn "pr-base: unknown repo $OWNER/$REPO_SHORT (PR #$NUMBER); update pr_base.REPO_BASE"
          continue
        fi
        if bash "$PR_BASE_SH" check "$OWNER" "$REPO_SHORT" "$NUMBER" >/dev/null 2>&1; then
          heartbeat "$TASK_ID" info "pr-base: $OWNER/$REPO_SHORT#$NUMBER base=$EXPECTED OK"
        else
          heartbeat "$TASK_ID" warn "pr-base: $OWNER/$REPO_SHORT#$NUMBER base != $EXPECTED; auto-rebasing"
          if bash "$PR_BASE_SH" fix "$OWNER" "$REPO_SHORT" "$NUMBER" >/dev/null 2>&1; then
            heartbeat "$TASK_ID" info "pr-base: $OWNER/$REPO_SHORT#$NUMBER rebased to $EXPECTED"
          else
            heartbeat "$TASK_ID" error "pr-base: failed to rebase $OWNER/$REPO_SHORT#$NUMBER (check gh auth + permissions)"
          fi
        fi
      done < <(printf '%s' "$PR_JSON" | python3 -c "
import json, sys
for x in json.load(sys.stdin):
    print('\t'.join([x['owner'], x['repo'], str(x['number']), str(x['expected_base'])]))
")
    fi
  fi
fi

# Optional summary row. We UPSERT instead of INSERT OR REPLACE so the
# sibling columns (sha_before, sha_after, metrics_json) that spawn /
# FARM-2.4 wrote earlier do not get blanked out.
if [[ -n "$SUMMARY" ]]; then
  ESCAPED=$(printf '%s' "$SUMMARY" | sed "s/'/''/g")
  db_exec "INSERT INTO results(task_id, summary) VALUES('$TASK_ID', '$ESCAPED') ON CONFLICT(task_id) DO UPDATE SET summary=excluded.summary;"
fi

# Worktree cleanup, gated by yaml policy
REMOVED=0
SKIP_REASON=""

if [[ -z "$WORKTREE" ]]; then
  SKIP_REASON="no worktree recorded"
elif [[ ! -d "$WORKTREE" ]]; then
  SKIP_REASON="worktree dir already gone"
else
  YAML="$ROOT/agents/${AGENT_NAME}.yaml"
  if [[ -f "$YAML" ]]; then
    CLEANUP=$(yaml_get "$YAML" "worktree.cleanup")
    PROTECTED_PATH=$(yaml_get "$YAML" "worktree.path")
    PROTECTED_PATH="${PROTECTED_PATH/#\~/$HOME}"

    if [[ "$CLEANUP" == "none" ]]; then
      SKIP_REASON="agent yaml cleanup=none (stable worktree, not touched)"
    elif [[ -n "$PROTECTED_PATH" && "$WORKTREE" == "$PROTECTED_PATH" ]]; then
      SKIP_REASON="worktree matches protected path in yaml"
    else
      # FARM-2.3: pass owner_repo as hint for O(1) fast path; wt_remove
      # falls back to the full repo scan when the hint is absent or stale.
      # Determine in advance whether the fast path will succeed so we can
      # emit a precise heartbeat matching the actual code path taken.
      FAST_PATH=0
      if [[ -n "$OWNER_REPO" && -d "$OWNER_REPO/.git" ]]; then
        if git -C "$OWNER_REPO" worktree list --porcelain 2>/dev/null \
            | grep -q "^worktree $WORKTREE$"; then
          FAST_PATH=1
        fi
      fi
      wt_remove "$WORKTREE" "$OWNER_REPO"
      REMOVED=1
      if [[ "$FAST_PATH" -eq 1 ]]; then
        heartbeat "$TASK_ID" info "worktree removed from $OWNER_REPO (via owner_repo column)"
      else
        heartbeat "$TASK_ID" info "worktree removed (scan fallback)"
      fi
    fi
  else
    SKIP_REASON="agent yaml missing: $YAML"
  fi
fi

# FARM-2.2: cost metrics writer. Source priority:
#   1. --metrics-json (already a JSON object, pass straight through)
#   2. --metrics-file (parse via parse_claude_cost.py)
#   3. Default capture: results/<task_id>/stream.jsonl (parse if present)
# Result on success: results.metrics_json populated, end-event payload
# annotated, and results/<task_id>/metrics.json mirrored for offline tools.
METRICS_PARSED=""
if [[ -n "$METRICS_JSON" ]]; then
  METRICS_PARSED="$METRICS_JSON"
elif [[ -n "$METRICS_FILE" && -f "$METRICS_FILE" ]]; then
  METRICS_PARSED=$(python3 "$ROOT/scripts/lib/parse_claude_cost.py" "$METRICS_FILE" 2>/dev/null || echo "")
else
  DEFAULT_STREAM="$ROOT/results/$TASK_ID/stream.jsonl"
  if [[ -f "$DEFAULT_STREAM" ]]; then
    METRICS_PARSED=$(python3 "$ROOT/scripts/lib/parse_claude_cost.py" "$DEFAULT_STREAM" 2>/dev/null || echo "")
  fi
fi

if [[ -n "$METRICS_PARSED" && "$METRICS_PARSED" != "{}" ]]; then
  # Mirror to disk first (useful even if the DB write later fails).
  RESULTS_DIR="$ROOT/results/$TASK_ID"
  mkdir -p "$RESULTS_DIR" 2>/dev/null || true
  printf '%s' "$METRICS_PARSED" > "$RESULTS_DIR/metrics.json" 2>/dev/null || true
  if python3 "$ROOT/scripts/lib/db.py" set-metrics "$TASK_ID" "$METRICS_PARSED" 2>/tmp/finalize-metrics.err; then
    heartbeat "$TASK_ID" info "metrics recorded: $METRICS_PARSED"
  else
    heartbeat "$TASK_ID" warn "set-metrics failed: $(cat /tmp/finalize-metrics.err 2>/dev/null)"
  fi
fi

# FARM-FEAT.8: advisory cost_budget check. Sums the agent's metrics_json
# over the last 24h and emits an error-level heartbeat (which records a
# kind=heartbeat event row carrying level=error) when the rolling sum
# exceeds the cap, or a warn-level heartbeat when it crosses the warn
# ratio. No hard gate: the task has already finished by the time we get
# here; this signal lets the operator decide whether to throttle next
# spawns. Best-effort: never blocks finalize.
if [[ -f "$ROOT/scripts/lib/budget_check.py" ]]; then
  python3 "$ROOT/scripts/lib/budget_check.py" emit-finalize "$TASK_ID" \
    >/dev/null 2>>/tmp/budget-check.err || true
fi

cat <<EOF
task_id=$TASK_ID
status=$STATUS
exit=$EXIT
worktree_removed=$REMOVED
${SKIP_REASON:+skip_reason=$SKIP_REASON}
${METRICS_PARSED:+metrics=$METRICS_PARSED}
EOF

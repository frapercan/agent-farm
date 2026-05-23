#!/usr/bin/env bash
# deploy-keeper-tick.sh — one tick of the deploy-keeper service.
#
# Reuses battle-tested deploy scripts (idempotent). Records heartbeats to sqlite.
# Returns:
#   0   tick OK (noop or redeployed cleanly + ngrok up)
#   1   failure — supervisor will escalate via spawn-subagent.sh janitor
#       (except FAIL_KIND=prereq_fail which is reported but not escalated)

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
TASK_ID="${TASK_ID:?TASK_ID env required}"
# shellcheck source=../lib/common.sh
source "$ROOT/scripts/lib/common.sh"
# shellcheck source=../lib/stack_owner.sh
source "$ROOT/scripts/lib/stack_owner.sh"

LIB="$ROOT/scripts/services/lib"

PROTEA_REPO="${PROTEA_REPO:-$HOME/Thesis2/repositories/PROTEA}"
PROTEA_COMPOSE="${PROTEA_COMPOSE:-$PROTEA_REPO/docker-compose.yml}"

# 0-pre) stack-owner gate (FARM-FEAT.12).
# When a long export pipeline (FARM-EXP.13 + friends) holds the stack
# lock, deploy-keeper MUST step aside: a blind restart would kill the
# in-flight export and silently corrupt the run (memory:
# feedback_deploykeeper_vs_export_stack_conflict 2026-05-20). The lock
# is advisory; we honor it by exiting 0 ("tick succeeded as noop") so
# the supervisor sleeps the full poll_interval and tries again.
# owner=deploy means a previous deploy-keeper tick claimed the lock for
# itself, which is fine; owner=free means no one is holding it. Any
# OTHER value (today only "export") defers.
STACK_OWNER_CURRENT=$(stack_owner_current | tr -d '[:space:]')
case "$STACK_OWNER_CURRENT" in
  free|deploy)
    : ;;
  export)
    OWNER_TASK=$(STACK_OWNER_FILE="${STACK_OWNER_FILE:-$ROOT/state/stack-owner.json}" \
                 bash -c "source $ROOT/scripts/lib/stack_owner.sh; _stack_owner_read_field task_id")
    heartbeat "$TASK_ID" info "deferred-stack-owned-by-task task_id=${OWNER_TASK:-unknown} owner=export (skipping tick)"
    exit 0
    ;;
  *)
    heartbeat "$TASK_ID" warn "stack-owner lock in unexpected state '$STACK_OWNER_CURRENT'; proceeding (treating as free)"
    ;;
esac

# 0) prereq sanity (docker hard fail; postgres/rabbit try one bring-up)
if ! docker info >/dev/null 2>&1; then
  heartbeat "$TASK_ID" error "prereq fail: docker daemon not responding"
  echo "FAIL_KIND=prereq_fail" > /tmp/deploy-keeper-last-fail.env
  echo "FAIL_EXIT=1" >> /tmp/deploy-keeper-last-fail.env
  exit 1
fi

# port_listening <port> returns 0 iff something listens on TCP <port>.
port_listening() {
  ss -ltn 2>/dev/null | grep -q ":$1 "
}

# wait_for_port <port> <timeout_s> polls until port_listening or timeout.
wait_for_port() {
  local port="$1" timeout="$2" elapsed=0
  while (( elapsed < timeout )); do
    if port_listening "$port"; then
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  return 1
}

# bring_up_pg_rabbit: try `docker compose up -d postgres rabbitmq` once,
# then wait up to 15s per port. Returns 0 iff BOTH ports are listening.
bring_up_pg_rabbit() {
  if [[ ! -f "$PROTEA_COMPOSE" ]]; then
    heartbeat "$TASK_ID" error "auto-recovery: compose file not found at $PROTEA_COMPOSE"
    return 1
  fi
  heartbeat "$TASK_ID" warn "auto-recovery: docker compose up -d postgres rabbitmq"
  if ! docker compose -f "$PROTEA_COMPOSE" up -d postgres rabbitmq >/dev/null 2>&1; then
    heartbeat "$TASK_ID" error "auto-recovery: docker compose up failed"
    return 1
  fi
  wait_for_port 5432 15 || return 1
  wait_for_port 5672 15 || return 1
  return 0
}

if ! port_listening 5432 || ! port_listening 5672; then
  if bring_up_pg_rabbit; then
    heartbeat "$TASK_ID" info "auto-recovery: postgres + rabbit now listening"
  else
    if ! port_listening 5432; then
      heartbeat "$TASK_ID" error "prereq fail: postgres not listening on :5432 (recovery attempted)"
      echo "FAIL_KIND=prereq_fail" > /tmp/deploy-keeper-last-fail.env
      echo "FAIL_EXIT=2" >> /tmp/deploy-keeper-last-fail.env
      exit 1
    fi
    if ! port_listening 5672; then
      heartbeat "$TASK_ID" error "prereq fail: rabbitmq not listening on :5672 (recovery attempted)"
      echo "FAIL_KIND=prereq_fail" > /tmp/deploy-keeper-last-fail.env
      echo "FAIL_EXIT=3" >> /tmp/deploy-keeper-last-fail.env
      exit 1
    fi
  fi
fi

# 0b) postgres schema preflight (FARM-1.7).
# If the public schema has dropped to a single table (typically just
# alembic_version) the underlying docker volume has likely been wiped
# again (cf. project_db_volume_landmine memory + 2026-05-11 incident).
# Emit a P0/critical heartbeat so the supervisor + human paging picks
# it up. We do NOT exit non-zero here: redeploy/ngrok recovery can
# still run usefully on a wiped DB, and the heartbeat is the signal.
PG_PUBLIC_TABLES=$(docker exec -i protea-postgres-1 \
  psql -U protea -d protea -tAc \
  "SELECT count(*) FROM pg_tables WHERE schemaname='public'" \
  2>/dev/null | tr -d '[:space:]' || true)
if [[ "$PG_PUBLIC_TABLES" == "1" ]]; then
  heartbeat "$TASK_ID" critical \
    "P0: pg_tables(public)=1 (only alembic_version). Volume wipe suspected. See agent-farm/state/logs/volume_audit.log and docs/runbook-pg-volume-recovery.md"
elif [[ "$PG_PUBLIC_TABLES" == "0" ]]; then
  heartbeat "$TASK_ID" critical \
    "P0: pg_tables(public)=0. Schema empty. See docs/runbook-pg-volume-recovery.md"
fi

# 0c) Persist the count to a TSV history log + 50%-drop guard (FARM-1.7).
# The 0/1 guards above catch a full wipe. A partial drop (e.g. someone
# DROP'd 20 of 40 tables) would slip past them. Compare against the
# most recent prior reading; if the new count is <50% of the prior
# count and there has been no schema migration commit on develop since
# that reading, emit a P0 heartbeat.
if [[ -n "$PG_PUBLIC_TABLES" && "$PG_PUBLIC_TABLES" =~ ^[0-9]+$ ]]; then
  PG_HIST_LOG="$ROOT/state/logs/pg_table_history.log"
  mkdir -p "$(dirname "$PG_HIST_LOG")"
  NOW_ISO_TICK=$(date -Iseconds)
  # Read the most recent prior row before appending this tick.
  PREV_LINE=""
  if [[ -f "$PG_HIST_LOG" ]]; then
    PREV_LINE=$(tac "$PG_HIST_LOG" 2>/dev/null \
      | awk -F'\t' '$2 ~ /^[0-9]+$/ {print; exit}')
  fi
  printf '%s\t%s\n' "$NOW_ISO_TICK" "$PG_PUBLIC_TABLES" >> "$PG_HIST_LOG"

  if [[ -n "$PREV_LINE" ]]; then
    PREV_ISO=$(printf '%s' "$PREV_LINE" | awk -F'\t' '{print $1}')
    PREV_COUNT=$(printf '%s' "$PREV_LINE" | awk -F'\t' '{print $2}')
    if [[ "$PREV_COUNT" =~ ^[0-9]+$ ]] && (( PREV_COUNT > 0 )); then
      HALF=$(( PREV_COUNT / 2 ))
      if (( PG_PUBLIC_TABLES < HALF )); then
        # Did a schema migration land on PROTEA develop between
        # PREV_ISO and now? If yes the drop is plausibly intentional;
        # downgrade to a warn so we still leave a trail but don't
        # page. If not, P0.
        MIG_HITS=0
        PROTEA_REPO="$HOME/Thesis2/repositories/PROTEA"
        if [[ -d "$PROTEA_REPO/.git" ]]; then
          MIG_HITS=$(git -C "$PROTEA_REPO" log \
            --since="$PREV_ISO" \
            --pretty=oneline \
            -- 'protea/infrastructure/alembic/versions' 2>/dev/null \
            | wc -l | tr -d '[:space:]')
        fi
        if [[ "$MIG_HITS" == "0" ]]; then
          heartbeat "$TASK_ID" critical \
            "P0: pg_tables(public)=$PG_PUBLIC_TABLES dropped from $PREV_COUNT (since $PREV_ISO) with no migration on develop. See state/logs/pg_table_history.log + docs/runbook-pg-volume-recovery.md"
        else
          heartbeat "$TASK_ID" warn \
            "pg_tables(public)=$PG_PUBLIC_TABLES dropped from $PREV_COUNT but $MIG_HITS migration commit(s) since $PREV_ISO; assuming intentional"
        fi
      fi
    fi
  fi
fi

# 1) redeploy (idempotent; exit 0 noop, 10 redeployed, 20/30/40 failure)
bash "$LIB/protea_redeploy.sh"
RC=$?
case "$RC" in
  0)  heartbeat "$TASK_ID" info "redeploy noop (already on tip)" ;;
  10) heartbeat "$TASK_ID" info "redeployed OK" ;;
  20) heartbeat "$TASK_ID" error "redeploy failed (deploy.sh exit $RC)"
      echo "FAIL_KIND=redeploy_fail" > /tmp/deploy-keeper-last-fail.env
      echo "FAIL_EXIT=20" >> /tmp/deploy-keeper-last-fail.env
      exit 1 ;;
  30) heartbeat "$TASK_ID" error "redeploy failed (git fetch exit $RC)"
      echo "FAIL_KIND=redeploy_fail" > /tmp/deploy-keeper-last-fail.env
      echo "FAIL_EXIT=30" >> /tmp/deploy-keeper-last-fail.env
      exit 1 ;;
  40) heartbeat "$TASK_ID" warn "sibling refresh failed (continuing)"
      # not a hard fail; siblings_advanced=0 is degraded but acceptable
      ;;
  *)  heartbeat "$TASK_ID" error "redeploy unknown exit $RC"
      echo "FAIL_KIND=redeploy_fail" > /tmp/deploy-keeper-last-fail.env
      echo "FAIL_EXIT=$RC" >> /tmp/deploy-keeper-last-fail.env
      exit 1 ;;
esac

# 2) ngrok ensure (idempotent; exit 0 up, 1 failed)
bash "$LIB/protea_ngrok_ensure.sh"
RC=$?
if [[ "$RC" -ne 0 ]]; then
  heartbeat "$TASK_ID" error "ngrok ensure failed (exit $RC)"
  echo "FAIL_KIND=ngrok_fail" > /tmp/deploy-keeper-last-fail.env
  echo "FAIL_EXIT=$RC" >> /tmp/deploy-keeper-last-fail.env
  exit 1
fi

# 3) thesis PDF publish (FARM-1.8). Best-effort: build failures here MUST
# NOT crash the tick (the deploy + ngrok above are the load-bearing
# responsibilities of this service; the PDF is a courtesy artefact). The
# publisher itself is idempotent: it skips the latex build when origin/main
# of the thesis repo has not moved since the last successful publish.
bash "$LIB/protea_thesis_pdf_publish.sh"
RC=$?
case "$RC" in
  0) ;;  # noop or success; the publisher already logged details
  1) heartbeat "$TASK_ID" warn "thesis PDF publish: build failed (see state/logs/thesis_pdf_publish.log)" ;;
  2) heartbeat "$TASK_ID" warn "thesis PDF publish: skipped (missing latex toolchain or deploy worktree)" ;;
  *) heartbeat "$TASK_ID" warn "thesis PDF publish: unexpected exit $RC" ;;
esac

heartbeat "$TASK_ID" info "tick OK (deploy + ngrok + thesis pdf)"
exit 0

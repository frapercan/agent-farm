#!/usr/bin/env bash
# deploy-keeper-tick.sh — one tick of the deploy-keeper service.
#
# Reuses battle-tested deploy scripts (, idempotent). Records heartbeats to sqlite.
# Returns:
#   0   tick OK (noop or redeployed cleanly + ngrok up)
#   1   failure — supervisor will escalate to claude -p

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
TASK_ID="${TASK_ID:?TASK_ID env required}"
# shellcheck source=../lib/common.sh
source "$ROOT/scripts/lib/common.sh"

LIB="$ROOT/scripts/services/lib"

# 0) prereq sanity (docker/postgres/rabbit)
if ! docker info >/dev/null 2>&1; then
  heartbeat "$TASK_ID" error "prereq fail: docker daemon not responding"
  echo "FAIL_KIND=prereq_fail" > /tmp/deploy-keeper-last-fail.env
  echo "FAIL_EXIT=1" >> /tmp/deploy-keeper-last-fail.env
  exit 1
fi
if ! ss -ltn 2>/dev/null | grep -q ':5432 '; then
  heartbeat "$TASK_ID" error "prereq fail: postgres not listening on :5432"
  echo "FAIL_KIND=prereq_fail" > /tmp/deploy-keeper-last-fail.env
  echo "FAIL_EXIT=2" >> /tmp/deploy-keeper-last-fail.env
  exit 1
fi
if ! ss -ltn 2>/dev/null | grep -q ':5672 '; then
  heartbeat "$TASK_ID" error "prereq fail: rabbitmq not listening on :5672"
  echo "FAIL_KIND=prereq_fail" > /tmp/deploy-keeper-last-fail.env
  echo "FAIL_EXIT=3" >> /tmp/deploy-keeper-last-fail.env
  exit 1
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

heartbeat "$TASK_ID" info "tick OK (deploy + ngrok)"
exit 0

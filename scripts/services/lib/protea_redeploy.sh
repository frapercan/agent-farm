#!/usr/bin/env bash
# Idempotent redeploy of origin/develop into the PROTEA deploy worktree.
# Skips heavy steps when nothing in their input changed; also pulls every
# sibling stack repo onto origin/develop into the siblings worktree dir
# so the docs portal builds against fresh upstream tips and ignores any
# WIP that other agents have on the regular Thesis2/repositories clones.
#
# Exit codes:
#   0  no-op (PROTEA already on tip and no sibling advanced)
#   10 redeployed (PROTEA or some sibling moved forward)
#   20 deploy script failed
#   30 fetch failed
#   40 a sibling refresh failed (deploy still attempted unless PROTEA also failed)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_FARM_ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"

DEPLOY_PATH="${PROTEA_DEPLOY_PATH:-$HOME/Thesis2/worktrees/protea-deploy}"
SIBLINGS_DIR="${PROTEA_SIBLINGS_DIR:-$HOME/Thesis2/worktrees/_siblings}"
REPOS_DIR="${PROTEA_REPOS_DIR:-$HOME/Thesis2/repositories}"
LOG_FILE="${PROTEA_REDEPLOY_LOG:-$AGENT_FARM_ROOT/state/logs/protea_redeploy.log}"

# Worker-healthcheck (FARM-DK-WORKER-HEALTHCHECK).
# Threshold of consecutive ticks a worker must be missing before we
# count the worker-healthcheck as failed and force BOOTSTRAP. Default 2
# (i.e. one transient miss during a manual `manage.sh restart` does not
# trigger a redundant redeploy). Override via env for tests.
WORKER_MISS_THRESHOLD="${PROTEA_WORKER_MISS_THRESHOLD:-2}"
# Persistent miss-count state file. One key per worker name, value is
# the number of consecutive ticks the worker has been missing. Stored
# under agent-farm state/ so it survives between ticks.
WORKER_MISS_STATE="${PROTEA_WORKER_MISS_STATE:-$AGENT_FARM_ROOT/state/deploy_keeper_worker_miss_count}"

mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$(dirname "$WORKER_MISS_STATE")"

FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1

ts() { date -Is; }
log() { printf '[%s] %s\n' "$(ts)" "$*" | tee -a "$LOG_FILE"; }

# self_heal_heartbeat <level> <message>
# Best-effort heartbeat into agent-farm sqlite. We only emit if TASK_ID
# is set (i.e. when invoked from the deploy-keeper supervisor; outside
# that context the script is run manually or under the FARM-1.6 test
# harness and the heartbeat is a no-op). Always returns 0 so a missing
# task row or sqlite hiccup never crashes the redeploy tick.
self_heal_heartbeat() {
  local level="$1" msg="$2"
  if [[ -z "${TASK_ID:-}" ]]; then
    return 0
  fi
  local db_py="$AGENT_FARM_ROOT/scripts/lib/db.py"
  if [[ ! -f "$db_py" ]]; then
    return 0
  fi
  python3 "$db_py" heartbeat "$TASK_ID" "$level" "$msg" >/dev/null 2>&1 || true
  return 0
}

# verify_workers_alive (FARM-DK-WORKER-HEALTHCHECK)
#
# Scans $DEPLOY_PATH/logs/pids/worker-*.pid (the source-of-truth set
# written by scripts/manage.sh on start, removed on stop) and checks
# each PID with `kill -0`. Workers whose process has died are
# accumulated into a per-worker miss counter persisted at
# $WORKER_MISS_STATE. A worker is only reported as missing once it has
# been absent for $WORKER_MISS_THRESHOLD consecutive ticks; this
# debouncer prevents a one-tick blip during a manual `manage.sh
# restart` from triggering a runaway redeploy.
#
# Sets one global consumed by the main loop below:
#   WORKERS_MISSING_NAMES (comma-separated list of breached workers,
#   only meaningful when the function returns non-zero)
#
# Returns 0 if all workers are alive (or no pid files exist yet, which
# is the "stack is down entirely" case, handled by the existing api
# healthcheck and not duplicated here). Returns 1 iff at least one
# worker is missing for >= $WORKER_MISS_THRESHOLD ticks.
#
# Does NOT touch the API or frontend pid file; those are healthchecked
# upstream by the curl on /jobs. Scope is intentionally worker-only.
verify_workers_alive() {
  WORKERS_MISSING_NAMES=""

  local pids_dir="$DEPLOY_PATH/logs/pids"
  if [[ ! -d "$pids_dir" ]]; then
    # No pid dir at all means the stack has never started (fresh
    # bootstrap) or has been hard-cleared. The existing BOOTSTRAP=1
    # branch above handles "no uvicorn yet"; do not double-fire.
    return 0
  fi

  # Iterate worker pid files only. The API and frontend pid files
  # share the same dir but are watched by the api healthcheck.
  local missing_now=()
  local present_now=()
  local pidfile name pid
  shopt -s nullglob
  for pidfile in "$pids_dir"/worker-*.pid; do
    name=$(basename "$pidfile" .pid)
    pid=$(cat "$pidfile" 2>/dev/null | tr -d '[:space:]' || true)
    if [[ -z "$pid" || ! "$pid" =~ ^[0-9]+$ ]]; then
      missing_now+=("$name")
      continue
    fi
    if kill -0 "$pid" 2>/dev/null; then
      present_now+=("$name")
    else
      missing_now+=("$name")
    fi
  done
  shopt -u nullglob

  # Load prior miss counts (one "name<TAB>count" per line).
  declare -A miss_count=()
  if [[ -f "$WORKER_MISS_STATE" ]]; then
    while IFS=$'\t' read -r mname mcount; do
      [[ -z "$mname" ]] && continue
      [[ "$mcount" =~ ^[0-9]+$ ]] || continue
      miss_count["$mname"]="$mcount"
    done < "$WORKER_MISS_STATE"
  fi

  # Reset counters for workers that are alive this tick.
  local p
  for p in "${present_now[@]}"; do
    miss_count["$p"]=0
  done

  # Increment counters for workers missing this tick.
  local m breached=()
  for m in "${missing_now[@]}"; do
    miss_count["$m"]=$(( ${miss_count["$m"]:-0} + 1 ))
    if (( miss_count["$m"] >= WORKER_MISS_THRESHOLD )); then
      breached+=("$m")
    fi
  done

  # Persist updated counts (atomic via temp + mv).
  local tmp_state="${WORKER_MISS_STATE}.tmp"
  : > "$tmp_state"
  local k
  for k in "${!miss_count[@]}"; do
    printf '%s\t%s\n' "$k" "${miss_count[$k]}" >> "$tmp_state"
  done
  mv -f "$tmp_state" "$WORKER_MISS_STATE"

  if (( ${#breached[@]} > 0 )); then
    # Map worker-* names back to their queue strings for the operator log line:
    #   worker-evaluations          -> protea.evaluations
    #   worker-predictions-batch-1  -> protea.predictions.batch
    #   worker-embeddings-coord     -> protea.embeddings
    #   worker-reaper               -> reaper
    local queues=()
    for m in "${breached[@]}"; do
      local q="${m#worker-}"
      # strip trailing -batch-N to collapse all batch siblings to a single
      # queue label
      q="${q%-batch-[0-9]*}"
      case "$q" in
        embeddings-coord)    q="protea.embeddings" ;;
        embeddings-write)    q="protea.embeddings.write" ;;
        embeddings)          q="protea.embeddings.batch" ;;
        predictions-coord)   q="protea.predictions" ;;
        predictions-write)   q="protea.predictions.write" ;;
        predictions)         q="protea.predictions.batch" ;;
        ping|jobs|training|evaluations) q="protea.$q" ;;
        reaper)              q="reaper" ;;
        *)                   q="protea.$q" ;;
      esac
      queues+=("$q")
    done
    # de-dup while preserving order
    local seen="" dedup=()
    for q in "${queues[@]}"; do
      case ",$seen," in
        *",$q,"*) ;;
        *) dedup+=("$q"); seen="$seen,$q" ;;
      esac
    done
    WORKERS_MISSING_NAMES=$(IFS=','; printf '%s' "${dedup[*]}")
    return 1
  fi
  return 0
}

# Self-seed .env.local with the JWT secret + supporting envs. manage.sh
# starts uvicorn via _start_bg (setsid + &) which needs vars EXPORTED,
# not just shell-local; PROTEA's scripts/deploy.sh does `set -a;
# source .env.local; set +a` so plain KEY=VAL lines also work, but the
# file must exist with sane content. Idempotent: if `export
# PROTEA_JWT_SECRET=` is already present we leave the file alone.
# Otherwise regenerate, preserving any existing secret value if found
# (e.g. file missing the `export ` prefix).
ensure_env_local() {
  local f="$DEPLOY_PATH/.env.local"
  if [[ -f "$f" ]] && grep -q '^export PROTEA_JWT_SECRET=' "$f"; then
    return 0
  fi
  local existing_secret=""
  if [[ -f "$f" ]]; then
    existing_secret=$(grep -oP '^(?:export )?PROTEA_JWT_SECRET=[\"]?\K[A-Fa-f0-9]+' "$f" 2>/dev/null | head -1 || true)
  fi
  local secret="${existing_secret:-$(openssl rand -hex 32)}"
  {
    printf 'export PROTEA_JWT_SECRET=%s\n' "$secret"
    printf 'export PROTEA_AUTHN_REQUIRED=true\n'
    printf 'export PROTEA_ADMIN_TOKEN=protea-admin\n'
  } > "$f"
  chmod 600 "$f"
  if [[ -n "$existing_secret" ]]; then
    log "seeded $f (preserved existing secret)"
  else
    log "seeded $f (generated new secret)"
  fi
}

# 0) Self-heal the deploy worktree if it has been removed. The
# deploy-keeper supervisor used to pause 30 min after consecutive
# failures when the worktree was missing (cf.
# feedback_deploy_worktree_bootstrap memory, 2026-05-11 incident).
# FARM-1.6 makes that recoverable on the next tick: we recreate the
# worktree from origin/develop and continue into the existing redeploy
# logic, which will then bootstrap deps + frontend on its own.
if [[ ! -d "$DEPLOY_PATH" ]]; then
  log "[self-heal] deploy worktree missing at $DEPLOY_PATH; recreating from origin/develop" >&2
  PROTEA_REPO_FOR_HEAL="${PROTEA_REPO:-$REPOS_DIR/PROTEA}"
  if [[ ! -d "$PROTEA_REPO_FOR_HEAL/.git" ]]; then
    log "[self-heal] ERR PROTEA clone not found at $PROTEA_REPO_FOR_HEAL; cannot recreate worktree"
    self_heal_heartbeat error "[self-heal] PROTEA clone missing at $PROTEA_REPO_FOR_HEAL; cannot recreate $DEPLOY_PATH"
    exit 30
  fi
  if ! git -C "$PROTEA_REPO_FOR_HEAL" fetch --quiet origin develop >>"$LOG_FILE" 2>&1; then
    log "[self-heal] ERR fetch origin develop failed"
    self_heal_heartbeat error "[self-heal] fetch origin develop failed; cannot recreate $DEPLOY_PATH"
    exit 30
  fi
  mkdir -p "$(dirname "$DEPLOY_PATH")"
  if ! git -C "$PROTEA_REPO_FOR_HEAL" worktree add "$DEPLOY_PATH" origin/develop >>"$LOG_FILE" 2>&1; then
    log "[self-heal] ERR git worktree add $DEPLOY_PATH origin/develop failed"
    self_heal_heartbeat error "[self-heal] git worktree add failed for $DEPLOY_PATH"
    exit 30
  fi
  log "[self-heal] recreated deploy worktree at $DEPLOY_PATH from origin/develop"
  self_heal_heartbeat info "[self-heal] recreated deploy worktree at $DEPLOY_PATH from origin/develop"
fi

# Test-only short-circuit. Set by tests/test_redeploy_self_heal.sh to
# exercise the self-heal preflight without invoking the full deploy
# pipeline (which needs docker, node, poetry, etc.). NOT consumed by any
# production caller. Exit 0 here means "self-heal preflight passed".
if [[ -n "${PROTEA_REDEPLOY_SELF_HEAL_TEST:-}" ]]; then
  log "[self-heal-test] short-circuit before sibling refresh and deploy"
  exit 0
fi

# 1) Refresh sibling worktrees first. If any of them advanced we want
# the deploy to rebuild the docs even if PROTEA itself is on tip.
PROTEA_SIBLINGS_DIR="$SIBLINGS_DIR" bash "$SCRIPT_DIR/protea_refresh_siblings.sh" >/dev/null
sib_rc=$?
case "$sib_rc" in
  0)  siblings_advanced=0 ;;
  10) siblings_advanced=1; log "siblings advanced, forcing redeploy" ;;
  *)  siblings_advanced=0; log "ERR sibling refresh exit=$sib_rc (continuing)" ;;
esac

cd "$DEPLOY_PATH" || { log "ERR cd $DEPLOY_PATH"; exit 30; }

ensure_env_local

git fetch --quiet origin develop || { log "ERR fetch failed"; exit 30; }

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/develop)

BOOTSTRAP=0
[[ ! -x "$DEPLOY_PATH/.venv/bin/uvicorn" ]] && BOOTSTRAP=1
[[ ! -d "$DEPLOY_PATH/apps/web/node_modules" || ! -d "$DEPLOY_PATH/apps/web/.next" ]] && BOOTSTRAP=1
# Recover from "manage.sh crashed mid-tick, stack down" without waiting
# for a new commit. If the api isn't returning 200 on /jobs, force a
# full redeploy. -m 3 + --fail keeps this cheap on the happy path.
PROTEA_API_HEALTH_URL="${PROTEA_API_HEALTH_URL:-http://localhost:8000/jobs}"
API_OK=1
if ! curl -sf -m 3 -o /dev/null "$PROTEA_API_HEALTH_URL"; then
  API_OK=0
  log "api healthcheck ${PROTEA_API_HEALTH_URL} non-200; forcing BOOTSTRAP"
  BOOTSTRAP=1
fi

# Worker-set healthcheck (FARM-DK-WORKER-HEALTHCHECK). The API can be
# OK while individual worker processes have died independently (the
# 2026-05-18 4h+ orphan-jobs incident, see project_orphan_jobs_2026_05_18).
# verify_workers_alive applies a per-worker debounce counter so a single
# transient miss during a manual `manage.sh restart` does not trigger a
# redundant redeploy; only workers absent for $WORKER_MISS_THRESHOLD
# consecutive ticks count as missing.
if ! verify_workers_alive; then
  if [[ "$API_OK" -eq 1 ]]; then
    log "api healthcheck OK, but workers missing: ${WORKERS_MISSING_NAMES}; forcing BOOTSTRAP"
  else
    log "workers also missing: ${WORKERS_MISSING_NAMES}"
  fi
  BOOTSTRAP=1
fi

if [[ "$FORCE" -eq 0 && "$BOOTSTRAP" -eq 0 && "$LOCAL" == "$REMOTE" && "$siblings_advanced" -eq 0 ]]; then
  log "noop on $REMOTE"
  exit 0
fi

CHANGED=$(git diff --name-only "$LOCAL" "$REMOTE" 2>/dev/null || true)
FORCE_TAG=""; [[ "$FORCE" -eq 1 ]] && FORCE_TAG="force "
SIB_TAG=""; [[ "$siblings_advanced" -eq 1 && "$LOCAL" == "$REMOTE" ]] && SIB_TAG="(siblings only) "
log "redeploy $(git rev-parse --short "$LOCAL") to $(git rev-parse --short "$REMOTE") (${FORCE_TAG}${SIB_TAG})files=$(echo "$CHANGED" | wc -l)"

ARGS=()
if [[ "$BOOTSTRAP" -eq 1 ]]; then
  # Fresh deploy worktree (no uvicorn in .venv). Force a full deploy
  # so deps install and frontend builds at least once before the
  # incremental-skip heuristics below kick in on subsequent ticks.
  log "bootstrap: $DEPLOY_PATH/.venv has no uvicorn; full deploy (deps + build)"
elif [[ "$LOCAL" == "$REMOTE" ]]; then
  # PROTEA didn't move, only siblings did. Skip deps and frontend rebuild;
  # only the docs build matters and deploy.sh runs that unconditionally.
  ARGS+=(--no-deps --no-build)
else
  if ! echo "$CHANGED" | grep -qE '^(pyproject\.toml|poetry\.lock)$'; then
    ARGS+=(--no-deps)
  fi
  if ! echo "$CHANGED" | grep -qE '^apps/web/'; then
    ARGS+=(--no-build)
  fi
fi

log "deploy.sh origin/develop ${ARGS[*]}"
if PROTEA_DEPLOY_PATH="$DEPLOY_PATH" PROTEA_SIBLINGS_DIR="$SIBLINGS_DIR" bash scripts/deploy.sh origin/develop "${ARGS[@]}" >>"$LOG_FILE" 2>&1; then
  log "OK now on $(git rev-parse --short HEAD)"
  exit 10
else
  rc=$?
  log "ERR deploy.sh exit=$rc"
  exit 20
fi

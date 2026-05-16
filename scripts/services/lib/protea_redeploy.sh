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
LOG_FILE="${PROTEA_REDEPLOY_LOG:-$AGENT_FARM_ROOT/state/logs/protea_redeploy.log}"

mkdir -p "$(dirname "$LOG_FILE")"

FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1

ts() { date -Is; }
log() { printf '[%s] %s\n' "$(ts)" "$*" | tee -a "$LOG_FILE"; }

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
if ! curl -sf -m 3 -o /dev/null "$PROTEA_API_HEALTH_URL"; then
  log "api healthcheck ${PROTEA_API_HEALTH_URL} non-200; forcing BOOTSTRAP"
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

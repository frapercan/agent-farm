#!/usr/bin/env bash
# cold-boot.sh -- canonical, FAST, idempotent bring-up of the PROTEA platform.
#
#   bash ~/Thesis2/agent-farm/scripts/cold-boot.sh            # revive (default)
#   bash ~/Thesis2/agent-farm/scripts/cold-boot.sh --deploy   # revive + sync develop + deps
#   bash ~/Thesis2/agent-farm/scripts/cold-boot.sh --status   # print infra state, change nothing
#   bash ~/Thesis2/agent-farm/scripts/cold-boot.sh --quiet    # watchdog mode (silent when healthy)
#
# BOOT IS NOT DEPLOY. A machine reboot must RESTORE what was running, not
# re-deploy develop and not touch CUDA. The old script did both on every run:
# `poetry install` downgraded torch to +cpu from the lock, then
# `install_gpu_torch.sh` re-downloaded cu128. Minutes and gigabytes, every time,
# for nothing. Now:
#
#   * FAST PATH: if containers are healthy, the API answers and ngrok is up,
#     this exits in ~2s having changed nothing.
#   * DEPS ARE REUSED: `poetry install` runs only when poetry.lock actually
#     changed (sha stamped in the venv) or the venv is broken. The GPU torch
#     override runs only when torch is not already CUDA-enabled.
#   * CONTAINERS SELF-HEAL: infra containers get `--restart unless-stopped`, so
#     a machine event no longer leaves them dead (the recurring 3-4x/day pain).
#   * NGROK IS STARTED, not merely warned about (it died overnight for that).
#   * INFRA STATE IS RECORDED to storage/infra_state/{state.json,events.log} so a
#     fresh session (or a context summary) reads what happened instead of
#     re-diagnosing from zero.
#
# Only `--deploy` syncs develop and may reinstall deps. Never `poetry install
# --sync` (pyproject pins torch to pytorch-cpu for CI; --sync wipes local CUDA).
set -euo pipefail

THESIS_ROOT="${THESIS_ROOT:-$HOME/Thesis2}"
DEPLOY="$THESIS_ROOT/worktrees/protea-deploy"
CUDA_VARIANT="${CUDA_VARIANT:-cu128}"   # driver 570/580 compatible
INFRA=(protea-postgres-1 protea-rabbitmq-1 protea-minio-1)
STATE_DIR="$THESIS_ROOT/storage/infra_state"
STATE_JSON="$STATE_DIR/state.json"
EVENTS_LOG="$STATE_DIR/events.log"
STAMP="$DEPLOY/.venv/.coldboot-stamp"

DO_DEPLOY=0; QUIET=0; STATUS_ONLY=0; FORCE_DEPS=0
for a in "$@"; do
  case "$a" in
    --deploy) DO_DEPLOY=1 ;;
    --quiet) QUIET=1 ;;
    --status) STATUS_ONLY=1 ;;
    --force-deps) FORCE_DEPS=1; DO_DEPLOY=1 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "unknown flag: $a" >&2; exit 2 ;;
  esac
done

GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"; BOLD="\033[1m"; RESET="\033[0m"
step() { [[ $QUIET -eq 1 ]] || printf "\n${BOLD}==> %s${RESET}\n" "$*"; }
ok()   { [[ $QUIET -eq 1 ]] || printf "  ${GREEN}OK${RESET} %s\n" "$*"; }
warn() { printf "  ${YELLOW}WARN${RESET} %s\n" "$*"; }

mkdir -p "$STATE_DIR"
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
record_event() { printf '%s\t%s\t%s\n' "$(now)" "$1" "${2:-}" >> "$EVENTS_LOG"; }
die()  { printf "  ${RED}FAIL${RESET} %s\n" "$*" >&2; record_event "boot.failed" "$*"; exit 1; }

# ---------------------------------------------------------------- probes
containers_healthy() {
  for c in "${INFRA[@]}"; do
    [[ "$(docker inspect -f '{{.State.Health.Status}}' "$c" 2>/dev/null)" == "healthy" ]] || return 1
  done
}
api_up()   { curl -fsS --max-time 4 http://localhost:8000/health >/dev/null 2>&1; }
# The public protea.ngrok.app tunnel points at the FRONTEND (:3000), not the API, so
# an API-only probe reports green while the public URL serves 502. Accept any HTTP
# response (the app answers 307): we are probing liveness, not a status code.
frontend_up() { curl -s -o /dev/null --max-time 4 http://localhost:3000 2>/dev/null; }
ngrok_up() { curl -fsS --max-time 4 http://localhost:4040/api/tunnels >/dev/null 2>&1; }
torch_is_cuda() {
  [[ -x "$DEPLOY/.venv/bin/python" ]] || return 1
  "$DEPLOY/.venv/bin/python" -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)" >/dev/null 2>&1
}
torch_version() {
  [[ -x "$DEPLOY/.venv/bin/python" ]] || { echo "?"; return; }
  "$DEPLOY/.venv/bin/python" -c "import torch;print(torch.__version__)" 2>/dev/null || echo "?"
}
lock_sha() { sha256sum "$DEPLOY/poetry.lock" 2>/dev/null | cut -d' ' -f1; }

write_state() {
  local action="$1"
  local sha tun cstates
  sha=$(git -C "$DEPLOY" rev-parse --short HEAD 2>/dev/null || echo "?")
  tun=$(curl -fsS --max-time 4 http://localhost:4040/api/tunnels 2>/dev/null \
    | python3 -c "import json,sys;print(','.join(t['name'] for t in json.load(sys.stdin).get('tunnels',[])))" 2>/dev/null || echo "")
  cstates=""
  for c in "${INFRA[@]}"; do
    cstates+="\"$c\":\"$(docker inspect -f '{{.State.Status}}/{{.HostConfig.RestartPolicy.Name}}' "$c" 2>/dev/null || echo '?')\","
  done
  cstates="${cstates%,}"
  cat > "$STATE_JSON" <<EOF
{
  "updated_at": "$(now)",
  "last_action": "$action",
  "deploy_git_sha": "$sha",
  "torch": "$(torch_version)",
  "cuda_available": $(torch_is_cuda && echo true || echo false),
  "poetry_lock_sha": "$(lock_sha)",
  "containers": { $cstates },
  "api_up": $(api_up && echo true || echo false),
  "frontend_up": $(frontend_up && echo true || echo false),
  "ngrok_tunnels": "$tun"
}
EOF
}

# ---------------------------------------------------------------- --status
if [[ $STATUS_ONLY -eq 1 ]]; then
  write_state "status-probe"
  cat "$STATE_JSON"
  [[ -f "$EVENTS_LOG" ]] && { echo "--- last events ---"; tail -6 "$EVENTS_LOG"; }
  exit 0
fi

# ---------------------------------------------------------------- fast path
# Nothing to do when everything is already green. This is what makes the script
# safe to run from a watchdog every few minutes.
if [[ $DO_DEPLOY -eq 0 ]] && containers_healthy && api_up && frontend_up && ngrok_up; then
  write_state "fast-path"
  [[ $QUIET -eq 1 ]] || printf "${GREEN}${BOLD}infra already healthy${RESET} (containers + API + frontend + ngrok). Nothing to do.\n"
  exit 0
fi

record_event "boot.start" "deploy=$DO_DEPLOY"

# ---------------------------------------------------------------- 1. docker
step "Docker daemon"
docker info >/dev/null 2>&1 || die "docker daemon unreachable -- sudo systemctl start docker"
ok "daemon up (context: $(docker context show 2>/dev/null || echo '?'))"

# ---------------------------------------------------------------- 2. infra
step "Platform containers (postgres + rabbitmq + minio)"
for c in "${INFRA[@]}"; do
  [[ -n "$(docker ps -aq -f name="^${c}$")" ]] \
    || die "$c missing. Recreate from $DEPLOY: docker compose --profile storage up -d postgres rabbitmq minio"
done
if ! containers_healthy; then
  record_event "outage.detected" "containers not healthy"
  docker start "${INFRA[@]}" >/dev/null
fi
# self-heal across machine events: this is why they kept dying on reboot
for c in "${INFRA[@]}"; do
  if [[ "$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$c" 2>/dev/null)" != "unless-stopped" ]]; then
    docker update --restart unless-stopped "$c" >/dev/null && ok "$c restart policy -> unless-stopped"
  fi
done
for i in $(seq 1 45); do containers_healthy && break; sleep 2; done
containers_healthy || die "containers not healthy -- docker logs ${INFRA[0]}"
for c in "${INFRA[@]}"; do ok "$c healthy"; done

# ---------------------------------------------------------------- 3. deps
# The expensive part, and the one that used to run unconditionally.
step "protea-deploy: environment"
[[ -d "$DEPLOY" ]] || die "deploy worktree missing at $DEPLOY (git worktree add it first)"
cd "$DEPLOY"

if [[ $DO_DEPLOY -eq 1 ]]; then
  git fetch origin --quiet
  git reset --hard origin/develop
  ok "synced to origin/develop ($(git rev-parse --short HEAD))"
else
  ok "boot-only: keeping current commit $(git rev-parse --short HEAD) (use --deploy to sync develop)"
fi

need_install=0
[[ -x "$DEPLOY/.venv/bin/python" ]] || need_install=1
[[ $FORCE_DEPS -eq 1 ]] && need_install=1
if [[ -f "$STAMP" ]]; then
  [[ "$(cat "$STAMP" 2>/dev/null)" == "$(lock_sha)" ]] || need_install=1
else
  # no stamp yet: only install if the venv cannot even provide a working torch
  torch_is_cuda || need_install=1
fi

if [[ $need_install -eq 1 ]]; then
  poetry install        # NOTE: never --sync -- it would force the CPU lock
  record_event "deps.installed" "lock=$(lock_sha)"
  ok "deps installed (lock changed or venv rebuilt)"
else
  ok "deps unchanged (lock $(lock_sha | cut -c1-12)) -- skipping poetry install"
fi

# GPU torch override: ONLY when torch is not already CUDA. A plain reboot no
# longer re-downloads cu128.
if torch_is_cuda; then
  ok "torch already CUDA ($(torch_version)) -- skipping GPU override"
else
  warn "torch is not CUDA ($(torch_version)) -- applying GPU override ($CUDA_VARIANT)"
  CUDA_VARIANT="$CUDA_VARIANT" bash scripts/install_gpu_torch.sh >/dev/null
  torch_is_cuda || die "GPU torch override failed -- torch.cuda.is_available() is False"
  record_event "gpu.override" "$(torch_version)"
  ok "torch GPU override applied ($(torch_version))"
fi
printf '%s' "$(lock_sha)" > "$STAMP"

# ---------------------------------------------------------------- 4. app
step "App layer"
# Probe BOTH halves. The API answering on :8000 does not mean the product is up: the
# public tunnel serves the frontend on :3000, and a machine event killed the frontend
# while the API survived, leaving the fast path green and protea.ngrok.app at 502.
if api_up && frontend_up; then
  ok "API :8000 and frontend :3000 already answering -- not restarting"
else
  api_up || record_event "outage.detected" "api down"
  frontend_up || record_event "outage.detected" "frontend down"
  set -a; source .env; [[ -f .env.local ]] && source .env.local; set +a
  bash scripts/manage.sh start
  for i in $(seq 1 30); do api_up && frontend_up && break; sleep 2; done
  api_up || die "API not answering on :8000"
  frontend_up && ok "API :8000 + frontend :3000 up" || die "frontend not answering on :3000"
fi

# ---------------------------------------------------------------- 5. ngrok
# Start it, do not merely warn. Never pkill an existing ngrok.
step "Public tunnel (ngrok)"
if ngrok_up; then
  ok "ngrok already up"
else
  record_event "outage.detected" "ngrok down"
  setsid nohup ngrok start --all --log=stdout > "$STATE_DIR/ngrok.log" 2>&1 &
  for i in $(seq 1 15); do ngrok_up && break; sleep 1; done
  if ngrok_up; then record_event "ngrok.started" ""; ok "ngrok started -> https://protea.ngrok.app"
  else warn "ngrok did not come up -- check $STATE_DIR/ngrok.log"; fi
fi

# ---------------------------------------------------------------- 6. state
write_state "revived"
record_event "boot.complete" "sha=$(git -C "$DEPLOY" rev-parse --short HEAD 2>/dev/null)"

if [[ $QUIET -eq 0 ]]; then
  printf "\n${BOLD}${GREEN}=== cold-boot complete ===${RESET}\n"
  printf "  Frontend  http://localhost:3000\n"
  printf "  API       http://localhost:8000  (public: https://protea.ngrok.app)\n"
  printf "  State     %s\n" "$STATE_JSON"
fi

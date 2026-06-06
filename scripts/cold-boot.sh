#!/usr/bin/env bash
# cold-boot.sh -- canonical bring-up of the PROTEA platform from a
# powered-off machine. Run this when the user says "empezamos de una
# maquina apagada" (we start from a cold box).
#
#   bash ~/Thesis2/agent-farm/scripts/cold-boot.sh
#
# This is the procedure boot.sh only DIAGNOSES. boot.sh never starts
# anything; it audits and reports. cold-boot.sh is the one place that
# actually revives the stack, in the correct order, with the GPU torch
# override that the deploy worktree needs on every fresh install.
#
# Why this script exists (the recurring cold-boot failures):
#   1. Native docker-ce (Docker Desktop was removed): the postgres /
#      rabbitmq / minio containers exit cleanly on shutdown and nobody
#      restarts them. They must be `docker start`ed before anything else.
#   2. `poetry install --sync` is WRONG here. pyproject.toml pins torch
#      to the `pytorch-cpu` source on purpose (GitHub CI has no GPU, see
#      PROTEA PR #122). `--sync` forces the lock and wipes the CUDA torch
#      we install locally. Use plain `poetry install` + the repo's own
#      `scripts/install_gpu_torch.sh` override. We want GPU always.
#   3. The GPU override (`install_gpu_torch.sh`) must run after EVERY
#      `poetry install` / `poetry update`, never with `--no-deps`
#      (cudnn comes in as an nvidia-* dep; without it `import torch`
#      dies with `libcudnn.so.9: cannot open shared object file`).
#
# Idempotent: safe to re-run. Each step checks current state first.
set -euo pipefail

THESIS_ROOT="${THESIS_ROOT:-$HOME/Thesis2}"
DEPLOY="$THESIS_ROOT/worktrees/protea-deploy"
CUDA_VARIANT="${CUDA_VARIANT:-cu128}"   # driver 570/580 compatible
INFRA=(protea-postgres-1 protea-rabbitmq-1 protea-minio-1)

GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"; BOLD="\033[1m"; RESET="\033[0m"
step() { printf "\n${BOLD}==> %s${RESET}\n" "$*"; }
ok()   { printf "  ${GREEN}OK${RESET} %s\n" "$*"; }
warn() { printf "  ${YELLOW}WARN${RESET} %s\n" "$*"; }
die()  { printf "  ${RED}FAIL${RESET} %s\n" "$*" >&2; exit 1; }

# --------------------------------------------------------------------------
# 1. Docker daemon (native docker-ce, default context -- NOT desktop-linux)
# --------------------------------------------------------------------------
step "Docker daemon"
docker info >/dev/null 2>&1 || die "docker daemon unreachable -- sudo systemctl start docker"
ctx=$(docker context show 2>/dev/null || echo "?")
[[ "$ctx" == "default" ]] || warn "docker context is '$ctx' (expected 'default' for native docker-ce)"
ok "daemon up (context: $ctx)"

# --------------------------------------------------------------------------
# 2. Platform containers -- start, then wait healthy. Volumes are preserved
#    (we `docker start` existing containers; we do NOT recreate).
# --------------------------------------------------------------------------
step "Platform containers (postgres + rabbitmq + minio)"
for c in "${INFRA[@]}"; do
  if [[ -z "$(docker ps -aq -f name="^${c}$")" ]]; then
    die "$c missing. Recreate from $DEPLOY: docker compose --profile storage up -d postgres rabbitmq minio"
  fi
done
docker start "${INFRA[@]}" >/dev/null
for i in $(seq 1 45); do
  all_ok=1
  for c in "${INFRA[@]}"; do
    [[ "$(docker inspect -f '{{.State.Health.Status}}' "$c" 2>/dev/null)" == "healthy" ]] || all_ok=0
  done
  [[ $all_ok -eq 1 ]] && break
  sleep 2
done
for c in "${INFRA[@]}"; do
  st=$(docker inspect -f '{{.State.Health.Status}}' "$c" 2>/dev/null || echo "?")
  [[ "$st" == "healthy" ]] && ok "$c healthy" || die "$c not healthy ($st) -- docker logs $c"
done

# --------------------------------------------------------------------------
# 3. Deploy worktree: sync develop, install deps, FLIP torch back to GPU
# --------------------------------------------------------------------------
step "protea-deploy: sync develop + deps + GPU torch override"
[[ -d "$DEPLOY" ]] || die "deploy worktree missing at $DEPLOY (git worktree add it first)"
cd "$DEPLOY"
git fetch origin --quiet
git reset --hard origin/develop
poetry install        # NOTE: never --sync -- it would force the CPU lock
ok "deps installed (CPU torch from lock)"
CUDA_VARIANT="$CUDA_VARIANT" bash scripts/install_gpu_torch.sh >/dev/null
poetry run python -c "import torch; assert torch.cuda.is_available()" \
  && ok "torch GPU override applied (cuda_available=True)" \
  || die "GPU torch override failed -- import torch / torch.cuda.is_available() is False"

# --------------------------------------------------------------------------
# 4. App layer (API + workers + frontend). manage.sh self-sources .env,
#    but we source explicitly too so a naive shell is safe.
# --------------------------------------------------------------------------
step "App layer (manage.sh start)"
set -a; source .env; [[ -f .env.local ]] && source .env.local; set +a
bash scripts/manage.sh start
curl -fsS --max-time 5 http://localhost:8000/health >/dev/null \
  && ok "API /health 200" || die "API not answering on :8000"

# --------------------------------------------------------------------------
# 5. Public tunnel. expose.sh runs in the FOREGROUND (it tails ngrok), so
#    we only remind the user -- launching it here would block this script.
# --------------------------------------------------------------------------
step "Public tunnel (ngrok)"
if pgrep -x ngrok >/dev/null 2>&1; then
  ok "ngrok already running -> https://protea.ngrok.app"
else
  warn "ngrok not running. In a separate terminal: cd $DEPLOY && bash scripts/expose.sh"
fi

printf "\n${BOLD}${GREEN}=== cold-boot complete ===${RESET}\n"
printf "  Frontend  http://localhost:3000\n"
printf "  API       http://localhost:8000  (public: https://protea.ngrok.app)\n"
printf "  Next: run boot.sh to confirm green, then spawn the farm.\n"

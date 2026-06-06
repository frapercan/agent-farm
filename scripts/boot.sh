#!/usr/bin/env bash
# boot.sh — agent-farm session boot diagnostic.
#
# Diagnose-first by policy (see memory: feedback_boot_diagnostic_first).
# Runs a 14-invariant read-only audit. Auto-fixes ONLY two safe cases:
#   - prune ~/Thesis2/worktrees/_siblings/<repo> when HEAD SHA == owning
#     repo's origin/develop AND no dirty diff AND no commits ahead.
#   - re-install FARM-1.4 dev-clone hooks (idempotent).
# Everything else is REPORT-ONLY with a suggested command. NEVER auto:
#   - manage.sh start / API revive / ngrok launch
#   - git reset --hard on any worktree
#   - agent-farm git pull (even if local diff duplicates upstream)
#   - DLQ purge, ghost-job reset, partition mount, deploy-keeper relaunch.
#
# Usage:
#   bash boot.sh                 # full diagnostic + the 2 safe auto-fixes
#   bash boot.sh --audit-only    # diagnostic only, no auto-fixes (use on session exit)
#   bash boot.sh --no-pull       # alias of --audit-only (backward-compat)
#
# Exit codes:
#   0 = green/amber — boot ok (warnings allowed)
#   1 = at least one FAIL — user must intervene before spawning agents
#   2 = SALVAGE CANDIDATES — dirty/unmerged worktrees with possible work
#
# Output: classified lines [FAIL] / [SALV] / [WARN] / [ OK ], followed by
# a one-line summary. The conductor parses the summary + exit code to
# decide whether to gate agent spawning.

set -uo pipefail
ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
THESIS_ROOT="${THESIS_ROOT:-$HOME/Thesis2}"

AUDIT_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --audit-only|--no-pull) AUDIT_ONLY=1 ;;
    -h|--help)
      sed -n '2,28p' "$0"; exit 0 ;;
    *)
      echo "boot.sh: unknown arg '$arg' (use --audit-only or --help)" >&2
      exit 64 ;;
  esac
done

OK_LINES=()
WARN_LINES=()
FAIL_LINES=()
SALV_LINES=()
ok()   { OK_LINES+=("$1"); }
warn() { WARN_LINES+=("$1"); }
fail() { FAIL_LINES+=("$1"); }
salv() { SALV_LINES+=("$1"); }

# ---------------------------------------------------------------------------
# 1. Docker daemon
# ---------------------------------------------------------------------------
if docker info >/dev/null 2>&1; then
  ok "docker daemon: $(docker info --format '{{.ServerVersion}}' 2>/dev/null)"
else
  fail "docker daemon: not reachable. Run: sudo systemctl start docker"
fi

# ---------------------------------------------------------------------------
# 2. Platform containers (postgres + rabbitmq + minio)
# ---------------------------------------------------------------------------
for c in protea-postgres-1 protea-rabbitmq-1 protea-minio-1; do
  state=$(docker inspect -f '{{.State.Health.Status}}' "$c" 2>/dev/null || echo "missing")
  case "$state" in
    healthy)  ok "$c: healthy" ;;
    starting) warn "$c: starting (wait or check 'docker logs $c')" ;;
    missing)  fail "$c: container missing. From worktrees/protea-deploy: docker compose --profile storage up -d postgres rabbitmq minio" ;;
    *)        fail "$c: $state (often just a clean-exit after shutdown). Cold-boot revive: bash $THESIS_ROOT/agent-farm/scripts/cold-boot.sh" ;;
  esac
done

# ---------------------------------------------------------------------------
# 3. PROTEA API on :8000
# ---------------------------------------------------------------------------
if ss -lnt 2>/dev/null | grep -q ':8000 '; then
  if curl -fsS --max-time 3 http://localhost:8000/health >/dev/null 2>&1; then
    ok "API :8000: /health 200"
  else
    warn "API :8000: listening but /health failed"
  fi
else
  fail "API :8000: not listening. Cold-boot revive: bash $THESIS_ROOT/agent-farm/scripts/cold-boot.sh (starts infra + GPU torch + manage.sh start; NEVER poetry install --sync, it wipes GPU torch)"
fi

# ---------------------------------------------------------------------------
# 4. ngrok tunnel
# ---------------------------------------------------------------------------
if pgrep -x ngrok >/dev/null 2>&1; then
  http_code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 4 https://protea.ngrok.app/health 2>/dev/null || echo "000")
  if [[ "$http_code" == "200" ]]; then
    ok "ngrok: tunnel up + /health 200"
  else
    warn "ngrok: process up but tunnel HTTP $http_code (API may be down)"
  fi
else
  fail "ngrok: not running. From protea-deploy: bash scripts/expose.sh"
fi

# ---------------------------------------------------------------------------
# 5. protea-deploy worktree fresh
# ---------------------------------------------------------------------------
DEPLOY="$THESIS_ROOT/worktrees/protea-deploy"
if [[ -e "$DEPLOY/.git" ]]; then
  ( cd "$DEPLOY" && git fetch -q origin develop 2>/dev/null || true )
  deploy_head=$(cd "$DEPLOY" && git rev-parse HEAD 2>/dev/null || echo "?")
  develop_tip=$(cd "$DEPLOY" && git rev-parse origin/develop 2>/dev/null || echo "?")
  if [[ "$deploy_head" == "$develop_tip" ]]; then
    ok "protea-deploy: at origin/develop tip"
  else
    behind=$(cd "$DEPLOY" && git rev-list --count "$deploy_head..$develop_tip" 2>/dev/null || echo "?")
    warn "protea-deploy: $behind commits behind origin/develop (stale). Update (manual): cd $DEPLOY && git fetch origin && git reset --hard origin/develop"
  fi
else
  fail "protea-deploy worktree missing at $DEPLOY"
fi

# ---------------------------------------------------------------------------
# 6. PROTEA dev workspace develop vs origin
# ---------------------------------------------------------------------------
PROTEA_DEV="$THESIS_ROOT/repositories/PROTEA"
if [[ -d "$PROTEA_DEV/.git" ]]; then
  ( cd "$PROTEA_DEV" && git fetch -q origin develop 2>/dev/null || true )
  dirty=$(cd "$PROTEA_DEV" && git status --porcelain | wc -l)
  ahead=$(cd "$PROTEA_DEV" && git rev-list --count origin/develop..HEAD 2>/dev/null || echo "?")
  behind=$(cd "$PROTEA_DEV" && git rev-list --count HEAD..origin/develop 2>/dev/null || echo "?")
  if [[ "$dirty" == "0" && "$ahead" == "0" && "$behind" == "0" ]]; then
    ok "PROTEA dev develop: clean, in sync"
  elif [[ "$dirty" -gt 0 ]]; then
    warn "PROTEA dev develop: $dirty dirty file(s) — inspect: cd $PROTEA_DEV && git status"
  else
    warn "PROTEA dev develop: ahead=$ahead behind=$behind (run git pull --ff-only manually if intended)"
  fi
else
  fail "PROTEA dev workspace missing at $PROTEA_DEV"
fi

# ---------------------------------------------------------------------------
# 7. thesis main vs origin
# ---------------------------------------------------------------------------
THESIS_DIR="$THESIS_ROOT/thesis"
if [[ -d "$THESIS_DIR/.git" ]]; then
  ( cd "$THESIS_DIR" && git fetch -q origin main 2>/dev/null || true )
  t_dirty=$(cd "$THESIS_DIR" && git status --porcelain | wc -l)
  t_behind=$(cd "$THESIS_DIR" && git rev-list --count HEAD..origin/main 2>/dev/null || echo "?")
  t_ahead=$(cd "$THESIS_DIR" && git rev-list --count origin/main..HEAD 2>/dev/null || echo "?")
  if [[ "$t_dirty" == "0" && "$t_ahead" == "0" && "$t_behind" == "0" ]]; then
    ok "thesis main: clean, in sync"
  else
    warn "thesis main: ahead=$t_ahead behind=$t_behind dirty=$t_dirty"
  fi
fi

# ---------------------------------------------------------------------------
# 8. PROTEA .env symlink in dev workspace
# ---------------------------------------------------------------------------
PROTEA_ENV="$PROTEA_DEV/.env"
SECRET="$HOME/.secrets/protea.env"
if [[ -L "$PROTEA_ENV" && -r "$PROTEA_ENV" ]]; then
  ok "PROTEA .env: symlink → $(readlink "$PROTEA_ENV")"
elif [[ -f "$PROTEA_ENV" ]]; then
  warn "PROTEA .env: regular file (expected symlink to $SECRET)"
elif [[ -r "$SECRET" ]]; then
  fail "PROTEA .env: missing. Fix: ln -s $SECRET $PROTEA_ENV"
else
  fail "PROTEA .env: missing AND secret target $SECRET unreadable"
fi

# ---------------------------------------------------------------------------
# 9. Ghost RUNNING jobs in postgres
# ---------------------------------------------------------------------------
# Ghost detection: jobs whose status is RUNNING but started_at is older
# than GHOST_HOURS. Export jobs legitimately take up to ~3h
# (project_farm_exp_13_dispatched_2026_05_25), so the threshold needs to
# leave headroom. Anything beyond 4h with no progress is almost certainly
# orphaned by a worker restart.
GHOST_HOURS=4
ghost_sql="SELECT count(*) FROM job WHERE status='RUNNING' AND started_at < now() - interval '${GHOST_HOURS} hours'"
ghost=$(PGPASSWORD=protea psql -h localhost -U protea -d protea -tA -c "$ghost_sql" 2>&1)
ghost_rc=$?
if [[ $ghost_rc -ne 0 ]]; then
  warn "postgres unreachable, skipping ghost-jobs check (psql: ${ghost})"
elif [[ "$ghost" == "0" ]]; then
  ok "no ghost RUNNING jobs (>${GHOST_HOURS}h stale)"
else
  warn "$ghost ghost RUNNING job(s) >${GHOST_HOURS}h stale (no progress). Inspect: psql -h localhost -U protea -d protea -c \"SELECT id, operation, started_at FROM job WHERE status='RUNNING' ORDER BY started_at\""
fi

# ---------------------------------------------------------------------------
# 10. RabbitMQ queue depths (training + DLQ)
# ---------------------------------------------------------------------------
if docker exec protea-rabbitmq-1 rabbitmqctl --quiet list_queues name messages 2>/dev/null > /tmp/.boot-rmq-$$; then
  rmq_training=$(awk '$1=="protea.training"{print $2}' /tmp/.boot-rmq-$$)
  rmq_dlq=$(awk '$1=="protea.dead-letter"{print $2}' /tmp/.boot-rmq-$$)
  rm -f /tmp/.boot-rmq-$$
  rmq_training=${rmq_training:-0}
  rmq_dlq=${rmq_dlq:-0}
  if [[ "$rmq_training" -gt 0 ]]; then
    warn "protea.training queue: $rmq_training msg(s) waiting (worker needed to drain — EXP.13 or other)"
  else
    ok "protea.training queue: empty"
  fi
  if [[ "$rmq_dlq" -gt 1000 ]]; then
    warn "protea.dead-letter: $rmq_dlq msg(s) accumulated (consider purge after audit)"
  else
    ok "protea.dead-letter: $rmq_dlq msg(s)"
  fi
else
  warn "rabbitmqctl unreachable, skipping queue depths"
  rm -f /tmp/.boot-rmq-$$
fi

# ---------------------------------------------------------------------------
# 11. stack-owner.json coherent
# ---------------------------------------------------------------------------
LOCK="$ROOT/state/stack-owner.json"
if [[ -f "$LOCK" ]]; then
  owner=$(python3 -c "import json; print(json.load(open('$LOCK'))['owner'])" 2>/dev/null || echo "?")
  task=$(python3 -c "import json; print(json.load(open('$LOCK'))['task_id'])" 2>/dev/null || echo "")
  if [[ "$owner" == "free" ]]; then
    ok "stack-owner: free"
  elif [[ -n "$task" ]] && bash "$ROOT/scripts/status.sh" 2>/dev/null | grep -qw "$task"; then
    ok "stack-owner: $owner (task $task alive)"
  else
    warn "stack-owner: $owner (task '$task' NOT in live status). Stale lock — release manually: python3 -c \"import json; p='$LOCK'; d=json.load(open(p)); d['owner']='free'; d['task_id']=''; json.dump(d, open(p,'w'))\""
  fi
else
  ok "stack-owner.json absent (no lock held)"
fi

# ---------------------------------------------------------------------------
# 12. agent-farm.db orphan RUNNING tasks
# ---------------------------------------------------------------------------
running=$(bash "$ROOT/scripts/status.sh" 2>/dev/null | awk 'NR>2 && $4=="running"{print $1}' | wc -l)
if [[ "$running" == "0" ]]; then
  ok "agent-farm tasks: no RUNNING"
else
  ok "agent-farm tasks: $running RUNNING (verify with status.sh)"
fi

# ---------------------------------------------------------------------------
# 13. Worktree salvage audit + _siblings auto-prune (when safe)
#
# For every directory under ~/Thesis2/worktrees/* (skipping the persistent
# ones — _thesis-publish, protea-deploy — which are handled elsewhere):
#   - Classify as CLEAN / DIRTY / UNPUSHED / UNMERGED_BRANCH.
#   - CLEAN _siblings/<repo>: auto-prune if HEAD equals owning repo's
#     origin/develop AND no commits ahead AND not dirty.
#   - Anything DIRTY/UNPUSHED/UNMERGED: SALVAGE candidate (manual review).
# ---------------------------------------------------------------------------
WORKTREES_DIR="$THESIS_ROOT/worktrees"
PERSISTENT_NAMES_RE='^(_thesis-publish|protea-deploy)$'

declare -A _trunk_cache
resolve_trunk() {
  local repo_dir="$1"
  if [[ -n "${_trunk_cache[$repo_dir]:-}" ]]; then
    printf '%s' "${_trunk_cache[$repo_dir]}"; return
  fi
  local trunk
  for cand in develop main; do
    if git -C "$repo_dir" show-ref --verify --quiet "refs/remotes/origin/$cand"; then
      trunk="origin/$cand"; break
    fi
  done
  trunk="${trunk:-origin/main}"
  _trunk_cache[$repo_dir]="$trunk"
  printf '%s' "$trunk"
}

audit_worktree() {
  local wt="$1" is_sibling="${2:-0}"
  local name; name=$(basename "$wt")
  [[ -e "$wt/.git" ]] || { warn "worktree $name: missing .git"; return; }

  local branch dirty unmerged common owning trunk upstream unpushed merged_into ahead head last flag
  branch=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
  dirty=$(git -C "$wt" status --porcelain 2>/dev/null | grep -vE '^\?\?' | wc -l | tr -d ' ')
  unmerged=$(git -C "$wt" diff --name-only --diff-filter=U 2>/dev/null | wc -l | tr -d ' ')
  common=$(git -C "$wt" rev-parse --git-common-dir 2>/dev/null)
  owning=$(dirname "$common")
  trunk=$(resolve_trunk "$owning")

  if [[ "$branch" == "HEAD" || "$branch" == "?" ]]; then
    unpushed="n/a"; merged_into="n/a"
  else
    upstream=$(git -C "$wt" rev-parse --abbrev-ref "${branch}@{u}" 2>/dev/null || echo "")
    if [[ -n "$upstream" ]]; then
      unpushed=$(git -C "$wt" rev-list --count "${upstream}..HEAD" 2>/dev/null || echo "?")
    else
      unpushed="no-upstream"
    fi
    if git -C "$wt" merge-base --is-ancestor HEAD "$trunk" 2>/dev/null; then
      merged_into="yes"
    else
      merged_into="no"
    fi
  fi

  head=$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo "?")
  ahead=$(git -C "$wt" rev-list --count "$trunk..HEAD" 2>/dev/null || echo "?")
  last=$(git -C "$wt" log -1 --format='%cr | %s' 2>/dev/null | head -c 80)

  flag="CLEAN"
  if [[ "$dirty" -gt 0 || "$unmerged" -gt 0 ]]; then
    flag="DIRTY"
  elif [[ "$unpushed" != "n/a" && "$unpushed" != "0" && "$unpushed" != "no-upstream" ]]; then
    flag="UNPUSHED"
  elif [[ "$merged_into" == "no" && "$branch" != "HEAD" ]]; then
    flag="UNMERGED_BRANCH"
  fi

  if [[ "$flag" == "CLEAN" ]]; then
    # Special case: clean _siblings/<repo> whose HEAD is an ancestor of
    # origin/develop (i.e. nothing unique in the worktree) → auto-prune.
    # Relaxed from strict SHA equality so that worktrees that develop has
    # moved past are still considered safe to remove.
    if [[ "$is_sibling" == "1" && "$ahead" == "0" ]]; then
      ( cd "$owning" && git fetch -q origin "${trunk#origin/}" 2>/dev/null || true )
      if git -C "$owning" merge-base --is-ancestor "$head" "$trunk" 2>/dev/null; then
        if [[ "$AUDIT_ONLY" == "0" ]]; then
          if ( cd "$owning" && git worktree remove --force "$wt" >/dev/null 2>&1 ); then
            ok "_siblings/$name: pruned (ancestor of $trunk)"
          else
            warn "_siblings/$name: prune failed (manual: cd $owning && git worktree remove --force $wt)"
          fi
        else
          ok "_siblings/$name: ancestor of $trunk (would prune in normal mode)"
        fi
        return
      fi
    fi
    ok "worktree $name: CLEAN (branch=$branch, $trunk merged=$merged_into, last=$last)"
  else
    salv "worktree $name: $flag branch=$branch dirty=$dirty unmerged_files=$unmerged unpushed=$unpushed merged_into=$merged_into($trunk) last=$last"
  fi
}

if [[ -d "$WORKTREES_DIR" ]]; then
  # 13a — _siblings/* (one level deeper)
  if [[ -d "$WORKTREES_DIR/_siblings" ]]; then
    for sd in "$WORKTREES_DIR/_siblings"/*/; do
      [[ -d "$sd" ]] || continue
      audit_worktree "${sd%/}" 1
    done
    if [[ "$AUDIT_ONLY" == "0" && -z "$(ls -A "$WORKTREES_DIR/_siblings" 2>/dev/null)" ]]; then
      rmdir "$WORKTREES_DIR/_siblings" 2>/dev/null && ok "_siblings: directory empty, removed"
    fi
  fi
  # 13b — every other non-persistent worktree
  while IFS= read -r wt; do
    name=$(basename "$wt")
    [[ "$name" == "_siblings" ]] && continue
    [[ "$name" =~ $PERSISTENT_NAMES_RE ]] && continue
    [[ -e "$wt/.git" ]] || continue
    audit_worktree "$wt" 0
  done < <(find "$WORKTREES_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort)
fi

# ---------------------------------------------------------------------------
# 14. Disk free on Thesis2 partition
# ---------------------------------------------------------------------------
disk_pct=$(df -P "$THESIS_ROOT" | awk 'NR==2{gsub("%","",$5); print $5}')
disk_avail=$(df -h "$THESIS_ROOT" | awk 'NR==2{print $4}')
if [[ "$disk_pct" -lt 80 ]]; then
  ok "disk: ${disk_pct}% used, $disk_avail free"
elif [[ "$disk_pct" -lt 90 ]]; then
  warn "disk: ${disk_pct}% used, $disk_avail free (tight)"
else
  fail "disk: ${disk_pct}% used, $disk_avail free (critical)"
fi

# ---------------------------------------------------------------------------
# Meta: agent-farm repo ff vs origin/main + meta-thesis2 root
# ---------------------------------------------------------------------------
( cd "$ROOT" && git fetch -q origin main 2>/dev/null || true )
# count tracked-file dirt only (exclude ?? untracked lines, which include
# state/, results/, etc. — these are runtime artifacts that don't belong
# in git and aren't gitignored only because the dirs vary across machines)
af_dirty=$(cd "$ROOT" && git status --porcelain 2>/dev/null | grep -vcE '^\?\?')
af_branch=$(cd "$ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null)
af_ahead=$(cd "$ROOT" && git rev-list --count origin/main..HEAD 2>/dev/null || echo "?")
af_behind=$(cd "$ROOT" && git rev-list --count HEAD..origin/main 2>/dev/null || echo "?")
if [[ "$af_dirty" == "0" && "$af_ahead" == "0" && "$af_behind" == "0" ]]; then
  ok "agent-farm ($af_branch): clean, in sync with origin/main"
elif [[ "$af_branch" != "main" ]]; then
  ok "agent-farm: on branch '$af_branch' (ahead=$af_ahead behind=$af_behind dirty=$af_dirty vs origin/main)"
else
  warn "agent-farm main: ahead=$af_ahead behind=$af_behind dirty-tracked=$af_dirty. Resolve manually."
fi

# ---------------------------------------------------------------------------
# Auto-fix: install-dev-hooks (idempotent)
# ---------------------------------------------------------------------------
if [[ "$AUDIT_ONLY" == "0" && -x "$ROOT/scripts/install-dev-hooks.sh" ]]; then
  if bash "$ROOT/scripts/install-dev-hooks.sh" --all >/dev/null 2>&1; then
    ok "install-dev-hooks: applied (idempotent)"
  else
    warn "install-dev-hooks: returned non-zero (re-run manually)"
  fi
fi

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
echo "=== boot.sh @ $(date -Iseconds) (mode: $([[ $AUDIT_ONLY == 1 ]] && echo audit-only || echo full)) ==="
echo
for l in "${FAIL_LINES[@]:-}";  do [[ -n "$l" ]] && echo "[FAIL] $l"; done
for l in "${SALV_LINES[@]:-}";  do [[ -n "$l" ]] && echo "[SALV] $l"; done
for l in "${WARN_LINES[@]:-}";  do [[ -n "$l" ]] && echo "[WARN] $l"; done
for l in "${OK_LINES[@]:-}";    do [[ -n "$l" ]] && echo "[ OK ] $l"; done
echo
echo "summary: ok=${#OK_LINES[@]} warn=${#WARN_LINES[@]} fail=${#FAIL_LINES[@]} salvage=${#SALV_LINES[@]}"

# ---------------------------------------------------------------------------
# Exit code
# ---------------------------------------------------------------------------
if [[ "${#SALV_LINES[@]}" -gt 0 ]]; then
  exit 2
elif [[ "${#FAIL_LINES[@]}" -gt 0 ]]; then
  exit 1
fi
exit 0

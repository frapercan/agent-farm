#!/usr/bin/env bash
# scripts/boot-freshness.sh — session-entry / session-exit freshness probe.
#
# Two responsibilities:
#   1. Ensure ~/Thesis2/agent-farm is up to date with origin/main (ff-only).
#   2. Audit every worktree under ~/Thesis2/worktrees/* and report any that
#      still hold work that has NOT yet landed somewhere safe (dirty tree,
#      unpushed commits, branch not merged into the canonical trunk of its
#      owning repo). The audit is REPORT-ONLY: it never deletes a worktree
#      and never touches dirty files. The human/conductor decides whether
#      to salvage, finalize, or prune.
#
# Usage:
#   bash scripts/boot-freshness.sh              # default: pull + audit
#   bash scripts/boot-freshness.sh --no-pull    # audit only (e.g. on session exit)
#   bash scripts/boot-freshness.sh --json       # machine-readable
#
# Exit codes:
#   0  no salvage candidates
#   2  >=1 worktree has WIP that requires human decision (dirty or unpushed)
#   1  pull failed (e.g. unstaged local changes block ff)
#
# Intended call sites:
#   - prompts/bootstrap-autowork.md step 0 (session entry)
#   - prompts/bootstrap-autowork.md "stop" branch (session exit)

set -uo pipefail

FARM_ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
WORKTREES_DIR="${WORKTREES_DIR:-$HOME/Thesis2/worktrees}"

DO_PULL=1
JSON=0
for arg in "$@"; do
  case "$arg" in
    --no-pull) DO_PULL=0 ;;
    --json)    JSON=1 ;;
    -h|--help)
      sed -n '1,30p' "$0"; exit 0 ;;
    *) echo "unknown arg: $arg" >&2; exit 64 ;;
  esac
done

log()   { [[ $JSON -eq 0 ]] && printf '%s\n' "$*" >&2 || true; }
print() { [[ $JSON -eq 0 ]] && printf '%s\n' "$*"; }

# ── 1. Pull agent-farm ───────────────────────────────────────────────────────
pull_status="skipped"
if [[ $DO_PULL -eq 1 ]]; then
  if [[ ! -d "$FARM_ROOT/.git" ]]; then
    log "WARN: $FARM_ROOT is not a git checkout; skipping pull"
    pull_status="not_a_repo"
  else
    # fetch first so we can compute the lag even if local has commits
    git -C "$FARM_ROOT" fetch --quiet origin main 2>/dev/null || true
    behind=$(git -C "$FARM_ROOT" rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
    ahead=$(git -C "$FARM_ROOT" rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
    dirty=$(git -C "$FARM_ROOT" status --porcelain 2>/dev/null | grep -vE '^\?\?' | wc -l)

    if [[ "$dirty" -gt 0 ]]; then
      log "agent-farm has $dirty tracked-file changes; refusing ff pull (would clobber). behind=$behind ahead=$ahead"
      pull_status="dirty_blocked"
    elif [[ "$behind" -eq 0 ]]; then
      log "agent-farm: up to date (ahead=$ahead)"
      pull_status="up_to_date"
    elif [[ "$ahead" -gt 0 ]]; then
      log "agent-farm: ahead=$ahead behind=$behind — manual rebase/merge needed"
      pull_status="diverged"
    else
      if git -C "$FARM_ROOT" pull --ff-only --quiet origin main 2>/dev/null; then
        log "agent-farm: pulled $behind commit(s) from origin/main"
        pull_status="pulled"
      else
        log "agent-farm: ff-only pull FAILED"
        pull_status="pull_failed"
      fi
    fi
  fi
fi

# ── 2. Worktree audit ────────────────────────────────────────────────────────
salvage_candidates=()
clean_orphans=()

mapfile -t wt_dirs < <(find "$WORKTREES_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort)

declare -A trunk_for_repo
resolve_trunk() {
  local repo_dir="$1"
  if [[ -n "${trunk_for_repo[$repo_dir]:-}" ]]; then
    printf '%s' "${trunk_for_repo[$repo_dir]}"; return
  fi
  local trunk
  for cand in develop main; do
    if git -C "$repo_dir" show-ref --verify --quiet "refs/remotes/origin/$cand"; then
      trunk="origin/$cand"; break
    fi
  done
  trunk="${trunk:-origin/main}"
  trunk_for_repo[$repo_dir]="$trunk"
  printf '%s' "$trunk"
}

PERSISTENT_NAMES_RE='^(_siblings|_thesis-publish|protea-deploy)$'

for wt in "${wt_dirs[@]}"; do
  name=$(basename "$wt")
  [[ "$name" =~ $PERSISTENT_NAMES_RE ]] && continue
  [[ -d "$wt/.git" || -f "$wt/.git" ]] || continue

  branch=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
  # tracked-file dirt only — ignore ??-untracked noise
  dirty=$(git -C "$wt" status --porcelain 2>/dev/null | grep -vE '^\?\?' | wc -l | tr -d ' ')
  unmerged=$(git -C "$wt" diff --name-only --diff-filter=U 2>/dev/null | wc -l | tr -d ' ')

  # owning repo (the common-dir's parent) — trunk is per-repo
  common=$(git -C "$wt" rev-parse --git-common-dir 2>/dev/null)
  owning_repo=$(dirname "$common")
  trunk=$(resolve_trunk "$owning_repo")

  if [[ "$branch" == "HEAD" || "$branch" == "?" ]]; then
    unpushed="n/a"
    merged_into_trunk="n/a"
  else
    upstream=$(git -C "$wt" rev-parse --abbrev-ref "${branch}@{u}" 2>/dev/null || echo "")
    if [[ -n "$upstream" ]]; then
      unpushed=$(git -C "$wt" rev-list --count "${upstream}..HEAD" 2>/dev/null || echo "?")
    else
      unpushed="no-upstream"
    fi
    if git -C "$wt" merge-base --is-ancestor HEAD "$trunk" 2>/dev/null; then
      merged_into_trunk="yes"
    else
      merged_into_trunk="no"
    fi
  fi

  last=$(git -C "$wt" log -1 --format='%cr | %s' 2>/dev/null | head -c 90)

  # classify
  flag=""
  if [[ "$dirty" -gt 0 || "$unmerged" -gt 0 ]]; then
    flag="DIRTY"
  elif [[ "$unpushed" != "n/a" && "$unpushed" != "0" && "$unpushed" != "no-upstream" ]]; then
    flag="UNPUSHED"
  elif [[ "$merged_into_trunk" == "no" && "$branch" != "HEAD" ]]; then
    flag="UNMERGED_BRANCH"
  else
    flag="CLEAN"
  fi

  if [[ "$flag" == "CLEAN" ]]; then
    clean_orphans+=("$name")
  else
    salvage_candidates+=("$name|$flag|branch=$branch|dirty=$dirty|unmerged_files=$unmerged|unpushed=$unpushed|merged_into=$merged_into_trunk($trunk)|last=$last")
  fi
done

# ── 3. Report ────────────────────────────────────────────────────────────────
if [[ $JSON -eq 1 ]]; then
  printf '{\n'
  printf '  "pull_status": "%s",\n' "$pull_status"
  printf '  "salvage_candidates": [\n'
  for i in "${!salvage_candidates[@]}"; do
    sc="${salvage_candidates[$i]}"
    sep=","; [[ $i -eq $((${#salvage_candidates[@]} - 1)) ]] && sep=""
    printf '    "%s"%s\n' "${sc//\"/\\\"}" "$sep"
  done
  printf '  ],\n'
  printf '  "clean_orphans": [\n'
  for i in "${!clean_orphans[@]}"; do
    sep=","; [[ $i -eq $((${#clean_orphans[@]} - 1)) ]] && sep=""
    printf '    "%s"%s\n' "${clean_orphans[$i]}" "$sep"
  done
  printf '  ]\n}\n'
else
  print "=== boot-freshness @ $(date -Iseconds) ==="
  print "agent-farm pull: $pull_status"
  print ""
  if [[ ${#salvage_candidates[@]} -gt 0 ]]; then
    print "SALVAGE CANDIDATES (${#salvage_candidates[@]}) — review BEFORE pruning:"
    for sc in "${salvage_candidates[@]}"; do
      print "  - $sc"
    done
  else
    print "No salvage candidates."
  fi
  print ""
  if [[ ${#clean_orphans[@]} -gt 0 ]]; then
    print "Clean orphans (${#clean_orphans[@]}) — safe to 'git worktree remove' once the owning"
    print "task is finalized:"
    for co in "${clean_orphans[@]}"; do
      print "  - $co"
    done
  fi
fi

if [[ "$pull_status" == "pull_failed" || "$pull_status" == "dirty_blocked" ]]; then
  exit 1
fi
[[ ${#salvage_candidates[@]} -gt 0 ]] && exit 2
exit 0

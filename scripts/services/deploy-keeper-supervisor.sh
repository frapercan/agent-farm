#!/usr/bin/env bash
# deploy-keeper-supervisor.sh -- persistent loop that runs deploy-keeper-tick.sh
# every poll_interval. On tick failure (FAIL_KIND != prereq_fail) the
# supervisor first runs a quick-retry ladder (FARM-1.11) of pure-bash
# ticks; only after the ladder is exhausted does it escalate to a
# janitor subagent via spawn-subagent.sh and enter the long cool-off
# pause. prereq_fail failures are logged + the supervisor backs off;
# the user is the recovery path for daemon-level issues.
#
# FARM-FEAT.4: between consecutive ticks the supervisor watches the
# yaml service.triggers list and short-circuits the poll_interval nap
# when one of the configured triggers fires:
#   - new_commit_on:<ref> : `git fetch` + `rev-parse`; SHA delta fires a tick
#   - ngrok_tunnel_down   : `curl -sfI` against the public ngrok URL
#   - manual              : a marker file (default /tmp/deploy-keeper-manual-trigger),
#                           written by scripts/services/deploy-keeper-trigger.sh.
# Trigger evaluation cadence is governed by TRIGGER_CHECK_INTERVAL_SEC
# (default 60s) and is independent of the yaml poll_interval. The poll
# loop still runs at poll_interval, so the triggers are an additive
# fast-path, not a replacement.
#
# FARM-FEAT.6: the generic persistent-loop core (ladder, escalation,
# cool-off pause, tick/nap overrides) lives in _supervisor-template.sh.
# This file is the deploy-keeper-specific wrapper: it reads the yaml
# poll_interval, owns the trigger subsystem, sets the template
# parameters and the two service hooks (service_escalate +
# service_nap_between_ticks), then sources the template to start the
# loop. Runtime behaviour is unchanged from the pre-FARM-FEAT.6 version.
#
# Spawned by spawn.sh in tmux session. Reads:
#   TASK_ID   -- task UUID (set by spawn.sh)
#   AGENT_FARM_ROOT (default ~/Thesis2/agent-farm)
#
# Termination: Ctrl-C in tmux, or `kill.sh <task_id>`.

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
TASK_ID="${TASK_ID:?TASK_ID env required}"
# shellcheck source=../lib/common.sh
source "$ROOT/scripts/lib/common.sh"
# shellcheck source=../lib/yaml_parse.sh
source "$ROOT/scripts/lib/yaml_parse.sh"

# FARM-2.5: read poll_interval from agents/deploy-keeper.yaml. Fall back
# to 300 if the yaml is missing or unparseable.
DEPLOY_KEEPER_YAML="${DEPLOY_KEEPER_YAML:-$ROOT/agents/deploy-keeper.yaml}"
POLL_INTERVAL_DEFAULT=300
POLL_INTERVAL_SEC=$(parse_yaml_duration "$DEPLOY_KEEPER_YAML" service.poll_interval "$POLL_INTERVAL_DEFAULT")
POLL_INTERVAL_RC=$?
if [[ "$POLL_INTERVAL_RC" -ne 0 ]]; then
  heartbeat "$TASK_ID" warn "yaml poll_interval missing/unparseable in $DEPLOY_KEEPER_YAML, defaulting to ${POLL_INTERVAL_DEFAULT}s"
fi

# FARM-FEAT.4: trigger configuration.
# TRIGGER_CHECK_INTERVAL_SEC is the cadence at which the inner nap loop
# wakes up to evaluate triggers between full ticks. Smaller = faster
# manual/git-commit response; larger = fewer git fetches per minute.
# 60s matches the slice acceptance ("runs every 60s in addition to the
# yaml poll_interval").
TRIGGER_CHECK_INTERVAL_SEC="${TRIGGER_CHECK_INTERVAL_SEC:-60}"
# Path of the manual-trigger marker file. The conductor (or a dashboard
# CommandPalette verb) writes this file to request an out-of-band tick;
# the supervisor consumes it (unlink) when the next check fires.
MANUAL_TRIGGER_FILE="${MANUAL_TRIGGER_FILE:-/tmp/deploy-keeper-manual-trigger}"
# Where we store the last-seen origin/<ref> SHA across ticks. State dir
# survives between supervisor restarts so a freshly-respawned keeper
# does not re-trigger on the same commit it already deployed.
TRIGGER_STATE_DIR="${TRIGGER_STATE_DIR:-$ROOT/state/deploy-keeper-triggers}"
mkdir -p "$TRIGGER_STATE_DIR" 2>/dev/null || true
# Public URL probed by ngrok_tunnel_down. The trigger fires when
# curl -sfI to this URL fails (any non-2xx, dns error, timeout, etc).
NGROK_PROBE_URL="${NGROK_PROBE_URL:-https://protea.ngrok.app/}"
NGROK_PROBE_TIMEOUT_SEC="${NGROK_PROBE_TIMEOUT_SEC:-5}"
# Where the PROTEA repo lives (we fetch from here so the supervisor
# does not touch the deploy worktree). Override via env for tests.
TRIGGER_PROTEA_REPO="${TRIGGER_PROTEA_REPO:-$HOME/Thesis2/repositories/PROTEA}"

# ngrok backoff state: when the probe fails we want to fire one tick
# (the redeploy script re-arms the tunnel) but not flood when the tunnel
# stays down longer than a tick. NGROK_BACKOFF_SEC is the floor between
# consecutive ngrok-triggered ticks; the file holds the last-fire epoch.
NGROK_BACKOFF_SEC="${NGROK_BACKOFF_SEC:-300}"
NGROK_LAST_FIRE_FILE="$TRIGGER_STATE_DIR/ngrok_last_fire"

# FARM-1.11: quick-retry ladder run before the 30-min cool-off pause.
# Each retry is a pure-bash tick (no claude -p), so it costs ~$0.
# Tunable for tests via QUICK_RETRY_LADDER_OVERRIDE (space-separated
# seconds list; supervisor tests use shorter delays to keep wall time
# reasonable). The template builds the ladder from this when set.
if [[ -n "${QUICK_RETRY_LADDER_OVERRIDE:-}" ]]; then
  # shellcheck disable=SC2206
  QUICK_RETRY_LADDER_SEC=($QUICK_RETRY_LADDER_OVERRIDE)
else
  QUICK_RETRY_LADDER_SEC=(30 120 300)
fi

# escalate_to_janitor <fail_kind> -- spawn a janitor subagent (haiku, via
# scripts/spawn-subagent.sh) to investigate the failure. We do NOT block
# on the janitor; spawn-subagent.sh inserts a pending task row and prints
# K=V env so we can record the janitor's task_id back into our own
# heartbeats. The janitor's own task spec will steer it to read the
# deploy-keeper heartbeats and act (PR fix, rerun, notify).
escalate_to_janitor() {
  local fail_kind="$1"
  local spawn_args
  spawn_args=$(jq -Rn \
    --arg task "deploy-keeper-rescue" \
    --arg msg "deploy-keeper $fail_kind fail, see heartbeats for task $TASK_ID" \
    --arg src_task "$TASK_ID" \
    '{task: $task, failure_kind: $msg, source_task_id: $src_task}')
  local spawn_out
  if ! spawn_out=$(bash "$ROOT/scripts/spawn-subagent.sh" janitor "$spawn_args" 2>&1); then
    heartbeat "$TASK_ID" error "janitor spawn failed: $spawn_out"
    return 1
  fi
  local janitor_task
  janitor_task=$(printf '%s\n' "$spawn_out" | grep -oP '^task_id=\K\S+' | head -1)
  heartbeat "$TASK_ID" info "escalated to janitor task_id=${janitor_task:-unknown} fail_kind=$fail_kind"
  return 0
}

# Template hook: deploy-keeper escalates via the deploy-keeper-rescue
# janitor (not the generic service-rescue default).
service_escalate() {
  escalate_to_janitor "$1"
}

# ---------------------------------------------------------------------
# FARM-FEAT.4: service.triggers wiring.
# ---------------------------------------------------------------------
# TRIGGERS is the parsed list (one element per line). Empty when the
# yaml field is absent or unparseable; in that case the triggers
# subsystem is a no-op and the supervisor behaves exactly like the
# pre-FARM-FEAT.4 version.
TRIGGERS=()

# read_triggers: populate TRIGGERS from $DEPLOY_KEEPER_YAML's
# service.triggers list using yaml_get (python+pyyaml). yaml_get prints
# the list as a JSON array; we split on quotes and commas with sed to
# avoid pulling in jq just for this. Empty / malformed yaml means an
# empty TRIGGERS list (no behaviour change from pre-FARM-FEAT.4).
read_triggers() {
  TRIGGERS=()
  [[ -f "$DEPLOY_KEEPER_YAML" ]] || return 0
  local raw
  raw=$(yaml_get "$DEPLOY_KEEPER_YAML" service.triggers 2>/dev/null || printf '')
  [[ -z "$raw" ]] && return 0
  # yaml_get prints list as `["a", "b", "c"]`. Strip brackets + quotes,
  # split on commas, trim whitespace, drop blanks.
  while IFS= read -r line; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" ]] && continue
    TRIGGERS+=("$line")
  done < <(printf '%s\n' "$raw" \
    | tr -d '[]"' \
    | tr ',' '\n')
}

# trigger_new_commit_check: returns 0 if a new commit landed on the ref
# specified by the new_commit_on:<ref> trigger spec. Side effect: writes
# the new SHA to TRIGGER_STATE_DIR/sha_<ref-slug> so a subsequent call
# does not retrigger on the same commit.
#
# The first time we see a ref (no state file) we record the current SHA
# but DO NOT fire, since at supervisor boot every commit is "new" and
# the first tick has already deployed it. Boot-fire would create a
# redeploy-loop on every supervisor restart.
trigger_new_commit_check() {
  local trig="$1"
  local ref="${trig#new_commit_on:}"
  [[ -z "$ref" || "$ref" == "$trig" ]] && return 1
  # ref may be "origin/develop"; slug -> "origin_develop".
  local ref_slug="${ref//\//_}"
  local sha_file="$TRIGGER_STATE_DIR/sha_${ref_slug}"

  # Override hook for tests: TRIGGER_GIT_CMD points at a command
  # (possibly multi-token, e.g. "bash /tmp/git_stub.sh") that accepts
  # the same `fetch` / `rev-parse` subcommands as real git. We split
  # on whitespace via the unquoted expansion so a multi-token override
  # is passed as separate argv entries.
  local repo="${TRIGGER_PROTEA_REPO}"
  [[ -d "$repo/.git" ]] || [[ -n "${TRIGGER_GIT_CMD:-}" ]] || return 1

  # Best-effort fetch: failure (offline, network blip) must not abort
  # the trigger check; we just skip until the next round.
  # shellcheck disable=SC2086
  ${TRIGGER_GIT_CMD:-git} -C "$repo" fetch --quiet origin "${ref#origin/}" >/dev/null 2>&1 || return 1

  local current_sha
  # shellcheck disable=SC2086
  current_sha=$(${TRIGGER_GIT_CMD:-git} -C "$repo" rev-parse "$ref" 2>/dev/null || printf '')
  [[ -z "$current_sha" ]] && return 1

  local prev_sha=""
  [[ -f "$sha_file" ]] && prev_sha=$(<"$sha_file")

  if [[ -z "$prev_sha" ]]; then
    # First sighting: arm without firing.
    printf '%s' "$current_sha" > "$sha_file"
    return 1
  fi

  if [[ "$prev_sha" != "$current_sha" ]]; then
    printf '%s' "$current_sha" > "$sha_file"
    heartbeat "$TASK_ID" info "[trigger] new_commit_on $ref: ${prev_sha:0:7} -> ${current_sha:0:7}"
    return 0
  fi
  return 1
}

# trigger_ngrok_tunnel_down: returns 0 when the ngrok URL probe fails.
# Includes a NGROK_BACKOFF_SEC floor so a sustained outage does not
# spam the tick loop: once we have fired, we wait at least the backoff
# window before firing again. The tick itself runs the ngrok_ensure.sh
# script that recovers the tunnel.
trigger_ngrok_tunnel_down() {
  # Override hook for tests: TRIGGER_CURL_CMD may be multi-token
  # (e.g. "bash /tmp/curl_stub.sh"). Expanded unquoted so the words
  # become separate argv entries.
  local now
  now=$(date +%s)
  # Backoff: don't fire more often than NGROK_BACKOFF_SEC.
  if [[ -f "$NGROK_LAST_FIRE_FILE" ]]; then
    local last_fire
    last_fire=$(<"$NGROK_LAST_FIRE_FILE")
    if [[ "$last_fire" =~ ^[0-9]+$ ]] && (( now - last_fire < NGROK_BACKOFF_SEC )); then
      return 1
    fi
  fi
  # shellcheck disable=SC2086
  if ${TRIGGER_CURL_CMD:-curl} -sfI --max-time "$NGROK_PROBE_TIMEOUT_SEC" "$NGROK_PROBE_URL" >/dev/null 2>&1; then
    return 1
  fi
  printf '%s' "$now" > "$NGROK_LAST_FIRE_FILE"
  heartbeat "$TASK_ID" warn "[trigger] ngrok_tunnel_down: probe failed for $NGROK_PROBE_URL"
  return 0
}

# trigger_manual_check: returns 0 if MANUAL_TRIGGER_FILE exists. Side
# effect: consumes (unlinks) the file so a second loop iteration does
# not retrigger forever. Conductor/CommandPalette writes the file via
# scripts/services/deploy-keeper-trigger.sh.
trigger_manual_check() {
  [[ -f "$MANUAL_TRIGGER_FILE" ]] || return 1
  local reason=""
  reason=$(head -c 200 "$MANUAL_TRIGGER_FILE" 2>/dev/null | tr '\n' ' ')
  rm -f "$MANUAL_TRIGGER_FILE" 2>/dev/null || true
  heartbeat "$TASK_ID" info "[trigger] manual${reason:+ : $reason}"
  return 0
}

# check_triggers: walk the configured TRIGGERS list; return 0 (with
# FIRED_TRIGGER set) the moment one fires. Triggers not listed in yaml
# are skipped, so the field is the load-bearing config.
FIRED_TRIGGER=""
check_triggers() {
  FIRED_TRIGGER=""
  local trig
  for trig in "${TRIGGERS[@]}"; do
    case "$trig" in
      new_commit_on:*)
        if trigger_new_commit_check "$trig"; then
          FIRED_TRIGGER="$trig"
          return 0
        fi
        ;;
      ngrok_tunnel_down)
        if trigger_ngrok_tunnel_down; then
          FIRED_TRIGGER="$trig"
          return 0
        fi
        ;;
      manual)
        if trigger_manual_check; then
          FIRED_TRIGGER="$trig"
          return 0
        fi
        ;;
      *)
        # Unknown trigger spec: warn once and skip. We do NOT abort the
        # supervisor -- a typo in the yaml shouldn't take the service
        # down, but the warn should make the typo discoverable.
        heartbeat "$TASK_ID" warn "[trigger] unknown spec in yaml: $trig (skipping)"
        ;;
    esac
  done
  return 1
}

# nap_with_triggers <total_seconds>: sleep for <total_seconds> divided
# into TRIGGER_CHECK_INTERVAL_SEC chunks. Between each chunk run
# check_triggers; if a trigger fires, return 0 immediately so the
# outer loop can fire a tick. If the full duration elapses without
# a trigger, return 1 (caller continues to next normal-poll tick).
#
# Empty TRIGGERS list short-circuits to a plain nap (no overhead).
nap_with_triggers() {
  local total="$1"
  # Re-read triggers each call so a yaml edit propagates without
  # respawn. read_triggers yields an empty list when the field is
  # absent, which keeps the pre-FARM-FEAT.4 behaviour intact.
  read_triggers
  if [[ "${#TRIGGERS[@]}" -eq 0 ]]; then
    nap "$total"
    return 1
  fi
  local remaining="$total"
  local chunk
  while (( remaining > 0 )); do
    if check_triggers; then
      heartbeat "$TASK_ID" info "[trigger] fired: $FIRED_TRIGGER (forcing early tick)"
      return 0
    fi
    chunk="$TRIGGER_CHECK_INTERVAL_SEC"
    (( chunk > remaining )) && chunk="$remaining"
    nap "$chunk"
    remaining=$((remaining - chunk))
  done
  # One final post-sleep check so a trigger that fires during the last
  # chunk still gets honored before the next tick.
  if check_triggers; then
    heartbeat "$TASK_ID" info "[trigger] fired: $FIRED_TRIGGER (post-nap)"
    return 0
  fi
  return 1
}

# Template hook: deploy-keeper's inter-tick wait is the trigger-aware nap.
service_nap_between_ticks() {
  nap_with_triggers "$1"
}

# Initial trigger read at boot. Re-read on every loop iteration so
# yaml edits propagate without a respawn.
read_triggers
heartbeat "$TASK_ID" info "triggers configured: ${TRIGGERS[*]:-<none>}"

# FARM-FEAT.6: template parameters. The generic loop core lives in
# _supervisor-template.sh and is parameterised by these. shellcheck
# cannot see through the dynamic source below, so it flags these as
# unused; the template consumes them all.
# shellcheck disable=SC2034
{
TICK_SCRIPT="$ROOT/scripts/services/deploy-keeper-tick.sh"
# Tests inject a stub tick via DEPLOY_KEEPER_TICK_CMD; the template
# reads TICK_CMD_OVERRIDE.
TICK_CMD_OVERRIDE="${DEPLOY_KEEPER_TICK_CMD:-}"
POLL_INTERVAL="$POLL_INTERVAL_SEC"
MAX_CONSECUTIVE_FAILURES="${#QUICK_RETRY_LADDER_SEC[@]}"
PAUSE_AFTER_PAUSE_SEC=1800  # 30 min cool-off after the ladder is exhausted
FAIL_KIND_ENV_FILE="${DEPLOY_KEEPER_FAIL_ENV:-/tmp/deploy-keeper-last-fail.env}"
}

# Source the template relative to THIS script (not $ROOT) so a test that
# points AGENT_FARM_ROOT at a fake scaffold still loads the real loop.
SUPERVISOR_SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_supervisor-template.sh
source "$SUPERVISOR_SELF_DIR/_supervisor-template.sh"

#!/usr/bin/env bash
# coord-conductor-tick.sh -- one pass of the missing fourth link.
#
# coord-tick.sh claims a message, writes results/<task_id>/handoff.env with the
# composed prompt, inserts the task row, and stops. Nothing reads that file.
# Verified on 2026-08-12: two well formed messages were claimed within seconds
# and sat as "running" in the pulse with no outcome entry, while both machines
# showed green. The channel transports and does not deliver.
#
# This closes that link on the laptop. It is deliberately the smallest thing
# that can: find an unconsumed handoff, run its prompt, mark it consumed.
#
# THREE BRAKES, because this runs an agent on instructions that arrived over the
# network without a human in the loop:
#
#   1. OFF BY DEFAULT. It does nothing until state/coord-conductor/ENABLED
#      exists. Deleting that file stops it at the next tick without touching
#      systemd.
#   2. ONE AT A TIME. A lock directory, not a pid file, so a crash cannot leave
#      a stale lock that a pid check would misread as live.
#   3. ONE SPAWN PER MESSAGE, EVER. The marker is keyed by message id and is NOT
#      scoped to the boot id, unlike the keeper's own emitted markers. A reboot
#      must not re-run work that already ran; the keeper's re-handoff exists to
#      recover a claim, not to repeat an execution.
#
# TRUST BOUNDARY, stated because it is not obvious: the prompt comes from a
# ledger both machines write. That is the same trust level as a commit either
# machine pushes, and the content contract is enforced on the receive side
# before the handoff is written. It is not a public input, and it is also not
# a local one.
#
# spawn.sh is bypassed on purpose. It routes headless agents through tmux, tmux
# is not installed here, and the only two headless agent definitions are a
# service loop and an embeddings job. Neither takes an arbitrary prompt. When a
# generic headless agent exists, this should call spawn.sh instead.

set -uo pipefail

ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
STATE="${COORD_CONDUCTOR_STATE:-$ROOT/state/coord-conductor}"
RESULTS="${COORD_RESULTS_DIR:-$ROOT/results}"
CLAUDE_BIN="${COORD_CLAUDE_BIN:-$HOME/.local/bin/claude}"
LOG="$STATE/conductor.log"
MAX_SECONDS="${COORD_CONDUCTOR_TIMEOUT:-1800}"

mkdir -p "$STATE/spawned" 2>/dev/null || true

log() { printf '%s %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" >> "$LOG"; }

[[ -f "$STATE/ENABLED" ]] || { echo "disabled (no $STATE/ENABLED)"; exit 0; }
[[ -x "$CLAUDE_BIN" ]] || { log "FATAL claude not executable at $CLAUDE_BIN"; exit 78; }

# Brake 2. mkdir is atomic and leaves nothing to interpret.
LOCK="$STATE/running.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "busy"; exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

shopt -s nullglob
took=0
for hf in "$RESULTS"/*/handoff.env; do
  mid=$(grep -m1 '^message_id=' "$hf" 2>/dev/null | cut -d= -f2-)
  [[ -n "$mid" ]] || continue
  # Brake 3. Not boot scoped: a reboot must not re-run completed work.
  [[ -e "$STATE/spawned/$mid" ]] && continue

  task=$(grep -m1 '^task_id=' "$hf" | cut -d= -f2-)
  model=$(grep -m1 '^model=' "$hf" | cut -d= -f2-)
  # composed_prompt is written as one line by the tick; everything after the
  # first = belongs to the value, including further = characters.
  prompt_path=$(grep -m1 '^composed_prompt=' "$hf" | cut -d= -f2-)
  [[ -n "$prompt_path" ]] || { log "SKIP $mid empty composed_prompt in $hf"; continue; }

  # THE PROMPT IS THE FILE'S CONTENTS, NOT ITS PATH.
  #
  # This line used to pass the path. Six coordination rounds died on it and none
  # of them said so, because the failure is silent by construction: the tick
  # writes composed_prompt as an absolute path built from AGENT_FARM_ROOT, that
  # path goes through a directory alias, and the agent's working directories are
  # the real directories the alias points at. So the agent was handed a location
  # it had no permission to read, its first act was a denied read of its own
  # instructions, and it exited 0. The log recorded DONE. Every light was green
  # and nothing had been delivered -- the same shape as everything else this
  # week.
  #
  # Reading the file here deletes the failure mode instead of widening a
  # permission to survive it. realpath is still worth doing: the results
  # directory is added below so the agent can write its working notes beside the
  # prompt, and it has to be added under the name the sandbox will check.
  prompt_path=$(realpath -e "$prompt_path" 2>/dev/null) \
    || { log "SKIP $mid composed_prompt does not resolve: $prompt_path"; continue; }
  prompt=$(cat "$prompt_path") \
    || { log "SKIP $mid cannot read $prompt_path"; continue; }
  [[ -n "$prompt" ]] || { log "SKIP $mid prompt file is empty: $prompt_path"; continue; }

  # Mark BEFORE spawning. A crash mid-run must not become a re-run: an
  # unfinished message is recoverable by a human reading the log, a duplicated
  # side effect is not.
  : > "$STATE/spawned/$mid"
  log "SPAWN $mid task=$task model=${model:-default} timeout=${MAX_SECONDS}s"

  out="$STATE/spawned/$mid.out"
  # PERMISSIONS. The first self-test (01KZVEZFPASG, 2026-08-12) computed the
  # answer, composed the correct outcome entry, and then stopped to ask a human
  # to approve writing into the coordination checkout. Headless, there is no
  # human, so it exited 0 having written nothing and the log said DONE. That is
  # the same shape of failure as everything else this week: success reported
  # over an empty result.
  #
  # acceptEdits auto-approves FILE EDITS only. It is deliberately not
  # bypassPermissions: the agent is executing a prompt that arrived over the
  # network, and the difference between "may write files" and "may do anything"
  # is the whole of the safety margin here.
  #
  # The second self-test (01KZVFQ61VAW) then stopped one step later, at the
  # push, and said why in its own words: writing a file and publishing it to a
  # remote the other machine reads are different acts, and the second is the
  # outward-facing one. It was right, and it is the first notch whose blast
  # radius leaves this machine.
  #
  # Bash(git:*) is therefore the narrowest thing that closes the round trip: git
  # is auto-approved, every other shell command is not. A wider mode would have
  # worked too and would have bought nothing except the ability to run anything
  # a message asks for.
  #
  # If a round trip stalls again, read the .out file first. The agent has said
  # plainly what it was waiting on both times, and guessing at a wider
  # permission without reading it is how this ends up at bypassPermissions by
  # accident.
  if timeout "$MAX_SECONDS" "$CLAUDE_BIN" -p "$prompt" \
       --permission-mode acceptEdits \
       --allowedTools "Bash(git:*)" \
       --add-dir "${COORD_SHARED_REPO:-$HOME/Thesis2/farm-coord}" \
       > "$out" 2>&1; then
    log "DONE  $mid exit=0 bytes=$(wc -c < "$out" 2>/dev/null || echo 0)"
  else
    rc=$?
    log "FAIL  $mid exit=$rc (124 = hit the ${MAX_SECONDS}s timeout)"
  fi
  took=1
  # One per tick. The supervisor comes back; a queue drained in one pass would
  # defeat the concurrency cap the lock exists to enforce.
  break
done

[[ "$took" = "1" ]] || echo "nothing pending"
exit 0

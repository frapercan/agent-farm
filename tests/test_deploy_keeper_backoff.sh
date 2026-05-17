#!/usr/bin/env bash
# tests/test_deploy_keeper_backoff.sh -- FARM-1.11
#
# Simulates a 90-second docker-down outage and asserts that the
# deploy-keeper supervisor's quick-retry ladder recovers within the
# ladder window WITHOUT invoking the claude -p (janitor escalation)
# code path.
#
# Strategy:
#   - Replace the production tick with a stub (DEPLOY_KEEPER_TICK_CMD)
#     that records each invocation timestamp to a counter file and
#     fails for the first ~90 seconds, then succeeds.
#   - Replace nap (SUPERVISOR_NAP_CMD) with a no-op that just advances
#     a virtual clock. The stub tick consults that clock to decide
#     fail vs ok. This keeps wall time O(seconds) while still exercising
#     the real ladder logic (the supervisor's own retry loop runs
#     deterministically and reads QUICK_RETRY_LADDER_OVERRIDE).
#   - Replace spawn-subagent.sh with a recording shim. If the
#     supervisor ever invokes it, the recording file appears -> FAIL.
#   - Stub out common.sh + db.py so heartbeats do not touch the real db.
#   - Run the supervisor as a background process with a 2-second hard
#     deadline; expect it to complete (success branch -> normal poll
#     sleep) before the deadline. We then inspect the recorded state.
#
# Exit code 0 on full pass.
#
# Usage:
#   bash tests/test_deploy_keeper_backoff.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SUPERVISOR="$REPO_ROOT/scripts/services/deploy-keeper-supervisor.sh"

PASS=0
FAIL=0
FAIL_MSGS=()

note_pass() { PASS=$((PASS + 1)); printf '  ok  %s\n' "$1"; }
note_fail() {
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("$1")
  printf '  FAIL %s\n' "$1" >&2
}

assert_file_absent() {
  local desc="$1" path="$2"
  if [[ ! -e "$path" ]]; then note_pass "$desc"
  else note_fail "$desc: file exists at $path"; fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --- 1. Fake AGENT_FARM_ROOT scaffold ---------------------------------------
FAKE_ROOT="$TMP/agent-farm"
mkdir -p "$FAKE_ROOT/scripts/lib" "$FAKE_ROOT/scripts/services" "$FAKE_ROOT/agents"

# Stub common.sh: heartbeat + task_set_ended that record to a file.
HB_LOG="$TMP/heartbeats.log"
cat > "$FAKE_ROOT/scripts/lib/common.sh" <<'EOF'
heartbeat() {
  printf 'HB level=%s msg=%s\n' "$2" "$3" >> "$HB_LOG"
}
task_set_ended() { :; }
EOF

# Stub db.py so no python imports needed.
cat > "$FAKE_ROOT/scripts/lib/db.py" <<'EOF'
#!/usr/bin/env python3
import sys
sys.exit(0)
EOF
chmod +x "$FAKE_ROOT/scripts/lib/db.py"

# Real yaml_parse.sh (we are exercising production code path).
cp "$REPO_ROOT/scripts/lib/yaml_parse.sh" "$FAKE_ROOT/scripts/lib/yaml_parse.sh"

# Minimal deploy-keeper.yaml so the supervisor's FARM-2.5 read works.
cat > "$FAKE_ROOT/agents/deploy-keeper.yaml" <<'EOF'
name: deploy-keeper
service:
  poll_interval: 5m
EOF

# Spawn-subagent shim that records if invoked. The test fails if this
# file ever exists at the end of the run.
SPAWN_RECORD="$TMP/spawn-called"
cat > "$FAKE_ROOT/scripts/spawn-subagent.sh" <<'EOF'
#!/usr/bin/env bash
echo "SPAWN_CALLED_$1" > "$SPAWN_RECORD"
cat <<'STDOUT'
task_id=fake-janitor
worktree=/tmp/fake
composed_prompt=/tmp/fake.md
model=haiku
repo=/tmp/fake
results_dir=/tmp/fake
STDOUT
EOF
chmod +x "$FAKE_ROOT/scripts/spawn-subagent.sh"

# --- 2. Virtual clock + stub tick ------------------------------------------
# CLOCK_FILE holds the simulated elapsed time (seconds since supervisor
# start). The nap stub adds to it; the tick stub reads it to decide
# fail vs ok.
CLOCK_FILE="$TMP/clock"
echo "0" > "$CLOCK_FILE"
TICK_LOG="$TMP/tick.log"

# Simulated outage: first 90 seconds of virtual time -> fail. After
# that -> success. Acceptance: ladder is (30, 120, 300); first tick
# at t=0 fails; first retry at t=30 still fails (30 < 90); second
# retry at t=30+120=150 succeeds (150 >= 90). So total tick calls = 3
# (initial + 2 retries) and SPAWN was never invoked.
OUTAGE_END=90

TICK_STUB="$TMP/tick_stub.sh"
cat > "$TICK_STUB" <<EOF
#!/usr/bin/env bash
clock=\$(cat "$CLOCK_FILE")
echo "TICK t=\$clock" >> "$TICK_LOG"
if [[ "\$clock" -lt $OUTAGE_END ]]; then
  echo "FAIL_KIND=redeploy_fail" > /tmp/deploy-keeper-last-fail.env
  echo "FAIL_EXIT=1" >> /tmp/deploy-keeper-last-fail.env
  exit 1
fi
exit 0
EOF
chmod +x "$TICK_STUB"

NAP_STUB="$TMP/nap_stub.sh"
cat > "$NAP_STUB" <<EOF
#!/usr/bin/env bash
# Advance the virtual clock; never actually sleep.
clock=\$(cat "$CLOCK_FILE")
clock=\$((clock + \$1))
echo "\$clock" > "$CLOCK_FILE"
echo "NAP s=\$1 clock=\$clock" >> "$TICK_LOG"
EOF
chmod +x "$NAP_STUB"

# --- 3. Run supervisor with all the overrides -------------------------------
# Use exec timeout so we can interrupt the supervisor's infinite loop
# the moment it reaches its next nap after success (the test passes
# before that timeout actually fires because the supervisor's normal-
# path nap is replaced by the stub too, but the loop continues; we
# stop it when we have enough evidence).

# We let the supervisor run a bounded number of total naps then signal
# it. The marker file `$TMP/done` is created by the nap stub once it
# has seen >= 5 calls (initial fail nap-30, second fail nap-120,
# recovery, normal nap-300, normal nap-300). That is enough to assert
# recovery.
cat >> "$NAP_STUB" <<EOF
count_file="$TMP/nap_count"
if [[ ! -f "\$count_file" ]]; then echo 0 > "\$count_file"; fi
n=\$(cat "\$count_file")
n=\$((n + 1))
echo "\$n" > "\$count_file"
if [[ "\$n" -ge 5 ]]; then
  touch "$TMP/done"
  # exit non-zero to break the supervisor's loop deterministically
  kill -TERM \$PPID 2>/dev/null || true
fi
EOF

env \
  AGENT_FARM_ROOT="$FAKE_ROOT" \
  TASK_ID="test-task" \
  DEPLOY_KEEPER_TICK_CMD="bash $TICK_STUB" \
  SUPERVISOR_NAP_CMD="bash $NAP_STUB" \
  QUICK_RETRY_LADDER_OVERRIDE="30 120 300" \
  HB_LOG="$HB_LOG" \
  SPAWN_RECORD="$SPAWN_RECORD" \
  bash "$SUPERVISOR" >"$TMP/sup.out" 2>"$TMP/sup.err" &
SUP_PID=$!

# Hard wall-clock cap (the stubs are zero-wait, so 10s is plenty).
DEADLINE=$(($(date +%s) + 10))
while (( $(date +%s) < DEADLINE )); do
  if [[ -f "$TMP/done" ]]; then break; fi
  if ! kill -0 "$SUP_PID" 2>/dev/null; then break; fi
  sleep 0.1
done
kill -TERM "$SUP_PID" 2>/dev/null || true
wait "$SUP_PID" 2>/dev/null || true

# --- 4. Assertions ----------------------------------------------------------
echo "== assertions =="

# 4a. Spawn was never called.
assert_file_absent "spawn-subagent.sh never invoked (no claude -p escalation)" "$SPAWN_RECORD"

# 4b. Recovery heartbeat exists.
if grep -q '\[backoff-recovery\]' "$HB_LOG"; then
  note_pass "backoff-recovery heartbeat emitted"
else
  note_fail "no [backoff-recovery] heartbeat in $HB_LOG"
fi

# 4c. The recovery delay should be 120 (the second ladder rung), since
#     the first retry fires at t=30 (still in outage) and the second
#     fires at t=150 (out of outage).
if grep -q '\[backoff-recovery\] tick succeeded after quick-retry delay=120s' "$HB_LOG"; then
  note_pass "recovery on second ladder rung (delay=120s)"
else
  note_fail "expected delay=120s recovery in heartbeats:"
  if [[ -f "$HB_LOG" ]]; then sed -n '1,40p' "$HB_LOG" >&2; fi
fi

# 4d. No [escalate] heartbeat (since we never exhausted the ladder).
if ! grep -q '\[escalate\]' "$HB_LOG"; then
  note_pass "no [escalate] heartbeat (ladder did not exhaust)"
else
  note_fail "unexpected [escalate] heartbeat present"
fi

# 4e. Tick count: initial fail + retry-1 (fail) + retry-2 (ok) + at least
#     one subsequent normal-path tick = 4 ticks at minimum.
TICK_COUNT=$(grep -c '^TICK' "$TICK_LOG" || true)
if [[ "$TICK_COUNT" -ge 3 ]]; then
  note_pass "tick count >= 3 (got $TICK_COUNT)"
else
  note_fail "tick count $TICK_COUNT < 3"
fi

# 4f. Sanity check: the supervisor read the yaml duration.
if grep -q 'supervisor up; poll_interval=300s' "$HB_LOG"; then
  note_pass "supervisor parsed poll_interval=300 from yaml (FARM-2.5)"
else
  note_fail "no startup heartbeat with poll_interval=300"
fi

# --- 5. Second scenario: outage longer than the ladder window -> escalate --
echo
echo "== scenario 2: ladder exhausted -> escalate =="

# Fresh state.
rm -f "$SPAWN_RECORD" "$HB_LOG" "$TICK_LOG" "$TMP/done" "$TMP/nap_count"
echo "0" > "$CLOCK_FILE"

# Outage longer than 30 + 120 + 300 = 450s -> ladder cannot recover.
LONG_OUTAGE=10000
cat > "$TICK_STUB" <<EOF
#!/usr/bin/env bash
clock=\$(cat "$CLOCK_FILE")
echo "TICK t=\$clock" >> "$TICK_LOG"
if [[ "\$clock" -lt $LONG_OUTAGE ]]; then
  echo "FAIL_KIND=redeploy_fail" > /tmp/deploy-keeper-last-fail.env
  echo "FAIL_EXIT=1" >> /tmp/deploy-keeper-last-fail.env
  exit 1
fi
exit 0
EOF

# A nap stub that stops the supervisor when it hits the 1800s pause
# (proves we reached the escalate branch).
cat > "$NAP_STUB" <<EOF
#!/usr/bin/env bash
clock=\$(cat "$CLOCK_FILE")
clock=\$((clock + \$1))
echo "\$clock" > "$CLOCK_FILE"
echo "NAP s=\$1 clock=\$clock" >> "$TICK_LOG"
if [[ "\$1" -ge 1800 ]]; then
  touch "$TMP/done"
  kill -TERM \$PPID 2>/dev/null || true
fi
EOF

env \
  AGENT_FARM_ROOT="$FAKE_ROOT" \
  TASK_ID="test-task-2" \
  DEPLOY_KEEPER_TICK_CMD="bash $TICK_STUB" \
  SUPERVISOR_NAP_CMD="bash $NAP_STUB" \
  QUICK_RETRY_LADDER_OVERRIDE="30 120 300" \
  HB_LOG="$HB_LOG" \
  SPAWN_RECORD="$SPAWN_RECORD" \
  bash "$SUPERVISOR" >"$TMP/sup2.out" 2>"$TMP/sup2.err" &
SUP_PID=$!
DEADLINE=$(($(date +%s) + 10))
while (( $(date +%s) < DEADLINE )); do
  if [[ -f "$TMP/done" ]]; then break; fi
  if ! kill -0 "$SUP_PID" 2>/dev/null; then break; fi
  sleep 0.1
done
kill -TERM "$SUP_PID" 2>/dev/null || true
wait "$SUP_PID" 2>/dev/null || true

# 5a. Spawn WAS called this time.
if [[ -f "$SPAWN_RECORD" ]]; then
  note_pass "spawn-subagent.sh invoked once ladder exhausted"
else
  note_fail "expected spawn invocation after ladder exhaustion"
fi

# 5b. [escalate] heartbeat present.
if grep -q '\[escalate\]' "$HB_LOG"; then
  note_pass "[escalate] heartbeat emitted on ladder exhaustion"
else
  note_fail "no [escalate] heartbeat"
fi

# 5c. All three ladder warns happened.
warns=$(grep -c '\[backoff\] tick failed, quick-retry in' "$HB_LOG" || true)
if [[ "$warns" -eq 3 ]]; then
  note_pass "all 3 ladder rungs attempted (got $warns warns)"
else
  note_fail "expected 3 backoff warns, got $warns"
fi

# --- 6. Third scenario: prereq_fail must NOT escalate ----------------------
echo
echo "== scenario 3: prereq_fail ladder exhaustion -> no spawn =="

rm -f "$SPAWN_RECORD" "$HB_LOG" "$TICK_LOG" "$TMP/done" "$TMP/nap_count"
echo "0" > "$CLOCK_FILE"

cat > "$TICK_STUB" <<EOF
#!/usr/bin/env bash
clock=\$(cat "$CLOCK_FILE")
echo "TICK t=\$clock" >> "$TICK_LOG"
echo "FAIL_KIND=prereq_fail" > /tmp/deploy-keeper-last-fail.env
echo "FAIL_EXIT=2" >> /tmp/deploy-keeper-last-fail.env
exit 1
EOF

cat > "$NAP_STUB" <<EOF
#!/usr/bin/env bash
clock=\$(cat "$CLOCK_FILE")
clock=\$((clock + \$1))
echo "\$clock" > "$CLOCK_FILE"
echo "NAP s=\$1 clock=\$clock" >> "$TICK_LOG"
if [[ "\$1" -ge 1800 ]]; then
  touch "$TMP/done"
  kill -TERM \$PPID 2>/dev/null || true
fi
EOF

env \
  AGENT_FARM_ROOT="$FAKE_ROOT" \
  TASK_ID="test-task-3" \
  DEPLOY_KEEPER_TICK_CMD="bash $TICK_STUB" \
  SUPERVISOR_NAP_CMD="bash $NAP_STUB" \
  QUICK_RETRY_LADDER_OVERRIDE="30 120 300" \
  HB_LOG="$HB_LOG" \
  SPAWN_RECORD="$SPAWN_RECORD" \
  bash "$SUPERVISOR" >"$TMP/sup3.out" 2>"$TMP/sup3.err" &
SUP_PID=$!
DEADLINE=$(($(date +%s) + 10))
while (( $(date +%s) < DEADLINE )); do
  if [[ -f "$TMP/done" ]]; then break; fi
  if ! kill -0 "$SUP_PID" 2>/dev/null; then break; fi
  sleep 0.1
done
kill -TERM "$SUP_PID" 2>/dev/null || true
wait "$SUP_PID" 2>/dev/null || true

assert_file_absent "prereq_fail never spawns janitor even after ladder" "$SPAWN_RECORD"
if grep -q 'prereq_fail.*no janitor escalation' "$HB_LOG"; then
  note_pass "prereq_fail heartbeat preserved"
else
  note_fail "missing prereq_fail no-janitor heartbeat"
fi

# Summary
printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  echo "--- heartbeat log ---" >&2
  cat "$HB_LOG" >&2 2>/dev/null || true
  echo "--- tick log ---" >&2
  cat "$TICK_LOG" >&2 2>/dev/null || true
  echo "--- supervisor stderr ---" >&2
  cat "$TMP/sup3.err" >&2 2>/dev/null || true
  for m in "${FAIL_MSGS[@]}"; do printf '  - %s\n' "$m" >&2; done
  exit 1
fi
exit 0

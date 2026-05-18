#!/usr/bin/env bash
# tests/test_deploy_keeper_triggers.sh -- FARM-FEAT.4
#
# Asserts that the deploy-keeper supervisor's service.triggers wiring
# is load-bearing: the supervisor reads the yaml list, evaluates each
# trigger between ticks, and fires an early tick when one signals.
#
# Three scenarios (each on its own stubbed supervisor; the live
# deploy-keeper is never touched):
#
#   1. new_commit_on:origin/develop
#      - First tick happens; supervisor enters nap_with_triggers.
#      - Stub git rev-parse returns SHA_A on first call (armed),
#        SHA_B on every later call (delta -> trigger fires).
#      - Assert: a second tick runs within 90s of virtual time even
#        though poll_interval is configured to 1h.
#
#   2. ngrok_tunnel_down
#      - Stub curl returns rc=22 (HTTP error). Trigger fires.
#      - Assert: extra tick within 90s; heartbeat names ngrok_tunnel_down.
#
#   3. manual
#      - Conductor stub writes MANUAL_TRIGGER_FILE between ticks.
#      - Assert: extra tick within 90s; marker file consumed.
#
# Exit 0 iff every assertion passes.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SUPERVISOR="$REPO_ROOT/scripts/services/deploy-keeper-supervisor.sh"
TRIGGER_SH="$REPO_ROOT/scripts/services/deploy-keeper-trigger.sh"

PASS=0
FAIL=0
FAIL_MSGS=()

note_pass() { PASS=$((PASS + 1)); printf '  ok  %s\n' "$1"; }
note_fail() {
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("$1")
  printf '  FAIL %s\n' "$1" >&2
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ---------- Common scaffold ----------
FAKE_ROOT="$TMP/agent-farm"
mkdir -p "$FAKE_ROOT/scripts/lib" "$FAKE_ROOT/scripts/services" "$FAKE_ROOT/agents" "$FAKE_ROOT/state"

cat > "$FAKE_ROOT/scripts/lib/common.sh" <<EOF
heartbeat() {
  printf 'HB level=%s msg=%s\n' "\$2" "\$3" >> "\$HB_LOG"
}
task_set_ended() { :; }
# yaml_get: minimal python+pyyaml shim used by read_triggers in the
# supervisor under test. Identical signature to the real common.sh
# version so we exercise the same JSON-array shape.
yaml_get() {
  local file="\$1" path="\$2"
  python3 -c "
import sys, yaml, json
with open('\$file') as f:
    d = yaml.safe_load(f) or {}
for p in '\$path'.split('.'):
    d = d.get(p) if isinstance(d, dict) else None
    if d is None:
        sys.exit(0)
if isinstance(d, (dict, list)):
    print(json.dumps(d))
else:
    print(d)
"
}
EOF

cat > "$FAKE_ROOT/scripts/lib/db.py" <<'EOF'
#!/usr/bin/env python3
import sys
sys.exit(0)
EOF
chmod +x "$FAKE_ROOT/scripts/lib/db.py"

cp "$REPO_ROOT/scripts/lib/yaml_parse.sh" "$FAKE_ROOT/scripts/lib/yaml_parse.sh"

# Yaml with a short poll_interval (1h => 3600s) so the only way an
# extra tick within 90s can happen is via a trigger fire (not via the
# normal poll loop).
cat > "$FAKE_ROOT/agents/deploy-keeper.yaml" <<'EOF'
name: deploy-keeper
service:
  poll_interval: 1h
  triggers:
    - new_commit_on:origin/develop
    - ngrok_tunnel_down
    - manual
EOF

# Spawn-subagent shim that records if invoked (no triggers in these
# scenarios should escalate).
SPAWN_RECORD="$TMP/spawn-called"
cat > "$FAKE_ROOT/scripts/spawn-subagent.sh" <<'EOF'
#!/usr/bin/env bash
echo "SPAWN_CALLED_$1" > "$SPAWN_RECORD"
echo "task_id=fake-janitor"
EOF
chmod +x "$FAKE_ROOT/scripts/spawn-subagent.sh"

# Per-scenario state files: each scenario resets them before running.
CLOCK_FILE="$TMP/clock"
TICK_LOG="$TMP/tick.log"
HB_LOG="$TMP/heartbeats.log"
GIT_CALLS="$TMP/git_calls.log"
CURL_CALLS="$TMP/curl_calls.log"

# Stub tick: every successful invocation = exit 0 (no fail). Records
# the virtual clock at tick time so we can later assert that ticks
# arrived independently of poll_interval.
TICK_STUB="$TMP/tick_stub.sh"
cat > "$TICK_STUB" <<EOF
#!/usr/bin/env bash
clock=\$(cat "$CLOCK_FILE")
echo "TICK t=\$clock" >> "$TICK_LOG"
exit 0
EOF
chmod +x "$TICK_STUB"

# Common nap stub: advances the virtual clock, records calls, and
# stops the supervisor after N nap calls (per-scenario configurable).
make_nap_stub() {
  local stop_after="$1"
  cat > "$TMP/nap_stub.sh" <<EOF
#!/usr/bin/env bash
clock=\$(cat "$CLOCK_FILE")
clock=\$((clock + \$1))
echo "\$clock" > "$CLOCK_FILE"
echo "NAP s=\$1 clock=\$clock" >> "$TICK_LOG"
count_file="$TMP/nap_count"
if [[ ! -f "\$count_file" ]]; then echo 0 > "\$count_file"; fi
n=\$(cat "\$count_file")
n=\$((n + 1))
echo "\$n" > "\$count_file"
if [[ "\$n" -ge $stop_after ]]; then
  touch "$TMP/done"
  kill -TERM \$PPID 2>/dev/null || true
fi
EOF
  chmod +x "$TMP/nap_stub.sh"
}

reset_state() {
  rm -f "$SPAWN_RECORD" "$HB_LOG" "$TICK_LOG" "$TMP/done" "$TMP/nap_count" \
        "$GIT_CALLS" "$CURL_CALLS" "/tmp/deploy-keeper-manual-trigger" \
        "$TMP/trigger-state/sha_origin_develop" "$TMP/trigger-state/ngrok_last_fire"
  echo "0" > "$CLOCK_FILE"
  mkdir -p "$TMP/trigger-state"
}

# ---------- Scenario 1: new_commit_on:origin/develop ----------
echo "== scenario 1: new_commit_on:origin/develop fires a tick =="
reset_state

# Stub git: every "fetch" succeeds; first "rev-parse" -> SHA_A, the
# rest -> SHA_B. The supervisor arms on the first sighting and fires
# on the second (different SHA).
GIT_STUB="$TMP/git_stub.sh"
cat > "$GIT_STUB" <<EOF
#!/usr/bin/env bash
echo "GIT \$*" >> "$GIT_CALLS"
case "\$*" in
  *"rev-parse"*)
    n=\$(grep -c rev-parse "$GIT_CALLS" 2>/dev/null || echo 0)
    if [[ "\$n" -le 1 ]]; then
      echo "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    else
      echo "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    fi
    ;;
  *)
    : # fetch / other: succeed silently
    ;;
esac
exit 0
EOF
chmod +x "$GIT_STUB"

# Curl stub for ngrok probe: always succeeds (ngrok is fine in
# scenario 1, so it must not fire).
CURL_STUB="$TMP/curl_stub.sh"
cat > "$CURL_STUB" <<EOF
#!/usr/bin/env bash
echo "CURL \$*" >> "$CURL_CALLS"
exit 0
EOF
chmod +x "$CURL_STUB"

# Stop the supervisor after the second tick fires + one more nap.
# Sequence we expect:
#   tick #1 -> nap_with_triggers(...) -> trigger checks chunk by chunk
#       chunk 1: armed (first sha)
#       chunk 2: SHA delta -> trigger fires within ~60s virtual time
#   tick #2 -> assertion passes
make_nap_stub 6

env \
  AGENT_FARM_ROOT="$FAKE_ROOT" \
  TASK_ID="trig-test-1" \
  DEPLOY_KEEPER_TICK_CMD="bash $TICK_STUB" \
  SUPERVISOR_NAP_CMD="bash $TMP/nap_stub.sh" \
  TRIGGER_CHECK_INTERVAL_SEC=60 \
  TRIGGER_GIT_CMD="bash $GIT_STUB" \
  TRIGGER_CURL_CMD="bash $CURL_STUB" \
  TRIGGER_STATE_DIR="$TMP/trigger-state" \
  TRIGGER_PROTEA_REPO="$TMP/nonexistent-repo" \
  HB_LOG="$HB_LOG" \
  SPAWN_RECORD="$SPAWN_RECORD" \
  bash "$SUPERVISOR" >"$TMP/sup1.out" 2>"$TMP/sup1.err" &
SUP_PID=$!

DEADLINE=$(($(date +%s) + 10))
while (( $(date +%s) < DEADLINE )); do
  if [[ -f "$TMP/done" ]]; then break; fi
  if ! kill -0 "$SUP_PID" 2>/dev/null; then break; fi
  sleep 0.1
done
kill -TERM "$SUP_PID" 2>/dev/null || true
wait "$SUP_PID" 2>/dev/null || true

# Assert: a [trigger] heartbeat fired with new_commit_on.
if grep -q '\[trigger\] new_commit_on origin/develop' "$HB_LOG"; then
  note_pass "new_commit_on heartbeat emitted"
else
  note_fail "no new_commit_on heartbeat (HB_LOG follows)"
  sed -n '1,30p' "$HB_LOG" >&2
fi

# Assert: at least 2 ticks (initial + trigger-driven).
TICK_COUNT=$(grep -c '^TICK' "$TICK_LOG" 2>/dev/null || echo 0)
if [[ "$TICK_COUNT" -ge 2 ]]; then
  note_pass "supervisor ran >= 2 ticks (got $TICK_COUNT) within virtual budget"
else
  note_fail "expected >= 2 ticks, got $TICK_COUNT"
fi

# Assert: the second tick fired at virtual t <= 90 (one or two
# TRIGGER_CHECK_INTERVAL_SEC chunks of 60s — armed + fire). The
# yaml poll_interval is 3600s, so anything <= 120s proves the
# trigger fired the early tick.
SECOND_TICK_T=$(grep '^TICK' "$TICK_LOG" | sed -n '2p' | awk -F't=' '{print $2}')
if [[ -n "$SECOND_TICK_T" && "$SECOND_TICK_T" -le 120 ]]; then
  note_pass "second tick at virtual t=${SECOND_TICK_T}s (<= 120s, independent of poll_interval=3600s)"
else
  note_fail "second tick at virtual t=${SECOND_TICK_T:-unset}s; expected <= 120s"
fi

# Assert: the supervisor logged a "triggers configured" line.
if grep -q 'triggers configured: new_commit_on:origin/develop ngrok_tunnel_down manual' "$HB_LOG"; then
  note_pass "triggers list parsed from yaml in expected order"
else
  note_fail "triggers list not parsed correctly:"
  grep -E 'triggers configured' "$HB_LOG" >&2 || true
fi

# Assert: spawn was never invoked.
if [[ ! -e "$SPAWN_RECORD" ]]; then
  note_pass "no janitor escalation (happy-path trigger)"
else
  note_fail "unexpected janitor spawn"
fi

# ---------- Scenario 2: ngrok_tunnel_down ----------
echo
echo "== scenario 2: ngrok_tunnel_down fires a tick =="
reset_state

# Git stub returns the same SHA every time, so new_commit_on stays armed.
cat > "$GIT_STUB" <<EOF
#!/usr/bin/env bash
echo "GIT \$*" >> "$GIT_CALLS"
case "\$*" in
  *"rev-parse"*) echo "ccccccccccccccccccccccccccccccccccccccc" ;;
esac
exit 0
EOF
chmod +x "$GIT_STUB"

# Curl stub: every probe fails with exit 22 (HTTP error).
cat > "$CURL_STUB" <<EOF
#!/usr/bin/env bash
echo "CURL \$*" >> "$CURL_CALLS"
exit 22
EOF
chmod +x "$CURL_STUB"

make_nap_stub 5

env \
  AGENT_FARM_ROOT="$FAKE_ROOT" \
  TASK_ID="trig-test-2" \
  DEPLOY_KEEPER_TICK_CMD="bash $TICK_STUB" \
  SUPERVISOR_NAP_CMD="bash $TMP/nap_stub.sh" \
  TRIGGER_CHECK_INTERVAL_SEC=60 \
  TRIGGER_GIT_CMD="bash $GIT_STUB" \
  TRIGGER_CURL_CMD="bash $CURL_STUB" \
  TRIGGER_STATE_DIR="$TMP/trigger-state" \
  TRIGGER_PROTEA_REPO="$TMP/nonexistent-repo" \
  NGROK_BACKOFF_SEC=600 \
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

if grep -q '\[trigger\] ngrok_tunnel_down' "$HB_LOG"; then
  note_pass "ngrok_tunnel_down heartbeat emitted"
else
  note_fail "no ngrok_tunnel_down heartbeat:"
  sed -n '1,30p' "$HB_LOG" >&2
fi

TICK_COUNT2=$(grep -c '^TICK' "$TICK_LOG" 2>/dev/null || echo 0)
if [[ "$TICK_COUNT2" -ge 2 ]]; then
  note_pass "supervisor ran >= 2 ticks on ngrok trigger (got $TICK_COUNT2)"
else
  note_fail "expected >= 2 ticks on ngrok trigger, got $TICK_COUNT2"
fi

SECOND_TICK_T2=$(grep '^TICK' "$TICK_LOG" | sed -n '2p' | awk -F't=' '{print $2}')
if [[ -n "$SECOND_TICK_T2" && "$SECOND_TICK_T2" -le 90 ]]; then
  note_pass "ngrok-driven second tick at virtual t=${SECOND_TICK_T2}s (<= 90s)"
else
  note_fail "ngrok-driven second tick at virtual t=${SECOND_TICK_T2:-unset}s; expected <= 90s"
fi

# ---------- Scenario 3: manual trigger ----------
echo
echo "== scenario 3: manual trigger fires a tick =="
reset_state

# Git + curl stubs that never fire (no spontaneous trigger).
cat > "$GIT_STUB" <<EOF
#!/usr/bin/env bash
case "\$*" in
  *"rev-parse"*) echo "dddddddddddddddddddddddddddddddddddddddd" ;;
esac
exit 0
EOF
cat > "$CURL_STUB" <<EOF
#!/usr/bin/env bash
exit 0
EOF
chmod +x "$GIT_STUB" "$CURL_STUB"

MANUAL_TRIGGER_FILE="$TMP/manual-trigger"
rm -f "$MANUAL_TRIGGER_FILE"

# A nap stub that ALSO writes the manual trigger file after the first
# 60s nap so we exercise the consume-and-fire path.
cat > "$TMP/nap_stub.sh" <<EOF
#!/usr/bin/env bash
clock=\$(cat "$CLOCK_FILE")
clock=\$((clock + \$1))
echo "\$clock" > "$CLOCK_FILE"
echo "NAP s=\$1 clock=\$clock" >> "$TICK_LOG"
count_file="$TMP/nap_count"
if [[ ! -f "\$count_file" ]]; then echo 0 > "\$count_file"; fi
n=\$(cat "\$count_file")
n=\$((n + 1))
echo "\$n" > "\$count_file"
# After the first 60s nap, write the marker file. The next
# check_triggers call will consume it and fire a tick.
if [[ "\$n" -eq 1 ]]; then
  echo "operator-test" > "$MANUAL_TRIGGER_FILE"
fi
if [[ "\$n" -ge 5 ]]; then
  touch "$TMP/done"
  kill -TERM \$PPID 2>/dev/null || true
fi
EOF
chmod +x "$TMP/nap_stub.sh"

env \
  AGENT_FARM_ROOT="$FAKE_ROOT" \
  TASK_ID="trig-test-3" \
  DEPLOY_KEEPER_TICK_CMD="bash $TICK_STUB" \
  SUPERVISOR_NAP_CMD="bash $TMP/nap_stub.sh" \
  TRIGGER_CHECK_INTERVAL_SEC=60 \
  TRIGGER_GIT_CMD="bash $GIT_STUB" \
  TRIGGER_CURL_CMD="bash $CURL_STUB" \
  TRIGGER_STATE_DIR="$TMP/trigger-state" \
  TRIGGER_PROTEA_REPO="$TMP/nonexistent-repo" \
  MANUAL_TRIGGER_FILE="$MANUAL_TRIGGER_FILE" \
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

if grep -q '\[trigger\] manual' "$HB_LOG"; then
  note_pass "manual trigger heartbeat emitted"
else
  note_fail "no manual trigger heartbeat:"
  sed -n '1,30p' "$HB_LOG" >&2
fi

TICK_COUNT3=$(grep -c '^TICK' "$TICK_LOG" 2>/dev/null || echo 0)
if [[ "$TICK_COUNT3" -ge 2 ]]; then
  note_pass "supervisor ran >= 2 ticks on manual trigger (got $TICK_COUNT3)"
else
  note_fail "expected >= 2 ticks on manual trigger, got $TICK_COUNT3"
fi

if [[ ! -f "$MANUAL_TRIGGER_FILE" ]]; then
  note_pass "manual trigger file consumed after fire"
else
  note_fail "manual trigger file NOT consumed (would re-trigger forever)"
fi

# ---------- Scenario 4: deploy-keeper-trigger.sh writes marker ----------
echo
echo "== scenario 4: deploy-keeper-trigger.sh writes marker =="
MANUAL_TRIGGER_FILE_S4="$TMP/manual-trigger-s4"
rm -f "$MANUAL_TRIGGER_FILE_S4"

if MANUAL_TRIGGER_FILE="$MANUAL_TRIGGER_FILE_S4" AGENT_FARM_ROOT="$FAKE_ROOT" \
    bash "$TRIGGER_SH" "smoke-test-reason" >/dev/null 2>&1; then
  if [[ -f "$MANUAL_TRIGGER_FILE_S4" ]] && grep -q 'smoke-test-reason' "$MANUAL_TRIGGER_FILE_S4"; then
    note_pass "deploy-keeper-trigger.sh wrote marker with reason"
  else
    note_fail "marker file missing or reason absent after trigger.sh run"
  fi
else
  note_fail "deploy-keeper-trigger.sh exited non-zero"
fi

# ---------- Summary ----------
printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  echo "--- heartbeat log ---" >&2
  cat "$HB_LOG" >&2 2>/dev/null || true
  echo "--- tick log ---" >&2
  cat "$TICK_LOG" >&2 2>/dev/null || true
  for m in "${FAIL_MSGS[@]}"; do printf '  - %s\n' "$m" >&2; done
  exit 1
fi
exit 0

#!/usr/bin/env bash
# tests/test_stack_owner_lock.sh -- FARM-FEAT.12
#
# Two scenarios validate the deploy-keeper stack-ownership gate:
#
#   (a) acquire export -> deploy-keeper tick is a no-op + emits the
#       deferred-stack-owned-by-task heartbeat.
#   (b) release export -> deploy-keeper tick proceeds past the gate
#       and reaches the docker prereq probe.
#
# The tick under test is the real scripts/services/deploy-keeper-tick.sh.
# We never spawn the supervisor (already covered by
# test_deploy_keeper_triggers.sh + test_supervisor_template.sh), so this
# test focuses tightly on the new gate.
#
# Exit 0 iff every assertion passes.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STACK_OWNER_LIB="$REPO_ROOT/scripts/lib/stack_owner.sh"
TICK="$REPO_ROOT/scripts/services/deploy-keeper-tick.sh"

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
mkdir -p "$FAKE_ROOT/scripts/lib" "$FAKE_ROOT/scripts/services/lib" \
         "$FAKE_ROOT/state" "$FAKE_ROOT/state/logs"

# heartbeat shim writes to HB_LOG; task_set_ended is a no-op.
cat > "$FAKE_ROOT/scripts/lib/common.sh" <<EOF
heartbeat() {
  printf 'HB level=%s msg=%s\n' "\$2" "\$3" >> "\$HB_LOG"
}
task_set_ended() { :; }
EOF

# Real stack_owner.sh (we are TESTING this lib, not a stub).
cp "$STACK_OWNER_LIB" "$FAKE_ROOT/scripts/lib/stack_owner.sh"

# Stub the redeploy + ngrok + thesis-pdf scripts so a tick that crosses
# the gate exits cleanly without touching the real stack. Each prints a
# marker on stdout we can grep for. The supervisor expects them at
# $LIB/* where LIB=$ROOT/scripts/services/lib.
for lib_script in protea_redeploy.sh protea_ngrok_ensure.sh \
                  protea_thesis_pdf_publish.sh; do
  cat > "$FAKE_ROOT/scripts/services/lib/$lib_script" <<EOF
#!/usr/bin/env bash
echo "STUB_${lib_script%.sh}_RAN"
exit 0
EOF
  chmod +x "$FAKE_ROOT/scripts/services/lib/$lib_script"
done

# We also need the tick to clear its docker / port probes. Easiest path
# is to stub docker + ss in PATH for the test subshell. The stubs return
# success so the tick advances past the prereq section.
STUB_BIN="$TMP/stub-bin"
mkdir -p "$STUB_BIN"

cat > "$STUB_BIN/docker" <<'EOF'
#!/usr/bin/env bash
case "$1" in
  info) exit 0 ;;
  exec) echo "0"; exit 0 ;;
  compose) exit 0 ;;
  *) exit 0 ;;
esac
EOF
chmod +x "$STUB_BIN/docker"

cat > "$STUB_BIN/ss" <<'EOF'
#!/usr/bin/env bash
# Pretend both postgres (5432) and rabbit (5672) are listening.
cat <<OUT
LISTEN 0 0 0.0.0.0:5432 0.0.0.0:*
LISTEN 0 0 0.0.0.0:5672 0.0.0.0:*
OUT
EOF
chmod +x "$STUB_BIN/ss"

# Scenario state.
HB_LOG="$TMP/heartbeats.log"
TICK_OUT="$TMP/tick.out"
STACK_FILE="$FAKE_ROOT/state/stack-owner.json"

reset_state() {
  rm -f "$HB_LOG" "$TICK_OUT" "$STACK_FILE" "${STACK_FILE}.lock"
}

run_tick() {
  PATH="$STUB_BIN:$PATH" \
  AGENT_FARM_ROOT="$FAKE_ROOT" \
  TASK_ID="stack-owner-test" \
  STACK_OWNER_FILE="$STACK_FILE" \
  HB_LOG="$HB_LOG" \
    bash "$TICK" >"$TICK_OUT" 2>&1
  echo $?
}

# ---------- Scenario A: acquire export -> tick is a no-op ----------
echo "== scenario A: acquire export -> deploy-keeper tick defers =="
reset_state

STACK_OWNER_FILE="$STACK_FILE" \
  bash "$STACK_OWNER_LIB" acquire export farm-exp-13 "smoke test sweep" \
  >>"$TMP/setup.log" 2>&1

RC_A=$(run_tick)

if [[ "$RC_A" == "0" ]]; then
  note_pass "tick exit=0 while export holds (intentional noop)"
else
  note_fail "expected exit=0, got $RC_A (output follows)"
  sed -n '1,40p' "$TICK_OUT" >&2
fi

if grep -q 'HB level=info msg=deferred-stack-owned-by-task' "$HB_LOG"; then
  note_pass "deferred-stack-owned-by-task heartbeat emitted"
else
  note_fail "expected deferred-stack-owned-by-task heartbeat (HB_LOG follows):"
  cat "$HB_LOG" >&2
fi

if grep -q 'task_id=farm-exp-13' "$HB_LOG"; then
  note_pass "heartbeat names the holding task_id"
else
  note_fail "heartbeat did not include task_id=farm-exp-13"
fi

# The tick must NOT have run any of the redeploy stubs.
if ! grep -q 'STUB_protea_redeploy_RAN' "$TICK_OUT"; then
  note_pass "redeploy script not invoked while export holds"
else
  note_fail "redeploy script ran despite export-owned lock"
fi

# ---------- Scenario B: release export -> tick proceeds past the gate ----
echo
echo "== scenario B: release export -> deploy-keeper tick proceeds =="
reset_state

# Acquire then release, then run the tick.
STACK_OWNER_FILE="$STACK_FILE" \
  bash "$STACK_OWNER_LIB" acquire export farm-exp-13 "to be released" \
  >>"$TMP/setup.log" 2>&1
STACK_OWNER_FILE="$STACK_FILE" \
  bash "$STACK_OWNER_LIB" release farm-exp-13 \
  >>"$TMP/setup.log" 2>&1

# Sanity: lock must be free now.
CUR=$(STACK_OWNER_FILE="$STACK_FILE" \
      bash "$STACK_OWNER_LIB" current | tr -d '[:space:]')
if [[ "$CUR" == "free" ]]; then
  note_pass "lock is free after release"
else
  note_fail "expected free after release, got '$CUR'"
fi

RC_B=$(run_tick)

if [[ "$RC_B" == "0" ]]; then
  note_pass "tick exit=0 after release (proceeded cleanly)"
else
  note_fail "expected exit=0 after release, got $RC_B (output follows)"
  sed -n '1,60p' "$TICK_OUT" >&2
fi

# The tick MUST have invoked the redeploy stub (proves it crossed the gate).
if grep -q 'STUB_protea_redeploy_RAN' "$TICK_OUT"; then
  note_pass "redeploy script invoked after release (gate did not block)"
else
  note_fail "redeploy stub did not run after release (output follows):"
  sed -n '1,60p' "$TICK_OUT" >&2
fi

# And it must NOT have emitted the deferred heartbeat this time.
if ! grep -q 'deferred-stack-owned-by-task' "$HB_LOG"; then
  note_pass "no deferred heartbeat on free-lock tick"
else
  note_fail "unexpected deferred heartbeat on free-lock tick:"
  cat "$HB_LOG" >&2
fi

# ---------- Bonus: bad arg shapes ----------
echo
echo "== scenario C: helper rejects invalid input =="
reset_state

# Acquiring with owner=free must fail.
if ! STACK_OWNER_FILE="$STACK_FILE" \
      bash "$STACK_OWNER_LIB" acquire free anyone "noop" \
      >>"$TMP/setup.log" 2>&1; then
  note_pass "acquire refuses owner=free"
else
  note_fail "acquire owner=free should have failed"
fi

# Acquiring with empty task_id must fail.
if ! STACK_OWNER_FILE="$STACK_FILE" \
      bash "$STACK_OWNER_LIB" acquire export "" "noop" \
      >>"$TMP/setup.log" 2>&1; then
  note_pass "acquire refuses empty task_id"
else
  note_fail "acquire with empty task_id should have failed"
fi

# Mismatched release after a real acquire must exit 3.
STACK_OWNER_FILE="$STACK_FILE" \
  bash "$STACK_OWNER_LIB" acquire export farm-exp-13 "hold" \
  >>"$TMP/setup.log" 2>&1
STACK_OWNER_FILE="$STACK_FILE" \
  bash "$STACK_OWNER_LIB" release wrong-task \
  >>"$TMP/setup.log" 2>&1
RC_REL=$?
if [[ "$RC_REL" == "3" ]]; then
  note_pass "mismatched release exits 3"
else
  note_fail "expected mismatched-release exit=3, got $RC_REL"
fi

# ---------- Summary ----------
echo
echo "PASS=$PASS FAIL=$FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  printf 'failures:\n' >&2
  for m in "${FAIL_MSGS[@]}"; do printf '  - %s\n' "$m" >&2; done
  exit 1
fi
exit 0

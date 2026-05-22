#!/usr/bin/env bash
# tests/test_supervisor_template.sh -- FARM-FEAT.6
#
# Exercises the generic scripts/services/_supervisor-template.sh through
# the example examples/queue-watcher/queue-watcher-supervisor.sh, proving
# the loop core (happy poll, quick-retry ladder, escalate-on-exhaustion,
# prereq_fail no-escalate) is reusable by a second persistent service
# with NO trigger subsystem and NO custom escalation hook.
#
# Same virtual-clock strategy as test_deploy_keeper_backoff.sh: stub the
# tick + nap so wall time is O(seconds).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SUPERVISOR="$REPO_ROOT/examples/queue-watcher/queue-watcher-supervisor.sh"

PASS=0
FAIL=0
FAIL_MSGS=()
note_pass() { PASS=$((PASS + 1)); printf '  ok  %s\n' "$1"; }
note_fail() { FAIL=$((FAIL + 1)); FAIL_MSGS+=("$1"); printf '  FAIL %s\n' "$1" >&2; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

FAKE_ROOT="$TMP/agent-farm"
mkdir -p "$FAKE_ROOT/scripts/lib" "$FAKE_ROOT/scripts/services" "$FAKE_ROOT/agents"

HB_LOG="$TMP/heartbeats.log"
cat > "$FAKE_ROOT/scripts/lib/common.sh" <<'EOF'
heartbeat() { printf 'HB level=%s msg=%s\n' "$2" "$3" >> "$HB_LOG"; }
task_set_ended() { :; }
EOF
cat > "$FAKE_ROOT/scripts/lib/db.py" <<'EOF'
#!/usr/bin/env python3
import sys
sys.exit(0)
EOF
chmod +x "$FAKE_ROOT/scripts/lib/db.py"
cp "$REPO_ROOT/scripts/lib/yaml_parse.sh" "$FAKE_ROOT/scripts/lib/yaml_parse.sh"
# The example sources the template by absolute path under its own dir, so
# copy the real template into the fake root's services dir.
cp "$REPO_ROOT/scripts/services/_supervisor-template.sh" "$FAKE_ROOT/scripts/services/_supervisor-template.sh"

# Spawn shim records invocations.
SPAWN_RECORD="$TMP/spawn-called"
cat > "$FAKE_ROOT/scripts/spawn-subagent.sh" <<'EOF'
#!/usr/bin/env bash
echo "SPAWN_CALLED_$1" > "$SPAWN_RECORD"
echo "task_id=fake-janitor"
EOF
chmod +x "$FAKE_ROOT/scripts/spawn-subagent.sh"

CLOCK_FILE="$TMP/clock"
TICK_LOG="$TMP/tick.log"
FAIL_ENV="$TMP/qw-fail.env"

run_supervisor() {
  local task="$1"
  env \
    AGENT_FARM_ROOT="$FAKE_ROOT" \
    TASK_ID="$task" \
    QUEUE_WATCHER_TICK_CMD="bash $TMP/tick_stub.sh" \
    SUPERVISOR_NAP_CMD="bash $TMP/nap_stub.sh" \
    QUICK_RETRY_LADDER_OVERRIDE="30 120 300" \
    QUEUE_WATCHER_FAIL_ENV="$FAIL_ENV" \
    HB_LOG="$HB_LOG" \
    SPAWN_RECORD="$SPAWN_RECORD" \
    bash "$SUPERVISOR" >"$TMP/sup.out" 2>"$TMP/sup.err" &
  local pid=$!
  local deadline=$(($(date +%s) + 10))
  while (( $(date +%s) < deadline )); do
    [[ -f "$TMP/done" ]] && break
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.1
  done
  kill -TERM "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

# ---------- Scenario 1: ladder recovers, no escalation ----------
echo "== scenario 1: quick-retry ladder recovers =="
rm -f "$SPAWN_RECORD" "$HB_LOG" "$TICK_LOG" "$TMP/done" "$TMP/nap_count"
echo "0" > "$CLOCK_FILE"

OUTAGE_END=90
cat > "$TMP/tick_stub.sh" <<EOF
#!/usr/bin/env bash
clock=\$(cat "$CLOCK_FILE")
echo "TICK t=\$clock" >> "$TICK_LOG"
if [[ "\$clock" -lt $OUTAGE_END ]]; then
  echo "FAIL_KIND=stalled_queue" > "$FAIL_ENV"
  exit 1
fi
exit 0
EOF
cat > "$TMP/nap_stub.sh" <<EOF
#!/usr/bin/env bash
clock=\$(cat "$CLOCK_FILE"); clock=\$((clock + \$1)); echo "\$clock" > "$CLOCK_FILE"
cf="$TMP/nap_count"; [[ -f "\$cf" ]] || echo 0 > "\$cf"
n=\$(cat "\$cf"); n=\$((n + 1)); echo "\$n" > "\$cf"
if [[ "\$n" -ge 5 ]]; then touch "$TMP/done"; kill -TERM \$PPID 2>/dev/null || true; fi
EOF
run_supervisor "qw-test-1"

if grep -q 'supervisor up; poll_interval=120s' "$HB_LOG"; then
  note_pass "template parsed poll_interval=120 from example yaml"
else
  note_fail "no startup heartbeat with poll_interval=120"; sed -n '1,10p' "$HB_LOG" >&2
fi
if grep -q '\[backoff-recovery\]' "$HB_LOG"; then
  note_pass "ladder recovery heartbeat emitted via template"
else
  note_fail "no [backoff-recovery] heartbeat"
fi
if [[ ! -e "$SPAWN_RECORD" ]]; then
  note_pass "no escalation when ladder recovers"
else
  note_fail "unexpected escalation on recovery"
fi

# ---------- Scenario 2: ladder exhausted -> default escalate ----------
echo
echo "== scenario 2: ladder exhausted escalates via default hook =="
rm -f "$SPAWN_RECORD" "$HB_LOG" "$TICK_LOG" "$TMP/done" "$TMP/nap_count"
echo "0" > "$CLOCK_FILE"

cat > "$TMP/tick_stub.sh" <<EOF
#!/usr/bin/env bash
echo "TICK" >> "$TICK_LOG"
echo "FAIL_KIND=stalled_queue" > "$FAIL_ENV"
exit 1
EOF
cat > "$TMP/nap_stub.sh" <<EOF
#!/usr/bin/env bash
clock=\$(cat "$CLOCK_FILE"); clock=\$((clock + \$1)); echo "\$clock" > "$CLOCK_FILE"
if [[ "\$1" -ge 900 ]]; then touch "$TMP/done"; kill -TERM \$PPID 2>/dev/null || true; fi
EOF
run_supervisor "qw-test-2"

if [[ -f "$SPAWN_RECORD" ]] && grep -q 'SPAWN_CALLED_janitor' "$SPAWN_RECORD"; then
  note_pass "default service_escalate spawned a janitor on exhaustion"
else
  note_fail "expected default janitor escalation"
fi
if grep -q '\[escalate\]' "$HB_LOG"; then
  note_pass "[escalate] heartbeat emitted"
else
  note_fail "no [escalate] heartbeat"
fi

# ---------- Scenario 3: prereq_fail must NOT escalate ----------
echo
echo "== scenario 3: prereq_fail does not escalate =="
rm -f "$SPAWN_RECORD" "$HB_LOG" "$TICK_LOG" "$TMP/done" "$TMP/nap_count"
echo "0" > "$CLOCK_FILE"

cat > "$TMP/tick_stub.sh" <<EOF
#!/usr/bin/env bash
echo "TICK" >> "$TICK_LOG"
echo "FAIL_KIND=prereq_fail" > "$FAIL_ENV"
exit 1
EOF
run_supervisor "qw-test-3"

if [[ ! -e "$SPAWN_RECORD" ]]; then
  note_pass "prereq_fail never escalates"
else
  note_fail "prereq_fail spawned a janitor (must not)"
fi

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  echo "--- heartbeats ---" >&2; cat "$HB_LOG" >&2 2>/dev/null || true
  for m in "${FAIL_MSGS[@]}"; do printf '  - %s\n' "$m" >&2; done
  exit 1
fi
exit 0

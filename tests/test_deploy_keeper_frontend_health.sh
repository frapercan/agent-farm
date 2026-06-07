#!/usr/bin/env bash
# tests/test_deploy_keeper_frontend_health.sh
# Slice: FARM-DEPLOY.1
#
# Verifies the frontend health-gate functions added to
# scripts/services/lib/protea_redeploy.sh:
#
#   1. is_frontend_healthy() returns 0 when a server is listening on
#      $PROTEA_FRONTEND_URL and non-zero when nothing is.
#   2. frontend_healthcheck_failed_debounce() stays in grace window on
#      first miss (returns 1).
#   3. Breaches threshold on the Nth consecutive miss (returns 0).
#   4. frontend_healthcheck_reset_debounce() clears the counter.
#   5. ensure_frontend_up() resets counter when frontend is healthy.
#   6. ensure_frontend_up() defers recovery on first miss (grace window).
#   7. ensure_frontend_up() triggers recovery after threshold is breached.
#   8. recover_frontend() launches a detached process and writes a pid file.
#
# Strategy: extract function definitions from protea_redeploy.sh (same awk
# approach used by test_deploy_keeper_worker_healthcheck.sh) and source
# them in a controlled sandbox. A python3 HTTP server is used to simulate
# a healthy :3000.
#
# Exit codes:
#   0  all assertions pass
#   1  one or more assertions failed (details on stderr)
#
# A pytest shim (test_deploy_keeper_frontend_health_pyshim.py) wraps this
# so the pytest sweep picks it up.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REDEPLOY="$REPO_ROOT/scripts/services/lib/protea_redeploy.sh"

PASS=0
FAIL=0
FAIL_MSGS=()

note_pass() { PASS=$((PASS + 1)); printf '  ok  %s\n' "$1"; }
note_fail() {
  FAIL=$((FAIL + 1))
  FAIL_MSGS+=("$1")
  printf '  FAIL %s\n' "$1"
}

assert_rc() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    note_pass "$desc"
  else
    note_fail "$desc (expected rc=$expected, got rc=$actual)"
  fi
}

assert_eq() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    note_pass "$desc"
  else
    note_fail "$desc (expected '$expected', got '$actual')"
  fi
}

# --- 0. preflight --------------------------------------------------------
echo "## 0. preflight"
if [[ -f "$REDEPLOY" ]]; then
  note_pass "redeploy script present"
else
  note_fail "redeploy script missing: $REDEPLOY"
  exit 1
fi
if bash -n "$REDEPLOY"; then
  note_pass "bash -n passes"
else
  note_fail "bash -n failed on $REDEPLOY"
  exit 1
fi

# --- 1. synthetic sandbox ------------------------------------------------
echo "## 1. synthetic sandbox"
SANDBOX=$(mktemp -d)
MOCK_PORT=19873

# Mock server state: single server instance for all "healthy" tests.
MOCK_SERVER_PID=""

start_mock_server() {
  if [[ -n "$MOCK_SERVER_PID" ]] && kill -0 "$MOCK_SERVER_PID" 2>/dev/null; then
    return 0  # already running
  fi
  python3 -c "
import http.server, socketserver, os
PORT = int(os.environ.get('MOCK_PORT', '19873'))
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')
class S(socketserver.TCPServer):
    allow_reuse_address = True
with S(('', PORT), H) as s:
    s.serve_forever()
" &
  MOCK_SERVER_PID=$!
  local waited=0
  while ! curl -sf -m 1 -o /dev/null "http://localhost:${MOCK_PORT}" 2>/dev/null; do
    sleep 0.1
    waited=$((waited + 1))
    if (( waited > 30 )); then
      note_fail "mock server did not become reachable in 3s"
      return 1
    fi
  done
  return 0
}

stop_mock_server() {
  if [[ -n "$MOCK_SERVER_PID" ]]; then
    kill "$MOCK_SERVER_PID" 2>/dev/null || true
    wait "$MOCK_SERVER_PID" 2>/dev/null || true
    MOCK_SERVER_PID=""
  fi
}

trap 'rm -rf "$SANDBOX"; stop_mock_server' EXIT

DEPLOY_PATH_T="$SANDBOX/worktrees/protea-deploy"
STATE_DIR="$SANDBOX/state"
LOG_FILE_T="$STATE_DIR/logs/redeploy.log"
FRONTEND_MISS_STATE_T="$STATE_DIR/frontend_miss_count"

mkdir -p "$DEPLOY_PATH_T/logs/pids" "$DEPLOY_PATH_T/apps/web/.next/standalone" \
         "$STATE_DIR/logs"

# Extract function definitions (everything before the top-level code).
LIB_ONLY="$SANDBOX/redeploy_lib_only.sh"
awk 'BEGIN{p=1} /^# 0\) Self-heal the deploy worktree if it has been removed\./{p=0} p' \
  "$REDEPLOY" > "$LIB_ONLY"

for fn in is_frontend_healthy frontend_healthcheck_failed_debounce \
          frontend_healthcheck_reset_debounce recover_frontend ensure_frontend_up; do
  if grep -q "${fn}()" "$LIB_ONLY"; then
    note_pass "lib-only captures $fn()"
  else
    note_fail "lib-only missing $fn()"
    exit 1
  fi
done

# Write a minimal standalone server.js stub for recover_frontend to find.
cat > "$DEPLOY_PATH_T/apps/web/.next/standalone/server.js" <<'STUBEOF'
// stub: exits immediately so recover_frontend returns without blocking
process.exit(0)
STUBEOF

# Source the lib-only block with overrides.
# shellcheck disable=SC1090
AGENT_FARM_ROOT="$SANDBOX" \
PROTEA_DEPLOY_PATH="$DEPLOY_PATH_T" \
PROTEA_REDEPLOY_LOG="$LOG_FILE_T" \
PROTEA_FRONTEND_MISS_STATE="$FRONTEND_MISS_STATE_T" \
PROTEA_FRONTEND_MISS_THRESHOLD=2 \
PROTEA_FRONTEND_URL="http://localhost:${MOCK_PORT}" \
TASK_ID="" \
  source "$LIB_ONLY"

# Re-bind globals consumed by the sourced functions.
# shellcheck disable=SC2034
DEPLOY_PATH="$DEPLOY_PATH_T"
# shellcheck disable=SC2034
FRONTEND_MISS_STATE="$FRONTEND_MISS_STATE_T"
# shellcheck disable=SC2034
FRONTEND_MISS_THRESHOLD=2
# shellcheck disable=SC2034
PROTEA_FRONTEND_URL="http://localhost:${MOCK_PORT}"

PID_FILE="$DEPLOY_PATH_T/logs/pids/frontend.pid"

# --- 2. is_frontend_healthy: nothing listening ---------------------------
echo "## 2. is_frontend_healthy: nothing on :${MOCK_PORT}"
is_frontend_healthy
_rc_probe=$?
if [[ "$_rc_probe" -ne 0 ]]; then
  note_pass "nothing on port -> non-zero rc (got $_rc_probe)"
else
  note_fail "nothing on port -> expected non-zero rc, got 0"
fi

# --- 3. is_frontend_healthy: server listening ----------------------------
echo "## 3. is_frontend_healthy: server listening on :${MOCK_PORT}"
start_mock_server
is_frontend_healthy
assert_rc "mock server up -> rc 0" 0 "$?"

# --- 4. debounce: first miss stays in grace window -----------------------
echo "## 4. debounce: first miss -> grace window (rc 1)"
stop_mock_server
rm -f "$FRONTEND_MISS_STATE_T"
frontend_healthcheck_failed_debounce
assert_rc "first miss -> grace (rc 1)" 1 "$?"
assert_eq "FRONTEND_HC_FAIL_COUNT=1" "1" "$FRONTEND_HC_FAIL_COUNT"
if grep -qP '^1\t[0-9]+$' "$FRONTEND_MISS_STATE_T"; then
  note_pass "state file records count=1"
else
  note_fail "state file unexpected: $(cat "$FRONTEND_MISS_STATE_T" 2>/dev/null)"
fi

# --- 5. debounce: second consecutive miss breaches threshold -------------
echo "## 5. debounce: second miss -> threshold breached (rc 0)"
frontend_healthcheck_failed_debounce
assert_rc "second miss -> breached (rc 0)" 0 "$?"
assert_eq "FRONTEND_HC_FAIL_COUNT=2" "2" "$FRONTEND_HC_FAIL_COUNT"

# --- 6. reset clears counter ---------------------------------------------
echo "## 6. frontend_healthcheck_reset_debounce clears state"
frontend_healthcheck_reset_debounce
if grep -qP '^0\t0$' "$FRONTEND_MISS_STATE_T"; then
  note_pass "reset wrote count=0 ts=0"
else
  note_fail "reset did not clear state: $(cat "$FRONTEND_MISS_STATE_T" 2>/dev/null)"
fi
# Next miss after reset should be back in grace window.
frontend_healthcheck_failed_debounce
assert_rc "first miss after reset -> grace (rc 1)" 1 "$?"
assert_eq "FRONTEND_HC_FAIL_COUNT=1 after reset" "1" "$FRONTEND_HC_FAIL_COUNT"

# --- 7. recover_frontend writes pid file and returns 0 ------------------
echo "## 7. recover_frontend launches process + writes pid"
rm -f "$FRONTEND_MISS_STATE_T" "$PID_FILE"
LOG_FILE="$SANDBOX/recover_test.log"
recover_frontend
RC_REC=$?
assert_rc "recover_frontend returns 0" 0 "$RC_REC"
if [[ -f "$PID_FILE" ]]; then
  note_pass "frontend.pid file created"
  LAUNCHED_PID=$(cat "$PID_FILE")
  if [[ "$LAUNCHED_PID" =~ ^[0-9]+$ ]]; then
    note_pass "frontend.pid contains numeric pid ($LAUNCHED_PID)"
  else
    note_fail "frontend.pid non-numeric: $LAUNCHED_PID"
  fi
else
  note_fail "frontend.pid not created at $PID_FILE"
fi

# --- 8. ensure_frontend_up: healthy frontend resets counter -------------
echo "## 8. ensure_frontend_up: healthy frontend resets counter"
start_mock_server
# Pre-seed a count=1 miss so we confirm reset happens.
printf '1\t%s\n' "$(date +%s)" > "$FRONTEND_MISS_STATE_T"
LOG_FILE="$SANDBOX/egu_healthy.log"
ensure_frontend_up
if grep -qP '^0\t0$' "$FRONTEND_MISS_STATE_T"; then
  note_pass "ensure_frontend_up reset counter when healthy"
else
  note_fail "ensure_frontend_up did not reset; state=$(cat "$FRONTEND_MISS_STATE_T" 2>/dev/null)"
fi

# --- 9. ensure_frontend_up: grace window on first miss ------------------
echo "## 9. ensure_frontend_up: first miss -> grace window, no recovery"
stop_mock_server
rm -f "$FRONTEND_MISS_STATE_T" "$PID_FILE"
LOG_FILE="$SANDBOX/egu_grace.log"
ensure_frontend_up
if grep -q "grace window\|deferring" "$SANDBOX/egu_grace.log" 2>/dev/null; then
  note_pass "ensure_frontend_up logged grace-window deferral"
else
  note_fail "expected grace-window log line; got: $(cat "$SANDBOX/egu_grace.log" 2>/dev/null)"
fi
if [[ ! -f "$PID_FILE" ]]; then
  note_pass "no recovery launched in grace window"
else
  note_fail "recovery launched in grace window (unexpected pid file)"
fi

# --- 10. ensure_frontend_up: second miss -> recovery launched -----------
echo "## 10. ensure_frontend_up: second miss -> recovery launched"
LOG_FILE="$SANDBOX/egu_recover.log"
ensure_frontend_up
if [[ -f "$PID_FILE" ]]; then
  note_pass "recovery launched after threshold breach (pid file written)"
else
  note_fail "pid file not written after threshold breach"
fi
if grep -q "frontend-heal" "$SANDBOX/egu_recover.log" 2>/dev/null; then
  note_pass "ensure_frontend_up logged frontend-heal message"
else
  note_fail "expected frontend-heal log line; got: $(cat "$SANDBOX/egu_recover.log" 2>/dev/null)"
fi

# --- summary -------------------------------------------------------------
echo
echo "================================================================"
printf 'frontend health gate tests: %d passed, %d failed\n' "$PASS" "$FAIL"
if (( FAIL > 0 )); then
  printf 'failures:\n'
  for msg in "${FAIL_MSGS[@]}"; do
    printf '  - %s\n' "$msg"
  done
  exit 1
fi
exit 0

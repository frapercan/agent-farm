#!/usr/bin/env bash
# Ensure the ngrok tunnel for protea.ngrok.app -> :3000 is alive.
# Idempotent: if already running, exit 0; otherwise relaunch detached.
#
# Exit codes:
#   0  tunnel already up (or just relaunched and verified)
#   1  failed to bring tunnel up
set -uo pipefail

AGENT_FARM_ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
LOG_FILE="${PROTEA_NGROK_LOG:-$AGENT_FARM_ROOT/state/logs/protea_ngrok.log}"
PID_FILE="${PROTEA_NGROK_PID:-$AGENT_FARM_ROOT/state/logs/protea_ngrok.pid}"
PUBLIC_URL="${PROTEA_NGROK_URL:-https://protea.ngrok.app}"

mkdir -p "$(dirname "$LOG_FILE")"

ts() { date -Is; }
log() { printf '[%s] %s\n' "$(ts)" "$*" >>"$LOG_FILE"; }

is_alive() {
  curl -sfI -m 5 "$PUBLIC_URL" >/dev/null 2>&1
}

if pgrep -f "ngrok http --domain=protea.ngrok.app" >/dev/null && is_alive; then
  log "alive"
  exit 0
fi

# kill any stale ngrok pointing at our domain before relaunching
pkill -f "ngrok http --domain=protea.ngrok.app" 2>/dev/null || true
sleep 1

log "launching tunnel"
nohup ngrok http --domain=protea.ngrok.app --log=stdout 3000 \
  >>"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"

# wait up to 15s for it to come up
for _ in $(seq 1 15); do
  if is_alive; then
    log "OK pid=$(cat "$PID_FILE")"
    exit 0
  fi
  sleep 1
done

log "ERR tunnel did not come up"
exit 1

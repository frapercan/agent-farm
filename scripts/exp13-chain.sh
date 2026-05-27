#!/usr/bin/env bash
# Autonomous chain to complete the 6 remaining EXP.13 cells (v226-lineage, range v226->v230).
# Dispatches cells one at a time on protea.training and waits for each to settle SUCCEEDED before
# launching the next. On FAILED/CANCELLED it logs and stops (so user can intervene).
#
# Spawned manually 2026-05-27 to run unattended while the user travels.

set -uo pipefail

cd /home/frapercan/Thesis2/worktrees/protea-deploy
set -a
# shellcheck source=/dev/null
source .env
set +a

LOG=/home/frapercan/Thesis2/exp13-chain.log
exec >>"$LOG" 2>&1

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
# log() writes to stderr so it bypasses any $() command substitution that
# captures stdout. Both 1 and 2 are already redirected to $LOG by the
# top-level `exec` above, so the line lands in the log either way.
log() { echo "[$(ts)] $*" >&2; }

log "=== EXP.13 chain started ==="

# Long-lived JWT (24h) so a single token spans the whole run.
TOKEN=$(poetry run python -c "
import jwt, time, os
print(jwt.encode({
    'sub': 'conductor-exp13-trip-autonomous',
    'iat': int(time.time()),
    'exp': int(time.time()) + 24*3600,
    'role': 'admin',
}, os.environ['PROTEA_JWT_SECRET'], algorithm='HS256'))
")
log "minted JWT len=${#TOKEN}"

# (cell_name | k | embedding_config_id | preexisting_job_id_if_in_flight)
# train_versions and the rest are identical across the v226-lineage grid;
# they live inside dispatch_cell().
CELLS=(
  "bench-v1-K3-v226-lineage-ankh_large|3|238f79b1-3068-4c6f-9013-5cc52b4f662b|61ff109d-c9cd-4c08-b92a-f9f3336e2aaf"
  "bench-v1-K3-v226-lineage-esm2_650m|3|c2e9dda3-e505-4170-b50d-435a451761ac|"
  "bench-v1-K3-v226-lineage-esmc_600m|3|2bf1e753-022f-44b8-a131-9a90acb4024e|"
  "bench-v1-K3-v226-lineage-prostt5|3|c0ae5b69-d6dc-41cf-a711-1739d3d2e170|"
  "bench-v1-K5-v226-lineage-ankh_base|5|08234f06-ba76-4d7d-aaec-ae601096b4fa|"
  "bench-v1-K5-v226-lineage-esmc_600m|5|2bf1e753-022f-44b8-a131-9a90acb4024e|"
)

dispatch_cell() {
  local name=$1 k=$2 emb_id=$3
  curl -sS -m 30 -X POST http://localhost:8000/v1/datasets \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d "{
      \"k\": $k,
      \"output_name\": \"$name\",
      \"test_versions\": [230],
      \"search_backend\": \"torch\",
      \"train_versions\": [160, 165, 170, 175, 180, 185, 190, 195, 200, 205, 211, 215, 220, 226],
      \"compute_taxonomy\": true,
      \"annotation_source\": \"goa\",
      \"use_embedding_pca\": true,
      \"compute_alignments\": true,
      \"embedding_config_id\": \"$emb_id\",
      \"ontology_snapshot_id\": \"35c3ad67-3002-47db-8f71-eeed69d22ad6\",
      \"expand_votes_to_ancestors\": true
    }" 2>&1 | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('job_id', ''))
except Exception as e:
    print('', file=sys.stderr)
    print(f'dispatch_cell parse_error: {e}', file=sys.stderr)
"
}

wait_for_job() {
  local jid=$1
  local last_state=""
  while true; do
    local s
    s=$(docker exec protea-postgres-1 psql -U protea -d protea -tA -c "SELECT status FROM job WHERE id='$jid';" 2>/dev/null || true)
    if [ -n "$s" ] && [ "$s" != "RUNNING" ] && [ "$s" != "QUEUED" ]; then
      log "job $jid terminal status=$s"
      echo "$s"
      return 0
    fi
    if [ "$s" != "$last_state" ]; then
      log "job $jid status=$s"
      last_state=$s
    fi
    sleep 180
  done
}

cleanup_temp_for_job() {
  local jid=$1
  # Best-effort delete of the temp/coordinator/<jid>/* tree in MinIO (kept by the
  # write stage for traceability; we drop it post-success to free disk).
  log "cleanup temp/$jid/* (best-effort)"
  docker exec protea-minio-1 mc rb --force "local/protea/temp/coordinator/$jid" 2>/dev/null || true
}

for CELL in "${CELLS[@]}"; do
  IFS='|' read -r name k emb_id pre_jid <<< "$CELL"

  # Idempotent skip: if a Dataset row already exists with this output_name,
  # treat as done (re-launching the chain after a partial run should not
  # re-dispatch finished cells).
  if docker exec protea-postgres-1 psql -U protea -d protea -tA \
       -c "SELECT 1 FROM dataset WHERE name='$name' LIMIT 1;" 2>/dev/null | grep -q 1; then
    log "cell $name already has a Dataset row; skipping"
    continue
  fi

  if [ -n "$pre_jid" ]; then
    JID=$pre_jid
    log "cell $name already dispatched as $JID"
  else
    log "dispatching cell $name k=$k emb=$emb_id"
    JID=$(dispatch_cell "$name" "$k" "$emb_id")
    if [ -z "$JID" ]; then
      log "ERROR dispatch failed for $name; stopping chain"
      exit 1
    fi
    log "cell $name dispatched as $JID"
  fi

  RESULT=$(wait_for_job "$JID")
  if [ "$RESULT" != "SUCCEEDED" ]; then
    log "STOP cell $name ended $RESULT (expected SUCCEEDED); user intervention required"
    exit 2
  fi
  log "cell $name SUCCEEDED"

  cleanup_temp_for_job "$JID"
  log "--- moving to next cell ---"
done

log "=== EXP.13 chain complete: all 6 cells SUCCEEDED ==="
log "Next: Phase 2 (run_cafa_evaluation across 24 datasets * 9 stages)"

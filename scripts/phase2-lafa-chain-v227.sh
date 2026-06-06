#!/usr/bin/env bash
# Phase 2 LAFA-band re-scoring chain, v227-aligned (goa:227 -> goa:230).
#
# Post-recovery re-run on the LAFA-aligned eval window. The reference
# annotation pool (t0) is goa@227 and the eval_set scores against the
# LAFA tiers (NK=399 / LK=868 / PK=6340) over a 7401-target query_set.
# The older 3b6f8064 band (goa:226 -> goa:230, query_set 045ab275) is
# retained as the broader-window supplementary, not superseded here.
#
# For each of the 24 canonical (PLM x K) cells (8 ADR-D35 PLMs x K{3,5,10}):
#  1. Skip predict if a canonical prediction_set on the LAFA query_set
#     (30ec3795, 7401 targets) already exists for this cell signature.
#  2. Otherwise dispatch predict_go_terms with search_backend=numpy
#     (torch backend OOMs on the large KNN corpus; 7401 queries is fine
#     on numpy).
#  3. Wait until SUCCEEDED. Resolve the prediction_set_id by filtering on
#     cell signature + job-window.
#  4. For each of the 7 canonical scoring_configs (embedding_only,
#     embedding_plus_vote, vote_fraction, alignment_only,
#     embedding_plus_alignment, evidence_veto, composite), dispatch
#     run_cafa_evaluation against eval_set dd9f16ed. Each call writes
#     one evaluation_result with the corresponding scoring_config_id.
#  5. Skip any (pred_set, scoring_config) pair that already has a
#     baseline (reranker_model_id IS NULL) result.
#
# Runs unattended; on any FAILED/CANCELLED leaves the chain and surfaces.

set -uo pipefail

cd /home/frapercan/Thesis2/worktrees/protea-deploy
set -a
# shellcheck source=/dev/null
source .env
# .env.local is sourced LAST and wins, mirroring scripts/manage.sh::_source_env.
# It carries the PROTEA_JWT_SECRET the API actually verifies with; sourcing
# only .env mints tokens the API rejects with "Signature verification failed".
# shellcheck source=/dev/null
[ -f .env.local ] && source .env.local
set +a

LOG=/home/frapercan/Thesis2/phase2-lafa-v227.log
exec >>"$LOG" 2>&1

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "[$(ts)] $*" >&2; }

log "=== Phase 2 LAFA v227 chain started (numpy backend, 7 scoring_configs) ==="

TOKEN=$(poetry run python -c "
import jwt, time, os
print(jwt.encode({
    'sub': 'conductor-phase2-lafa-v227',
    'iat': int(time.time()),
    'exp': int(time.time()) + 72*3600,
    'role': 'admin',
}, os.environ['PROTEA_JWT_SECRET'], algorithm='HS256'))
")
log "minted JWT len=${#TOKEN}"

# Canonical IDs shared across every cell (v227-aligned LAFA band).
QUERY_SET=30ec3795-6d82-4df7-97ba-7dc2dcb6b247          # LAFA targets v227->v230 (7401)
ANN_SET=c905dffa-a5ce-430b-b17b-503e88666adb            # v227 train pool (goa@227, t0)
ONT=35c3ad67-3002-47db-8f71-eeed69d22ad6                 # GO snapshot
EVAL_SET=dd9f16ed-6f4c-40de-a7fb-78676b01368d            # goa:227 -> goa:230 (LAFA tiers)
# v227 LAFA IA (the table the deployed LAFA scored against; 39906 terms).
# Passed as eval payload ia_file so f_micro_w is LAFA-comparable. WITHOUT
# this the eval falls back to snapshot 35c3ad67 ia_url = IA_cafa6.tsv
# (generic CAFA6 corpus) and the weighted F does NOT match LAFA.
# Authoritative per PROTEA PR#598 (docs/IA_PROVENANCE_v227.md).
IA_FILE=/home/frapercan/Thesis2/protea-lafa-knn/lafa_t0_Sep_2025/IA.tsv

# 7 canonical scoring_configs (excludes "IEA up" which has 0 historical usage).
SCORING_CONFIGS=(
  "01446858-c56f-4204-8b5d-cec90e16bbde|embedding_only"
  "1ad536db-9aa3-4eec-ba40-99ae281121b5|embedding_plus_vote"
  "19b30773-d4d4-4a40-ba9d-da9f77382af4|vote_fraction"
  "dc8aa37d-a316-41eb-a9c0-9cb4151a2870|alignment_only"
  "fb738ec4-e0e0-4b03-9c8f-75bf5feddd60|embedding_plus_alignment"
  "04c55eb3-c77b-4e98-88b9-1e7c21fe0353|evidence_veto"
  "bae5ece3-e641-41da-a52e-07458eebd689|composite"
)

# (k|embedding_config_id|plm_label)  24 canonical (ADR D35) cells:
# 8 canonical PLMs x K{3,5,10}. Orphan PLMs (esmc_300m, ankh_base_v2,
# prot_t5_full) are deliberately excluded from the v227 LAFA grid.
CELLS=(
  "3|08234f06-ba76-4d7d-aaec-ae601096b4fa|ankh_base"
  "3|238f79b1-3068-4c6f-9013-5cc52b4f662b|ankh_large"
  "3|2bf1e753-022f-44b8-a131-9a90acb4024e|esmc_600m"
  "3|500a0c59-be09-424d-9d51-b7997629c95a|esm2_150m"
  "3|c2e9dda3-e505-4170-b50d-435a451761ac|esm2_650m"
  "3|55e43f1c-1a3b-4b1d-88c0-26b433f5f673|esm2_3b"
  "3|c0ae5b69-d6dc-41cf-a711-1739d3d2e170|prostt5"
  "3|084943c6-fec1-441d-bdc5-63b0268ada1b|prot_t5"
  "5|08234f06-ba76-4d7d-aaec-ae601096b4fa|ankh_base"
  "5|238f79b1-3068-4c6f-9013-5cc52b4f662b|ankh_large"
  "5|2bf1e753-022f-44b8-a131-9a90acb4024e|esmc_600m"
  "5|500a0c59-be09-424d-9d51-b7997629c95a|esm2_150m"
  "5|c2e9dda3-e505-4170-b50d-435a451761ac|esm2_650m"
  "5|55e43f1c-1a3b-4b1d-88c0-26b433f5f673|esm2_3b"
  "5|c0ae5b69-d6dc-41cf-a711-1739d3d2e170|prostt5"
  "5|084943c6-fec1-441d-bdc5-63b0268ada1b|prot_t5"
  "10|08234f06-ba76-4d7d-aaec-ae601096b4fa|ankh_base"
  "10|238f79b1-3068-4c6f-9013-5cc52b4f662b|ankh_large"
  "10|2bf1e753-022f-44b8-a131-9a90acb4024e|esmc_600m"
  "10|500a0c59-be09-424d-9d51-b7997629c95a|esm2_150m"
  "10|c2e9dda3-e505-4170-b50d-435a451761ac|esm2_650m"
  "10|55e43f1c-1a3b-4b1d-88c0-26b433f5f673|esm2_3b"
  "10|c0ae5b69-d6dc-41cf-a711-1739d3d2e170|prostt5"
  "10|084943c6-fec1-441d-bdc5-63b0268ada1b|prot_t5"
)

psql_one() {
  docker exec protea-postgres-1 psql -U protea -d protea -tA -c "$1" 2>/dev/null
}

dispatch_predict() {
  local k=$1 ec=$2
  curl -sS -m 30 -X POST http://localhost:8000/v1/embeddings/predict \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d "{
      \"query_set_id\": \"$QUERY_SET\",
      \"search_backend\": \"numpy\",
      \"compute_taxonomy\": true,
      \"annotation_set_id\": \"$ANN_SET\",
      \"compute_alignments\": true,
      \"embedding_config_id\": \"$ec\",
      \"aspect_separated_knn\": true,
      \"ontology_snapshot_id\": \"$ONT\",
      \"compute_reranker_features\": true,
      \"limit_per_entry\": $k
    }" 2>&1 | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('id', ''))
except Exception as e:
    print('', file=sys.stderr)
    print(f'dispatch_predict parse_error: {e}', file=sys.stderr)
"
}

dispatch_eval() {
  local pred_id=$1 sc_id=$2
  curl -sS -m 30 -X POST "http://localhost:8000/v1/annotations/evaluation-sets/$EVAL_SET/run" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d "{
      \"prediction_set_id\": \"$pred_id\",
      \"scoring_config_id\": \"$sc_id\",
      \"ia_file\": \"$IA_FILE\"
    }" 2>&1 | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('id', ''))
except Exception as e:
    print('', file=sys.stderr)
    print(f'dispatch_eval parse_error: {e}', file=sys.stderr)
"
}

wait_for_job() {
  local jid=$1 sleep_s=${2:-180}
  local last=""
  while true; do
    local s
    s=$(psql_one "SELECT status FROM job WHERE id='$jid';")
    if [ -n "$s" ] && [ "$s" != "RUNNING" ] && [ "$s" != "QUEUED" ]; then
      log "job $jid terminal status=$s"
      echo "$s"
      return 0
    fi
    if [ "$s" != "$last" ]; then
      log "job $jid status=$s"
      last=$s
    fi
    sleep "$sleep_s"
  done
}

# Workaround for the predict_go_terms coord that never claims the job:
# RMQ re-delivers the message every 3 min and each delivery creates a
# duplicate pred_set. Wait for the go_prediction count on the newest
# matching pred_set to STABILIZE (no growth for 2 consecutive 60s polls
# after reaching a floor of 100k), then purge RMQ, drop duplicate
# pred_sets in this job's window, and force-finalize.
#
# Stability-based (K-agnostic): tolerates K=3 (~smaller) and K=10
# (~larger) prediction volumes without a fixed threshold.
wait_for_predict_with_recovery() {
  local jid=$1 k=$2 ec=$3 plm=$4 sleep_s=${5:-60}
  local start_at min_floor=100000 max_seconds=3600
  start_at=$(psql_one "SELECT created_at FROM job WHERE id='$jid';")
  local elapsed=0 prev_count=-1 stable_polls=0
  while [ "$elapsed" -lt "$max_seconds" ]; do
    local s
    s=$(psql_one "SELECT status FROM job WHERE id='$jid';")
    if [ -n "$s" ] && [ "$s" != "RUNNING" ] && [ "$s" != "QUEUED" ]; then
      log "job $jid terminal status=$s (natural)"
      echo "$s"
      return 0
    fi
    local newest_pred
    newest_pred=$(psql_one "
      SELECT id FROM prediction_set
      WHERE embedding_config_id='$ec' AND annotation_set_id='$ANN_SET'
        AND ontology_snapshot_id='$ONT' AND limit_per_entry=$k
        AND query_set_id='$QUERY_SET'
        AND created_at >= '$start_at'::timestamptz
      ORDER BY created_at DESC LIMIT 1;")
    if [ -n "$newest_pred" ]; then
      local count
      count=$(psql_one "SELECT COUNT(*) FROM go_prediction WHERE prediction_set_id='$newest_pred';")
      if [ "$count" -ge "$min_floor" ] && [ "$count" -eq "$prev_count" ]; then
        stable_polls=$((stable_polls + 1))
      else
        stable_polls=0
      fi
      log "predict $jid K=$k $plm: $count preds (stable_polls=$stable_polls)"
      if [ "$stable_polls" -ge 2 ]; then
        log "STUCK-RECOVERY K=$k $plm: $count predictions stable, force-finalizing job $jid"
        docker exec protea-rabbitmq-1 rabbitmqctl purge_queue protea.predictions >/dev/null 2>&1 || true
        psql_one "
          DELETE FROM prediction_set
          WHERE embedding_config_id='$ec' AND annotation_set_id='$ANN_SET'
            AND ontology_snapshot_id='$ONT' AND limit_per_entry=$k
            AND query_set_id='$QUERY_SET'
            AND created_at >= '$start_at'::timestamptz
            AND id != '$newest_pred';" >/dev/null
        psql_one "
          UPDATE job SET status='SUCCEEDED',
            started_at=COALESCE(started_at, '$start_at'::timestamptz),
            finished_at=NOW()
          WHERE id='$jid';" >/dev/null
        log "job $jid terminal status=SUCCEEDED (recovered, $count preds)"
        echo "SUCCEEDED"
        return 0
      fi
      prev_count=$count
    fi
    sleep "$sleep_s"
    elapsed=$((elapsed + sleep_s))
  done
  log "ERROR predict $jid timeout after ${max_seconds}s"
  echo "TIMEOUT"
  return 1
}

find_or_dispatch_predict() {
  local k=$1 ec=$2 plm=$3
  local existing
  existing=$(psql_one "
    SELECT id FROM prediction_set
    WHERE embedding_config_id='$ec'
      AND annotation_set_id='$ANN_SET'
      AND ontology_snapshot_id='$ONT'
      AND limit_per_entry=$k
      AND query_set_id='$QUERY_SET'
    ORDER BY created_at DESC
    LIMIT 1;")
  if [ -n "$existing" ]; then
    log "cell K=$k $plm: reusing existing prediction_set $existing"
    echo "$existing"
    return 0
  fi

  log "cell K=$k $plm: dispatching predict_go_terms (numpy)"
  local jid
  jid=$(dispatch_predict "$k" "$ec")
  if [ -z "$jid" ]; then
    log "ERROR predict dispatch failed for K=$k $plm"
    return 1
  fi
  log "cell K=$k $plm: predict job $jid"

  local start_at
  start_at=$(psql_one "SELECT created_at FROM job WHERE id='$jid';")

  local res
  res=$(wait_for_predict_with_recovery "$jid" "$k" "$ec" "$plm" 60)
  if [ "$res" != "SUCCEEDED" ]; then
    log "ERROR predict for K=$k $plm ended $res"
    return 1
  fi

  local pred_id
  pred_id=$(psql_one "
    SELECT id FROM prediction_set
    WHERE embedding_config_id='$ec'
      AND annotation_set_id='$ANN_SET'
      AND ontology_snapshot_id='$ONT'
      AND limit_per_entry=$k
      AND query_set_id='$QUERY_SET'
      AND created_at >= '$start_at'::timestamptz
    ORDER BY created_at DESC
    LIMIT 1;")
  if [ -z "$pred_id" ]; then
    log "ERROR could not resolve prediction_set for K=$k $plm"
    return 1
  fi
  log "cell K=$k $plm: prediction_set $pred_id"
  echo "$pred_id"
}

run_all_scorings_for_cell() {
  local k=$1 plm=$2 pred_id=$3
  for SC in "${SCORING_CONFIGS[@]}"; do
    IFS='|' read -r sc_id sc_name <<< "$SC"

    # Skip if baseline (no reranker) eval_result already exists for this combo.
    local existing
    existing=$(psql_one "
      SELECT id FROM evaluation_result
      WHERE prediction_set_id='$pred_id'
        AND evaluation_set_id='$EVAL_SET'
        AND scoring_config_id='$sc_id'
        AND reranker_model_id IS NULL
      LIMIT 1;")
    if [ -n "$existing" ]; then
      log "  K=$k $plm/$sc_name: existing eval $existing; skipping"
      continue
    fi

    log "  K=$k $plm/$sc_name: dispatching run_cafa_evaluation"
    local jid
    jid=$(dispatch_eval "$pred_id" "$sc_id")
    if [ -z "$jid" ]; then
      log "  ERROR eval dispatch failed for K=$k $plm/$sc_name"
      return 1
    fi

    local res
    res=$(wait_for_job "$jid" 30)
    if [ "$res" != "SUCCEEDED" ]; then
      log "  ERROR eval for K=$k $plm/$sc_name ended $res"
      return 1
    fi
    log "  K=$k $plm/$sc_name: SUCCEEDED"
  done
  return 0
}

for CELL in "${CELLS[@]}"; do
  IFS='|' read -r k ec plm <<< "$CELL"
  log "--- cell K=$k $plm ec=$ec ---"

  PRED_ID=$(find_or_dispatch_predict "$k" "$ec" "$plm")
  if [ -z "$PRED_ID" ]; then
    log "STOP: predict resolution failed for K=$k $plm"
    exit 2
  fi

  if ! run_all_scorings_for_cell "$k" "$plm" "$PRED_ID"; then
    log "STOP: scoring fan-out failed for K=$k $plm"
    exit 2
  fi
done

log "=== Phase 2 LAFA v227 chain complete: 24 cells x 7 scoring_configs scored on 227->230 ==="

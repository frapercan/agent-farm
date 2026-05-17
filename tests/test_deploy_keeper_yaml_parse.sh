#!/usr/bin/env bash
# tests/test_deploy_keeper_yaml_parse.sh -- FARM-2.5
#
# Covers scripts/lib/yaml_parse.sh in isolation:
#   - parse_yaml_field: nested key lookup, missing key, top-level key,
#     comments, quoted values
#   - parse_duration: integers, Xs / Xm / Xh, garbage rejection
#   - parse_yaml_duration: end-to-end + fallback to default
#
# Pure bash so it runs without pytest. Discovered by the bash test
# sweep (run-tests.sh) and is safe to invoke standalone:
#   bash tests/test_deploy_keeper_yaml_parse.sh
#
# Exit code 0 on full pass; non-zero on any failure (details on stderr).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LIB="$REPO_ROOT/scripts/lib/yaml_parse.sh"

# shellcheck source=../scripts/lib/yaml_parse.sh
source "$LIB"

PASS=0
FAIL=0
FAIL_MSGS=()

assert_eq() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    PASS=$((PASS + 1))
    printf '  ok  %s\n' "$desc"
  else
    FAIL=$((FAIL + 1))
    FAIL_MSGS+=("$desc: expected=$expected actual=$actual")
    printf '  FAIL %s (expected=%q actual=%q)\n' "$desc" "$expected" "$actual" >&2
  fi
}

assert_rc() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    PASS=$((PASS + 1))
    printf '  ok  %s\n' "$desc"
  else
    FAIL=$((FAIL + 1))
    FAIL_MSGS+=("$desc: expected rc=$expected, got $actual")
    printf '  FAIL %s (expected rc=%s, got %s)\n' "$desc" "$expected" "$actual" >&2
  fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Fixture 1: simple service yaml shaped like deploy-keeper.yaml
cat > "$TMP/simple.yaml" <<'EOF'
name: example-agent
kind: headless
service:
  poll_interval: 60s
  triggers:
    - new_commit_on:origin/develop
cost_budget:
  expected_tokens: 0
EOF

# Fixture 2: poll_interval shaped as bare minutes
cat > "$TMP/minutes.yaml" <<'EOF'
service:
  poll_interval: 5m
EOF

# Fixture 3: bare-integer poll
cat > "$TMP/integer.yaml" <<'EOF'
service:
  poll_interval: 90
EOF

# Fixture 4: quoted value + comment after
cat > "$TMP/quoted.yaml" <<'EOF'
service:
  poll_interval: "30s"   # comment after value
EOF

# Fixture 5: missing key
cat > "$TMP/empty.yaml" <<'EOF'
name: nobody
service:
  triggers: []
EOF

# Fixture 6: hours
cat > "$TMP/hours.yaml" <<'EOF'
service:
  poll_interval: 2h
EOF

echo "== parse_yaml_field =="

v="$(parse_yaml_field "$TMP/simple.yaml" service.poll_interval)"
assert_eq "nested key (simple.yaml service.poll_interval)" "60s" "$v"

v="$(parse_yaml_field "$TMP/simple.yaml" name)"
assert_eq "top-level key (simple.yaml name)" "example-agent" "$v"

v="$(parse_yaml_field "$TMP/quoted.yaml" service.poll_interval)"
assert_eq "quoted+comment (quoted.yaml service.poll_interval)" "30s" "$v"

parse_yaml_field "$TMP/empty.yaml" service.poll_interval >/dev/null
assert_rc "missing key rc=1" 1 $?

parse_yaml_field "$TMP/does-not-exist.yaml" service.poll_interval >/dev/null
assert_rc "missing file rc=2" 2 $?

echo "== parse_duration =="

assert_eq "5m -> 300" "300" "$(parse_duration 5m)"
assert_eq "30s -> 30" "30" "$(parse_duration 30s)"
assert_eq "1h -> 3600" "3600" "$(parse_duration 1h)"
assert_eq "bare integer 300 -> 300" "300" "$(parse_duration 300)"
assert_eq "bare integer 90 -> 90" "90" "$(parse_duration 90)"

parse_duration bogus >/dev/null
assert_rc "garbage rc=1" 1 $?

parse_duration "" >/dev/null
assert_rc "empty rc=1" 1 $?

parse_duration "5x" >/dev/null
assert_rc "unknown suffix rc=1" 1 $?

echo "== parse_yaml_duration =="

# Acceptance test from the slice: poll_interval: 60s -> 60
out=$(parse_yaml_duration "$TMP/simple.yaml" service.poll_interval 300)
rc=$?
assert_eq "60s yaml -> 60" "60" "$out"
assert_rc "60s yaml rc=0 (no fallback)" 0 "$rc"

out=$(parse_yaml_duration "$TMP/minutes.yaml" service.poll_interval 300)
rc=$?
assert_eq "5m yaml -> 300" "300" "$out"
assert_rc "5m yaml rc=0 (no fallback)" 0 "$rc"

out=$(parse_yaml_duration "$TMP/integer.yaml" service.poll_interval 300)
assert_eq "bare integer yaml -> 90" "90" "$out"

out=$(parse_yaml_duration "$TMP/hours.yaml" service.poll_interval 300)
assert_eq "2h yaml -> 7200" "7200" "$out"

out=$(parse_yaml_duration "$TMP/empty.yaml" service.poll_interval 300)
rc=$?
assert_eq "missing key -> default 300" "300" "$out"
assert_rc "missing key fallback rc=1" 1 "$rc"

# Real fixture: agents/deploy-keeper.yaml at HEAD
out=$(parse_yaml_duration "$REPO_ROOT/agents/deploy-keeper.yaml" service.poll_interval 300)
rc=$?
assert_eq "deploy-keeper.yaml -> 300 (5m)" "300" "$out"
assert_rc "deploy-keeper.yaml parse rc=0" 0 "$rc"

# Summary
printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  for m in "${FAIL_MSGS[@]}"; do
    printf '  - %s\n' "$m" >&2
  done
  exit 1
fi
exit 0

---
name: deploy-keeper-bootstrap-debounce
section: "6-services"
state: working
owner: agent-farm conductor loop
source:
  - scripts/services/lib/protea_redeploy.sh
related: docs/features/deploy-keeper-tick.md
---

# deploy-keeper bootstrap debounce (FARM-DK-HC-DEBOUNCE)

Prevents a single transient `/jobs` 5xx from triggering a full venv
wipe and bootstrap cascade inside `protea_redeploy.sh`.

## Problem (2026-05-24 incident)

A healthcheck blip during a prewarm or worker reap set `BOOTSTRAP=1`
immediately. The venv wipe caused a multi-minute outage during which
every subsequent tick also saw a non-200 response, so bootstrap looped
until the operator manually killed the supervisor.

A secondary bug: when `LOCAL==REMOTE` and `BOOTSTRAP` was the only
trigger, `git diff --name-only` produced an empty string, but
`echo "$CHANGED" | wc -l` returned `1` (echo emits a newline). This
logged `files=1` for every spurious redeploy, masking the real cause.

## Fix

### API healthcheck debounce

Three env-configurable knobs in `protea_redeploy.sh`:

| Variable | Default | Meaning |
|---|---|---|
| `PROTEA_API_FAIL_THRESHOLD` | `3` | Consecutive failures before BOOTSTRAP |
| `PROTEA_API_FAIL_WINDOW_SEC` | `90` | Window in seconds; counter resets if elapsed |
| `PROTEA_API_FAIL_STATE` | `$AGENT_FARM_ROOT/state/deploy_keeper_api_fail_count` | Persistent counter file |

A single 5xx logs `"deferring BOOTSTRAP (tick N/3)"` and exits cleanly.
The third consecutive failure within the window logs the response body
and current uvicorn importability before setting `BOOTSTRAP=1`.

On a successful healthcheck, `api_healthcheck_reset_debounce` clears
the counter so transient blips do not accumulate across unrelated ticks.

### files=0 noise fix

Replaced `echo "$CHANGED" | wc -l` with:

```bash
FILES_COUNT=0
[[ -n "$CHANGED" ]] && FILES_COUNT=$(printf '%s\n' "$CHANGED" | grep -c .)
```

An empty `CHANGED` (SHA-unchanged redeploy driven only by BOOTSTRAP or
siblings) now correctly logs `files=0`.

### Bootstrap diagnostics

Before the heavy `deploy.sh` call the script now logs:
- The number of consecutive failures that triggered the decision
- Whether `uvicorn` is importable inside the existing venv
- The first 200 bytes of the last healthcheck response body

## Tests

`tests/test_deploy_keeper_bootstrap_debounce.py` (9 pytest cases):

- Single 5xx stays in grace window (does not bootstrap)
- Two consecutive 5xx stay in grace window
- Third consecutive 5xx within window boots BOOTSTRAP=1
- `api_healthcheck_reset_debounce` clears counter; next single failure is grace
- Expired window resets counter (count=2 but ts > window_sec -> restarts at 1)
- Empty CHANGED produces files=0
- Single-file CHANGED produces files=1
- Multi-file CHANGED counts correctly
- Old `echo | wc -l` approach produces 1 for empty (regression doc)

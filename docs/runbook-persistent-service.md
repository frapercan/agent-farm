# Runbook: add a new persistent service

A persistent service is a headless agent that loops forever instead of
running once and exiting. `deploy-keeper` is the production example: it
keeps `protea.ngrok.app` serving HEAD of `origin/develop`. The loop
itself is pure bash and never spawns an LLM on the happy path; only when
a quick-retry ladder is exhausted does it escalate to a janitor subagent.

Before FARM-FEAT.6 the only way to add a second persistent service was
to copy `deploy-keeper-supervisor.sh` wholesale. The shared loop now
lives in `scripts/services/_supervisor-template.sh`, so a new service is
a thin wrapper that sets five parameters and sources the template.

A complete worked example ships under `examples/queue-watcher/`.

## What the template gives you

`scripts/services/_supervisor-template.sh` owns:

1. The forever loop: run a tick, sleep `POLL_INTERVAL`, repeat.
2. The quick-retry ladder: on a failed tick it retries on a backoff
   schedule (default `30s, 120s, 300s`, one rung per
   `MAX_CONSECUTIVE_FAILURES`) before giving up.
3. Escalation: once the ladder is exhausted (and the failure is not a
   `prereq_fail`) it spawns a janitor subagent, then sleeps
   `PAUSE_AFTER_PAUSE_SEC` as a cool-off.
4. The `prereq_fail` carve-out: a daemon-level failure (docker down, no
   network) is logged and retried but never escalated, because the
   operator is the recovery path for those.
5. Clean shutdown on `SIGINT` / `SIGTERM` (marks the task ended).
6. Test seams: `TICK_CMD_OVERRIDE` and `SUPERVISOR_NAP_CMD` let a test
   inject a scripted tick and a virtual clock so the loop runs in
   milliseconds. `QUICK_RETRY_LADDER_OVERRIDE` shortens the ladder.

## The five parameters

Set these in your wrapper before sourcing the template:

| Variable | Meaning |
|---|---|
| `TICK_SCRIPT` | absolute path of the per-tick script to run |
| `POLL_INTERVAL` | seconds between successful ticks |
| `MAX_CONSECUTIVE_FAILURES` | number of quick-retry rungs before escalate |
| `PAUSE_AFTER_PAUSE_SEC` | cool-off pause (seconds) after the ladder is exhausted |
| `FAIL_KIND_ENV_FILE` | path of the `K=V` file your tick writes on failure |

The wrapper must also set `TASK_ID` and `ROOT` (or `AGENT_FARM_ROOT`)
and source `scripts/lib/common.sh` (for `heartbeat` and
`task_set_ended`) before sourcing the template.

## The tick contract

The template treats your tick as a black box:

- exit `0` means success. The supervisor sleeps until the next poll.
- a non-zero exit means failure. The supervisor reads `FAIL_KIND` and
  `FAIL_EXIT` from `FAIL_KIND_ENV_FILE`, so your tick MUST write that
  file before exiting non-zero. A `FAIL_KIND` of `prereq_fail` tells
  the supervisor to retry but not escalate.

## Optional hooks

Define either function before sourcing the template to override the
default:

- `service_escalate <fail_kind>`: what to do once the ladder is
  exhausted. Default spawns a generic `service-rescue` janitor.
  deploy-keeper overrides this to spawn its `deploy-keeper-rescue`
  janitor.
- `service_nap_between_ticks <seconds>`: the inter-tick wait. Default is
  a plain sleep. deploy-keeper overrides this with a trigger-aware nap
  so a new commit, a dead ngrok tunnel, or a manual marker file can
  short-circuit the poll interval and force an early tick. Return `0`
  from the hook to force an early tick.

## Minimal wrapper (no hooks)

This is the whole `examples/queue-watcher/queue-watcher-supervisor.sh`
in spirit:

```bash
set -uo pipefail
ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"
TASK_ID="${TASK_ID:?TASK_ID env required}"
source "$ROOT/scripts/lib/common.sh"
source "$ROOT/scripts/lib/yaml_parse.sh"

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLL_INTERVAL_SEC=$(parse_yaml_duration "$SELF_DIR/queue-watcher.yaml" service.poll_interval 120)

TICK_SCRIPT="$SELF_DIR/queue-watcher-tick.sh"
POLL_INTERVAL="$POLL_INTERVAL_SEC"
MAX_CONSECUTIVE_FAILURES=3
PAUSE_AFTER_PAUSE_SEC=900
FAIL_KIND_ENV_FILE="/tmp/queue-watcher-last-fail.env"

source "$ROOT/scripts/services/_supervisor-template.sh"
```

## Step-by-step

1. Create `examples/<service>/` or, for a production service,
   `scripts/services/<service>-*.sh`.
2. Write `<service>-tick.sh` honouring the tick contract above.
3. Write `<service>-supervisor.sh`: read config, set the five
   parameters, define any hooks, source the template.
4. Add a `<service>.yaml` under `agents/` (production) with
   `persistent: true` and a `service.poll_interval`. The example keeps
   its yaml next to the scripts.
5. Add a test under `tests/` modelled on
   `tests/test_deploy_keeper_backoff.sh`: stub the tick (scripted
   fail then ok), stub the nap with a virtual clock, assert the ladder
   recovers without escalating, then assert the long-outage path does
   escalate.
6. Validate locally with `bash -n` on both scripts and a dry tick:
   ```bash
   bash -n scripts/services/<service>-supervisor.sh
   TASK_ID=dry SUPERVISOR_NAP_CMD='true' <service>_TICK_CMD='exit 0' \
     timeout 5 bash scripts/services/<service>-supervisor.sh
   ```
7. Wire the spawn path the same way deploy-keeper is wired (see
   `agents/deploy-keeper.yaml` and `scripts/spawn.sh`).

## Notes

- The `_` prefix on `_supervisor-template.sh` marks it as not directly
  runnable. Sourcing it starts the loop; set `SUPERVISOR_DEFER_MAIN=1`
  before sourcing if you need to do work after the parameters are
  resolved but before the loop starts, then call `supervisor_main`.
- Persistent services should use a stable worktree (`cleanup: none`)
  rather than an ephemeral one, so caches survive restarts.

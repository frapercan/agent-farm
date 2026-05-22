---
name: persistent-service-factory
section: "6-services"
state: working
owner: agent-farm conductor loop
source:
  - scripts/services/_supervisor-template.sh
  - docs/runbook-persistent-service.md
  - examples/queue-watcher/queue-watcher-supervisor.sh
  - examples/queue-watcher/queue-watcher-tick.sh
  - examples/queue-watcher/queue-watcher.yaml
runbook: docs/runbook-persistent-service.md
smoke: bash -n scripts/services/_supervisor-template.sh
---

# persistent-service-factory

Generic supervisor loop shared by every persistent service. Extracted
from `deploy-keeper-supervisor.sh` under FARM-FEAT.6 so a new persistent
service is a thin wrapper rather than a wholesale copy.

The template (`scripts/services/_supervisor-template.sh`) owns the
forever loop, the quick-retry ladder, the janitor escalation, the
`prereq_fail` carve-out, the cool-off pause, and the test seams
(`TICK_CMD_OVERRIDE`, `SUPERVISOR_NAP_CMD`, `QUICK_RETRY_LADDER_OVERRIDE`).
A wrapper sets five parameters and sources it:

- `TICK_SCRIPT`, `POLL_INTERVAL`, `MAX_CONSECUTIVE_FAILURES`,
  `PAUSE_AFTER_PAUSE_SEC`, `FAIL_KIND_ENV_FILE`.

Two optional hooks let a service override behaviour without forking the
loop: `service_escalate` (default spawns a `service-rescue` janitor) and
`service_nap_between_ticks` (default plain sleep; deploy-keeper overrides
it with its trigger-aware nap).

## Source coordinates

- `scripts/services/_supervisor-template.sh` (the shared loop)
- `scripts/services/deploy-keeper-supervisor.sh` (production wrapper,
  adds the trigger subsystem + custom escalation)
- `examples/queue-watcher/` (placeholder second service, NOT
  productionised: demonstrates the minimal wrapper with template
  defaults)
- `docs/runbook-persistent-service.md` (how to add a new service)

## State

working. deploy-keeper is the production consumer; its runtime behaviour
is unchanged by the extraction (tests
`tests/test_deploy_keeper_backoff.sh` +
`tests/test_deploy_keeper_triggers.sh` still green). The example
queue-watcher is a placeholder demonstrating reuse; a real RabbitMQ
queue-watcher is out of scope for FARM-FEAT.6.

## Smoke test

```bash
bash -n scripts/services/_supervisor-template.sh
bash -n scripts/services/deploy-keeper-supervisor.sh
bash -n examples/queue-watcher/queue-watcher-supervisor.sh
bash tests/test_supervisor_template.sh
bash tests/test_deploy_keeper_backoff.sh
```

## Runbook

- `docs/runbook-persistent-service.md` walks through adding a new
  persistent service step by step.

## Current owner

agent-farm conductor loop.

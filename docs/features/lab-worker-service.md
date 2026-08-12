---
name: lab-worker-service
section: "4-infrastructure"
state: working
owner: compute node, unattended
source:
  - scripts/services/protea-lab-worker.sh
  - scripts/services/protea-lab-worker@.service
  - scripts/services/protea-lab-worker.logrotate
runbook: scripts/services/README-lab-worker.md
smoke: bash -n scripts/services/protea-lab-worker.sh
---

# lab-worker-service

The compute node rejoins the server's queues by itself after a reboot, and
publishes logs a dashboard can read.

The desktop is a personal machine and is restarted without warning. Before this
existed, a restart meant the graphics card sat idle until somebody remembered to
start a worker by hand. A two-hour absence in the middle of a fifteen-hour run
cost an hour of throughput for that reason and no other.

## Source coordinates

- `scripts/services/protea-lab-worker@.service`, a templated systemd user unit,
  one instance per queue
- `scripts/services/protea-lab-worker.sh`, the wrapper the unit runs
- `scripts/services/protea-lab-worker.logrotate`
- `scripts/services/README-lab-worker.md`, the runbook

## What it does

One instance per queue, named by the queue: `protea-lab-worker@protea.embeddings.batch`.
`Restart=always` brings it back after a crash, and `RestartPreventExitStatus=78`
stops it retrying a configuration error forever.

Logs are appended under the user's own storage and emitted as JSON, because the
platform's log rules are JSON and a worker writing plain text is invisible to
every dashboard rule that parses them. That was the defect this feature was
extended to fix.

`PYTHONUNBUFFERED=1` is set. Without it the wrapper's output is block buffered
when stdout is a file, and a healthy worker looks dead for the first half hour.

## Unattended restart requires linger

A user unit does not start until somebody logs in. **`loginctl enable-linger`
must be set on the account**, or a reboot leaves the queues unconsumed until a
human reaches the greeter. It was measured off on the compute node on 2026-08-12
and enabled the same day; before that, the claim that a reboot brings the worker
back without a human was false.

Verify with `loginctl show-user <user> | grep Linger`.

## Smoke

```bash
bash -n scripts/services/protea-lab-worker.sh
systemctl --user is-enabled 'protea-lab-worker@protea.embeddings.batch'
loginctl show-user "$USER" | grep Linger
```

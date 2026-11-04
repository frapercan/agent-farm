---
name: node-revision-sync
section: "4-infrastructure"
state: working
owner: compute node, unattended
source:
  - scripts/services/protea-node-sync.sh
  - scripts/services/protea-node-sync.service
  - scripts/services/protea-node-sync.timer
  - plans/DECLARED-REVISION.txt
runbook: scripts/services/README-lab-worker.md
smoke: bash -n scripts/services/protea-node-sync.sh
---

# node-revision-sync

The compute node follows the revision the server's workers are running, and
refuses to follow anything it cannot verify.

The two machines share no state and nothing on the node pulls. An instruction
committed on the laptop sits unseen on the desktop until a person carries it
across, and the cost of not carrying it is not a wrong answer: the revision
guard makes a worker on the wrong commit refuse every batch, which on the server
side is indistinguishable from a queue with no consumer.

On 2026-08-30 the drift was a single internal dependency, `protea-method`. Its
version string read `0.3.1` on both commits, so no version check anywhere could
see it, and the only witness was `direct_url.json` inside the dist-info.

## Source coordinates

- `scripts/services/protea-node-sync.sh`, the whole of the logic
- `scripts/services/protea-node-sync.service` and `.timer`, a oneshot on a
  three minute persistent timer
- `plans/DECLARED-REVISION.txt`, what the server declares
- `scripts/services/README-lab-worker.md`, the runbook, section "Following the
  server, without being told"

## What it does

Reads one line from this repository with `git show origin/main:...`, so it never
checks anything out and cannot disturb a tree somebody is using. **Every sibling
package is derived from that commit's own `poetry.lock`**, because the lockfile
is already the authority and a second list is a second thing to disagree with.

The declared line names what the workers are RUNNING, not what a tree is checked
out at. Those are two quantities and they differed on the day the file was
written: a branch was checked out in the server's deploy tree while a twelve arm
sweep was live, the workers had loaded their code hours earlier and never
reloaded, and two arms recorded a revision no process had ever held.

## Every worker of the slot moves, in every environment it uses

Every worker on a node runs out of the same deploy slot, so the units are
derived rather than listed. They are every `protea-lab-worker@` instance whose
working directory is the slot, named by the units the user manager has loaded
and by the drop-in directories this node has configured. The running ones are
stopped and started together, and the stopped ones stay stopped. Each unit's
environment is its own `VIRTUAL_ENV`, or `PROTEA_VENV`, and each distinct
environment is synced: with its pip, or with `uv pip` when it has none. Until
2026-11-04 the script moved one unit and one environment. The other workers kept
the code they had imported, under a tree that had moved, and the node's Python
3.12 environment was synced by hand.

## It refuses rather than guesses

Every step that changes the node is gated on the check in front of it, and a
check that cannot run is a refusal. It refuses a sha that is absent from the
clone, a sha that is not an ancestor of `origin/develop`, a dirty deploy slot,
an environment with no installer, and a sha that changes `alembic/versions/`
unless the declaration also carries a matching `schema-applied` line. It defers
while any running worker of the slot has a job or a batch in flight, reading the
first worker's log of each queue and every extra's: a batch until its log has
been silent for 1500 s, a job until it is 6 h old, because a job consumer
writes nothing between dispatch and finish and a GOA release load is silent for
close to two hours. If an install fails or leaves a sibling wrong, if torch
reads differently in any environment, if the card's environment loses CUDA, or
if the operation does not import, **the workers stay down**: a silent wrong
consumer is worse than no consumer. A worker that comes back on another revision,
read from its own start line, is stopped.

The migration check is a local git diff and never opens the database. Reading
the applied revision off the live server is exactly the access a compute node
should not have, so the check detects that a revision changes the schema and the
acknowledgement line is the server asserting the rest.

## Smoke

```bash
bash -n scripts/services/protea-node-sync.sh
PROTEA_SYNC_DRYRUN=1 ~/.local/lib/protea/protea-node-sync.sh
PROTEA_DECL_FILE=/tmp/decl.txt ~/.local/lib/protea/protea-node-sync.sh   # rehearse an undeclared move
systemctl --user list-timers protea-node-sync.timer
```

A dry run runs every check a real tick runs and stops where it would act, so it
reports a refusal, a deferral or the units it would stop, and touches nothing. `node-sync.state` in the
log directory carries the last verdict and is written on every path, including
the ones that do nothing, because a state file left from an earlier run reads as
a current one.

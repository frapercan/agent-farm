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

## It refuses rather than guesses

Every step that changes the node is gated on the check in front of it, and a
check that cannot run is a refusal. It refuses a sha that is absent from the
clone, a sha that is not an ancestor of `origin/develop`, a dirty deploy slot,
and a sha that changes `alembic/versions/` unless the declaration also carries a
matching `schema-applied` line. If an install fails, leaves a sibling wrong,
costs torch its CUDA build, or leaves the operation unimportable, **the worker
stays down**: a silent wrong consumer is worse than no consumer.

The migration check is a local git diff and never opens the database. Reading
the applied revision off the live server is exactly the access a compute node
should not have, so the check detects that a revision changes the schema and the
acknowledgement line is the server asserting the rest.

## Smoke

```bash
bash -n scripts/services/protea-node-sync.sh
PROTEA_SYNC_DRYRUN=1 ~/.local/lib/protea/protea-node-sync.sh
systemctl --user list-timers protea-node-sync.timer
```

A dry run reports what it would do and touches nothing. `node-sync.state` in the
log directory carries the last verdict and is written on every path, including
the ones that do nothing, because a state file left from an earlier run reads as
a current one.

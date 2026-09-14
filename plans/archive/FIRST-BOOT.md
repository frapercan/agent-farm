# First boot on the reinstalled machine

What to do, in order, the first time the new system comes up. Every command
here was checked against the tree that produced this file rather than
remembered, and every gap is named where it bites rather than at the end.

The companion documents stay authoritative for WHY: `GENESIS-STATE.md` for what
the bring-up is missing, `CAMPAIGN.md` for the run itself, `DECISION-LOG.md`
for the decisions this file assumes.

---

## 0. Recover, before anything else

The archive partition is a separate disk and survives the reinstall. Everything
below lives under `/mnt/protea-archive/archive/`.

**Do this first, and do the paper first of all.** It is the one thing that
exists nowhere else: the repository has no remote, so the mirror is the only
copy in the world.

```bash
cd ~/Thesis2
git clone /mnt/protea-archive/archive/preformat-preserve-2026-07-28-local-only-repos/complexity-paper.git complexity-paper
git clone /mnt/protea-archive/archive/preformat-preserve-2026-07-28-local-only-repos/CAFA_forever.git   CAFA_forever
```

Then give the paper a real remote. Until it has one, every new commit sits
exactly where the first thirteen sat.

The rest:

| what | where |
|---|---|
| the secret surface, no template exists in any repository | `preformat-preserve-2026-07-27_preformat/secrets/protea.env` |
| database dumps, newest first | `protea-dumps/` |
| the object store snapshot | `preformat-preserve-2026-07-27_preformat/minio/` |
| assistant memory for this project | `preformat-preserve-2026-07-27_preformat/claude-memory.tar.gz` |
| artefacts whose producer was never found | `preformat-preserve-2026-07-27_preformat/no-producer-artifacts/` |

Restore the secrets to `~/.secrets/protea.env` and `chmod 600` it. Nothing
recreates that file and no repository documents its contents.

---

## 1. Host

```bash
bash ~/Thesis2/agent-farm/scripts/bootstrap-fresh-machine.sh
```

It is idempotent and skips what is already present. It installs the build
toolchain, the database client, Python, pip and pipx, Poetry, Node and Docker.

**It is an orphan.** No document in any repository referenced it before this
one, which is why it was easy to forget it existed.

**What it does not do, and nothing else does either.** Each of these has to be
done by hand:

- **The graphics driver.** The installed torch wheels assume a specific CUDA
  runtime. No script installs or pins the driver, and the mismatch does not
  surface until the first embedding job.
- **InterProScan**, still a prerequisite for the functional-enrichment stage.
- **The tunnel token and the reserved domain.** The domain survives the
  reinstall; the local credential does not.
- **The five scheduled jobs**, recorded in
  `agent-farm/observability/CRONTAB.md`. One of them points into `storage/`,
  so it fails silently until that tree is restored.
- **The deploy runtime slot**, below. This one is the most likely to be missed.

### The deploy slot

```bash
cd ~/Thesis2/repositories/PROTEA
git worktree add ~/Thesis2/worktrees/protea-deploy <ref>
```

Thirteen scripts hardcode that path and **nothing creates it**. The count is
from a sweep of both script directories, not from an earlier document that said
seven. The monitoring
stack binds its provisioning directory from inside it, so a missing slot shows
up as a dashboard that renders empty rather than as an error that says what is
wrong.

---

## 2. Platform

```bash
cd ~/Thesis2/repositories/PROTEA
poetry install
docker compose up -d                      # containers and volumes
poetry run python scripts/init_db.py      # schema, first time only
poetry run alembic upgrade head           # migrations
bash scripts/manage.sh start              # api, workers, frontend
```

### The cold-boot trap

**Two divergent copies exist and their flags are not compatible.** This was
verified, not inferred:

| | flags |
|---|---|
| `agent-farm/scripts/cold-boot.sh` | `--status --deploy --sync --restart --hard --short --force-deps --max-time` |
| `repositories/PROTEA/scripts/cold-boot.sh` | `--fast --no-build --no-deps --no-ngrok --no-watchdog --value` |

They share only four flags out of twelve. **The agent-farm copy is canonical**
and the documentation points at the other one, so a habit learned from the docs
runs the wrong script with flags it does not accept.

And the rule that survives from the previous machine: **boot is not deploy.**
Read the status first. The revive path is fast and idempotent; only the deploy
path syncs and reinstalls.

```bash
bash ~/Thesis2/agent-farm/scripts/cold-boot.sh --status
```

---

## 3. Restore the database

```bash
pg_restore -d protea --clean --if-exists -j 4 \
  /mnt/protea-archive/archive/protea-dumps/<newest>.dump
```

Watch for the loading defect recorded against the most recent annotation set:
it presents as a loader warning rather than an error, so a short load looks
like a successful one.

---

## 4. The campaign

`CAMPAIGN.md` is authoritative from here. Two things to carry in before the
first command, because both change what the early steps are for.

**There is no rehearsal run.** The first window goes through the entire chain,
evaluation included, and everything stops for inspection before the run widens.
That gate is where the seam the audit found becomes visible: several consumers
resolve their input from a filesystem path in an environment variable rather
than from a registered entity, and that is invisible until something flows.

**The adjustment set is not yet expressible.** With the releases the plan
currently enumerates there are no candidate windows at all, because the table
begins at the comparable window's own start. Earlier cuts have to be ingested
before a champion can be selected. The split registry reports this through a
function to gate on rather than leaving it to be discovered mid-run.

---

## 5. What will stop you, and is not written anywhere

Two gaps in the corpus phase, both known and neither closed:

**The ingest payload that produced the corpus is recorded nowhere.** The only
documented example is a toy query. Reconstructing it is an afternoon, not a
week, but it is reconstruction and not replay.

**The snapshot sweep** that maps each release to its source archive exists in
no script, no configuration and no plan.

Write both down as operations the first time they are reconstructed. That is
the invariant this campaign runs on: no artifact without an operation that
produces it, and a procedure outside the platform is a capability that dies
with the disk. This document exists because that lesson was learned the
expensive way, one command before a reinstall.

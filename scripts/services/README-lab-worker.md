# The compute-node worker, as a service

The project runs on two machines. The laptop is the persistent server and owns
all state: the database, the object store, the broker, the job registry. The
desktop is a compute node that holds no state, joins the server's queues,
computes, and publishes results back.

That split already survives a reboot of the compute node without losing work,
because the server owns everything. What it did not survive, until this unit
existed, was the node coming back: a worker started by hand dies with the
terminal that started it, and **the compute node is also somebody's personal
machine, so it gets rebooted.** On 2026-07-29 that cost about an hour of
compute, because the queue ran with one consumer instead of two until somebody
noticed.

This unit removes that failure. Nothing else about the topology changes.

## Install

```bash
mkdir -p ~/.config/systemd/user ~/.local/lib/protea ~/Thesis2/storage/logs
install -m 755 scripts/services/protea-lab-worker.sh    ~/.local/lib/protea/
install -m 644 scripts/services/protea-lab-worker@.service ~/.config/systemd/user/
systemctl --user daemon-reload
```

The wrapper is installed rather than run out of the checkout, so a branch
switch, a rebase or a removed worktree cannot stop a node that is mid-run. The
repository is still the source of truth: after pulling a change to either file,
repeat the two `install` lines and then

```bash
systemctl --user daemon-reload
systemctl --user restart 'protea-lab-worker@*'
```

**Enable lingering, or the service stops when you log out.** A user service is
bound to the user's session unless lingering is on, which defeats the purpose on
a machine you log out of.

```bash
sudo loginctl enable-linger "$USER"
loginctl show-user "$USER" | grep Linger    # expect Linger=yes
```

Then enable the queue this node should consume. The instance name is the queue
name:

```bash
systemctl --user enable --now protea-lab-worker@protea.embeddings.batch.service
```

## Operate

```bash
systemctl --user status  protea-lab-worker@protea.embeddings.batch.service
systemctl --user restart protea-lab-worker@protea.embeddings.batch.service
systemctl --user stop    protea-lab-worker@protea.embeddings.batch.service
journalctl --user -u 'protea-lab-worker@*' -f
```

Per-batch timings, which the throughput analysis reads, go to
`~/Thesis2/storage/logs/protea-lab-worker-<queue>.log`. That path is deliberate:
the first version of this logged to `/tmp` and a reboot erased fourteen hours of
timings.

## What it assumes

- `~/.secrets/protea-lab.env` defines `PROTEA_DB_URL` and `PROTEA_AMQP_URL`
  pointing at the server. The wrapper sources it as shell, so `export` prefixes
  are fine, which is why `EnvironmentFile=` is not used.
- A PROTEA checkout at `~/Thesis2/repositories/PROTEA` with dependencies
  installed, and poetry at `~/.local/bin/poetry`. All three are overridable
  through `PROTEA_LAB_ENV`, `PROTEA_REPO` and `POETRY_BIN`.
- Paths use systemd's `%h` rather than a literal home directory. The other unit
  in this directory hardcodes one, and every hardcoded home in this project
  broke when the username changed.

## Restart behaviour, and why it is shaped this way

`Restart=always` with `RestartSec=30`, and the start rate limiter disabled. The
server can be unreachable for hours; the node should keep trying rather than
give up and need a human.

`RestartPreventExitStatus=78` is the exception. The wrapper exits 78 for
configuration problems: a missing environment file, a missing checkout, no
poetry, no connection settings. Those do not fix themselves, so the unit stops
and says so instead of looping every thirty seconds.

Stopping sends SIGINT and waits up to two minutes, so an in-flight batch can
finish. A batch killed mid-flight is not lost, because the broker redelivers
anything unacknowledged; the wait only avoids computing it twice.

## Which queues belong here

One instance per queue, and only the compute-bound stages. The embeddings batch
stage belongs on the node; the write stage stays on the server, which is the
split the queue layout already encoded and the reason both machines are useful
at once.

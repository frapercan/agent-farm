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

**The format is JSON, not text.** The platform's own default is json and a text
line is invisible to any pipeline that filters on structure: a Loki rule written
as `| json | level="error"` never matches one. The first version of this script
passed `--log-format text`, which would have made the compute node the one
machine whose failures no dashboard could see.

**Rotation is not automatic.** `append:` does not rotate and these files grow for
as long as the node runs. `protea-lab-worker.logrotate` in this directory is a
user-level rotation that needs no root; wire it into your own crontab. It uses
`copytruncate` on purpose, because the worker holds the file open through systemd
and a rename would leave it writing to an unlinked inode.

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

## The clock gate

The node dual-boots, and Windows writes local time to the hardware clock. After
a Windows session the Linux kernel reads that clock as UTC, so the system clock
comes up exactly two hours fast and stays that way until chronyd steps it back.
On 2026-08-29:

```
05:46:04  kernel sets the system clock from the RTC   (two hours fast)
05:46:11  systemd starts the worker unit              (worker alive, clock wrong)
05:46:20  worker consumes a job and writes three events with the skewed clock
05:46:23  chronyd steps the clock by -7199.5 seconds
```

Twelve seconds of exposure, and the worker took its job with three seconds to
spare. Those rows are stamped two hours in the future and nothing downstream can
tell them from real ones: a job event carries the clock of the machine that
emitted it, so a compute node that starts early does not merely mislabel its own
work, it writes fiction into the stream both machines read. 2026-08-11 has the
same shape. Two episodes in 798,081 events, both on this node.

The wrapper now waits for `timedatectl show -p NTPSynchronized --value` to say
`yes` before it execs the worker, for up to 120 seconds, overridable with
`PROTEA_LAB_CLOCK_WAIT` and capped at 600. That property is the kernel's own
sync flag read through adjtimex, so it is the same clock the worker will stamp
events with and it does not care which daemon clears it.

**The gate cannot keep the node down.** When the budget runs out it starts
anyway. A permanently broken NTP behaves exactly as this node behaved the day
before the gate existed, two minutes later and with a loud warning, and never as
a queue whose only consumer has quietly decided not to consume. That direction
is deliberate: a node that is up, looks healthy and computes nothing is the
failure this project is worst at noticing, and it once cost 110 minutes.

The cap exists for the same reason. The budget is read from the environment
file, and it is the one number here that can hold the node off its queue: 1200
is a plausible "give NTP plenty of time" and it buys twenty minutes of a unit
sitting in `active (running)`, absent from `--failed`, silent in the log,
consuming nothing.

The budget is also paid at most once per boot **per queue**, because a give-up
leaves a marker in `$XDG_RUNTIME_DIR`, which is tmpfs. Without it a node with
broken NTP would add the budget to every one of the thirty-second restarts the
unit performs while the server is unreachable, and take 150 seconds rather than
30 to notice it come back. The marker is per queue and not per boot because this
node runs several instances of the template at once, and an unscoped marker lets
the first instance to give up disarm the gate for all the others on a boot where
the clock is still wrong. Note the consequence: after a give-up, a restart of
that same queue during a still-skewed window will not hold. The marker can only
ever cause less waiting, never more, and it is deleted the moment any start for
that queue sees a synchronised clock.

**It is not in the unit file, and it cannot be.** These are user units and a
user manager cannot order against a system target:

```bash
systemctl --user show time-sync.target -p LoadState   # LoadState=not-found
```

So `After=time-sync.target` would order against nothing while reading as a gate.
The `After=network-online.target` and `Wants=network-online.target` this unit
used to carry were inert for exactly that reason, which is why the worker could
start before the network was up, and they have been removed rather than
commented.

Two traps in checking any of this, and they point in opposite directions.
`systemctl --user show <unit> -p After` lists ordering names even for units that
do not exist, so it reports what was asked for rather than what will happen, and
grepping it proves nothing about whether a gate fires. And `LoadState` answers
only for unit types that need a unit file: measured here, an invented
`.service` and an invented `.target` both report `not-found`, but an invented
`.slice` reports `loaded`, because slices are implicit units systemd
synthesises on demand. So `LoadState` carries no information about a slice in
either direction, and the check above is sound only because it is asked of a
target. Confirm existence with `list-units --all`, not with `LoadState`.

Three other stock answers were checked and rejected.
`systemd-time-wait-sync.service` is not installed here at all, because the node
runs chrony rather than systemd-timesyncd, and `timedatectl timesync-status`
needs timesyncd for the same reason.
`ConditionPathExists=/run/systemd/timesync/synchronized` is worse than useless:
that path never exists on this machine, and a unit skipped by an unmet condition
reports `ActiveState=inactive` with `Result=success`, never appears in
`systemctl --user list-units --failed`, and makes `systemctl --user start` exit
0. That is a node that is up, looks healthy, and consumes nothing. An
`ExecStartPre=` was rejected too: the failure-tolerating `-` prefix does not
protect against `TimeoutStartSec`, so a dash-prefixed wait that outran the
timeout still failed the unit and looped with `ExecStart` never running.

### Reading the log afterwards

`StandardError=inherit` duplicates stdout, so every clock line lands in the same
file as the events. The verdict rides on the line that already anchors every
per-batch timing, so a normal start adds no line at all:

```
protea-lab-worker: starting queue=protea.embeddings.batch repo=... at 2026-08-29T14:30:05+02:00 clock=ok
```

and a skew episode reads

```
protea-lab-worker: clock NOT synchronised (up 7s, reads 2026-08-29T05:46:11+02:00); holding this worker off queue=protea.embeddings.batch for up to 120s rather than stamp events with a clock that is about to move
protea-lab-worker: clock synchronised after 12s of waiting
protea-lab-worker: the system clock STEPPED by -7199s during this startup. Lines above this one carry the old clock, lines below the corrected one.
protea-lab-worker: a step of 2h is the dual boot: Windows leaves LOCAL time in the hardware clock and Linux reads it as UTC.
protea-lab-worker: starting queue=protea.embeddings.batch repo=... at 2026-08-29T03:46:23+02:00 clock=ok
```

The step is measured as the difference between how far the wall clock moved and
how far the monotonic clock moved, because `hwclock` is not installed here: only
its manual page, a unit stub and a completion file survive. So `grep clock=` and
`grep STEPPED` over the logs answer in one line the question that twice took a
day.

### Proving the gate gates

That the line is present in the file proves nothing, which is the defect this
whole change is about. Run it where it MUST fire and require the behaviour:

```bash
PATH="/tmp/stub:${PATH}" \
PROTEA_LAB_CLOCK_WAIT=3 \
  bash scripts/services/protea-lab-worker.sh q.test
```

with `/tmp/stub/timedatectl` a two-line script that prints `no`. Require: the
holding line appears, the run takes three seconds and not zero, the warning
names the dual boot, and the anchor line ends `clock=unsynced`. Then flip the
stub to print `yes` after two probes and require `clock synchronised after 2s`
and `clock=ok`. A run of the unpatched wrapper against the same stub is the
control: it starts immediately and says nothing.

## Which queues belong here

One instance per queue, and only the compute-bound stages. The embeddings batch
stage belongs on the node; the write stage stays on the server, which is the
split the queue layout already encoded and the reason both machines are useful
at once.

# TOPOLOGY: two machines, and how instructions reach both

From 2026-07-29 the project runs on two machines. This file is the shared
description of that split. It lives here, in a repository both machines clone,
because that is the only place an instruction can be written once and read by
both.

`CAMPAIGN.md` stays authoritative for what the run is. `RUN-LEDGER.md` records
what has been computed and at what rate. `COLLIDING-A-NUMBER.md` says what has
to be true before a number either machine produces is allowed to travel between
them. This file answers a different question: which machine does what, and how
each one learns what you decided.

---

## 1. The two machines

| | role | owns state | is rebooted |
|---|---|---|---|
| **laptop** | persistent server | **everything** | rarely, deliberately |
| **desktop** | compute node | **nothing** | often, without warning |

**The laptop is the server.** It runs the whole stack and owns all state: the
database, the object store, the broker, the job registry, the frontend, the
monitoring. Every artifact the project produces lands there.

**The desktop is a compute node.** It holds no state. It joins the server's
queues, computes, publishes results back, and could be wiped without losing
anything but time. It also has the graphics card, which is why it exists in the
topology at all.

**The desktop is also a personal machine.** It gets used for other things and
rebooted without notice. That is a design input, not an inconvenience: the split
above is what makes it harmless.

### Why the split is shaped this way

It was tested by accident on 2026-07-29. The desktop was powered down for about
two hours in the middle of a fifteen-hour embedding run. Nothing was lost, no
job failed, no batch was dropped: the server kept the state and the queue, and
the run simply continued at half throughput until the node came back. The whole
cost was about an hour of compute.

That is the property to protect. Anything that would make a reboot of the
desktop lose work is a mistake, however convenient.

---

## 2. What runs where

**On the server:** the API, the frontend, Postgres, RabbitMQ, MinIO, Prometheus,
Grafana, Loki, and the worker for every queue including the write stages.

**On the compute node:** one worker per compute-bound queue, and nothing else.
Today that is `protea.embeddings.batch`. The matching write stage stays on the
server, which is the split the queue layout already encoded and the reason both
machines are useful at the same time.

The node's workers run under systemd so that a reboot brings them back without a
human. See `scripts/services/README-lab-worker.md`. Before that unit existed, a
reboot left the queue with one consumer until somebody noticed.

### The link between them

The two machines talk over wifi, and on 2026-07-29 the node measured the link at
-75 dBm with 40 ms average latency and 147 ms peaks, against 2.7 ms to its own
access point. That accounts for part of the per-batch overhead and is the
likeliest cause of the first connection drop that costs real work. A cable
removes this class of failure entirely and is the cheapest improvement available
to the run.

---

## 3. How instructions reach both machines

This is the part that is easy to get wrong, because two of the obvious channels
do not cross machines at all.

### Git crosses. Use it.

`CLAUDE.md`, this file and everything under `plans/` are in repositories with a
remote. An instruction committed on one machine reaches the other on the next
pull. **If something must be known by both machines, it goes in a repository.**

### Assistant memory does not cross, and that is the decision

The memory store is per machine, at `~/.claude/projects/<project>/memory/`, and
nothing synchronises it. A decision recorded there on one machine is invisible to
every session on the other.

**Decided 2026-07-30: memory stays per agent.** Each machine's sessions keep
their own store and see only their own. It is not a gap waiting to be closed by
a mirror, so no synchronisation is planned and `thesis2-archive` stays a
hand-refreshed off-machine copy rather than a channel.

That makes one rule mandatory rather than advisory: **memory is for what one
machine needs to remember, a repository is for what both machines must agree
on.** Anything the other machine must know is not recorded, it is committed. When
in doubt, commit it.

### The live state crosses by itself

Any session on either machine can read the server's job registry and see what is
running, what succeeded and what failed. That surface is shared by construction
and survived the reboot untouched. It carries facts, not reasoning: what ran,
not why it was decided.

### What each machine's root CLAUDE.md must say

The root `CLAUDE.md` is per machine and is not tracked by any repository, which
is why it did not survive the 2026-07-28 reinstall and had to be rebuilt from a
seven-week-old snapshot. Until that changes, each machine's copy needs two
things:

- **which of the two roles this machine has**, in one line, because nothing else
  on the machine says so
- **a pointer to this file**, so the shared part is read from the repository
  rather than duplicated into a file that is not tracked

---

## 4. Decided, so it is not re-litigated

### The API's read endpoints stay open

Writes on the jobs router require an operator role. All four reads do not:
`GET /jobs`, `GET /jobs/{id}`, `GET /jobs/{id}/events` and
`GET /jobs/{id}/comments` carry no auth dependency, and the router is mounted
without a global one. This is deliberate and consistent with the anonymous quota
the deployment already grants for a public open-research demo.

**Decided 2026-07-30: they stay open.** The consequence has to be designed for
rather than discovered, because the stack is reachable through a public tunnel:

- **A job's payload is public.** For an agent, the payload is its instruction.
- **A job's events are public.** For an agent, the events are its reasoning.

So the rule that follows, and it binds every agent operation: **nothing sensitive
inside a payload or an event.** Anything sensitive is passed by reference, an
identifier the server resolves against the secret surface, and is never inlined.
An agent that needs a credential receives the name of one, not the value.

### Memory is per agent

See section 3. Recorded here as well, because it is the decision that makes
committing mandatory.

---

## 5. Still open

**The root `CLAUDE.md` is tracked nowhere.** It is the highest-authority
instruction file in the project, it exists only as a loose file on each disk, and
it has already been lost once, in the 2026-07-28 reinstall. Tracking it would
close that. Not decided.

**Nothing pulls.** Both machines have checkouts that update only when somebody
runs `git pull`, so an instruction committed on one can sit unseen on the other
indefinitely. A periodic fast-forward of the instruction surface, plus a line
recording what changed, is what makes this file's promise real rather than
theoretical.

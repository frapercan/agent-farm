# Orchestration: how a non-trivial front gets advanced

Author instruction, 2026-09-02: **every time a non-trivial front has to be
advanced, orchestrate it rather than working it solo.** Solo work is for
conversational turns and trivial mechanical edits.

This file is in the plan store because assistant memory is per machine and
nothing synchronises it, so a rule that both machines must obey cannot live
there. It is short on purpose.

## The shape, and why it is not the obvious one

**Width is measured in waves, not in agents.** The concurrency cap is
`min(16, nproc - 2)`. On the compute node `nproc` is 12, so ten agents run at
once and everything above queues rather than failing. A fan-out of six and one
of ten cost the same wall clock. Eleven costs two waves. Twelve agents cost
about what twenty cost. Size to ten, or to a multiple of ten.

**Use a pipeline, not a barrier.** A barrier empties all ten slots waiting on
the slowest agent of the stage before the next stage starts. A pipeline lets
item A reach stage three while B is still in stage one, so the slots stay
saturated and the clock is the slowest single chain rather than the sum of
per-stage maxima. With a stage whose slowest agent takes three times the
fastest, a barrier wastes two thirds of the fast agents' time.

A barrier is correct only when stage N needs every result of N-1 at once:
deduplicating before an expensive verification, cutting early if the total is
zero, or comparing each finding against all the others. Needing to map or
filter is not a reason.

**Split by read-surface overlap, not by phase.** This is the rule that decides
the shape, and it is not "wide first, narrow later" even though it usually
looks like that.

- If N subtasks read the same material, splitting them multiplies the prefill
  without adding information. Use one wide agent.
- If N subtasks read disjoint material, each agent loads only its own. Use many
  narrow agents.

Which is why the canonical shape is a few wide reviewers per dimension, all
reading the same material, feeding many narrow verifiers, each reading only its
own finding.

## What crosses between agents, and what must not

No agent inherits context from another. Every call is a clean prefill. The only
channels are the prompt string, a schema, and the pipeline callbacks.

**Propagate conclusions and pointers to the evidence, never narration.** A
schema returning a claim, a file, a line, a receipt path and a verdict costs
hundreds of tokens. Passing the previous agent's reasoning prose costs
thousands, and the receiver treats it as somebody else's assertion rather than
as evidence. Having the verifier reopen the file is both cheaper and more
reliable than telling it what the file said.

**Never spend an agent on flattening, filtering or deduplicating.** That is
plain code inside a pipeline stage.

**Explore first, then orchestrate.** List the files, bound the diff, derive the
item list with ordinary tools, and hand the workflow a concrete list. Paying an
agent to run a find is waste.

## Cost levers, in order of value

1. **Low effort on mechanical stages, high only on the judge or the refuter.**
   Best ratio of saving to risk available.
2. **Resume by run id with a script path** while iterating. The unchanged
   prefix of agent calls returns from cache instantly and only the first edited
   call onward runs live.
3. **A token budget** when the depth should scale with what was budgeted.

## The natural unit of fan-out here

The nine cells, category by aspect, and nine fits in one wave. For a sweep:
nine measuring agents over disjoint cells, each feeding its own refuters. For a
review of one lever the shape inverts: two or three wide agents reading the
signal registry, the receipts and the code, which is the same material and must
not be split, then one verifier per surviving number.

## Two limits of the compute node

**Resources.** The ten slots compete with the compute worker running under
systemd, and there is one card with 12 GB. A workflow agent touching the card
while an embedding batch runs is the documented CUDA out-of-memory. Workflow
agents on that machine are read and analysis only. Anything that dispatches
goes through the jobs endpoint, never through an agent.

**The standing project rules still hold.** No agent is ever pointed at the live
database, and worktree isolation is never taken over the developer workspace.

## One rule paid for in lost work

**Every agent writes its report to disk as it goes, before returning.** On
2026-09-02 two runs were killed by a session limit at the moment their agents
were about to synthesise. Twelve agents had done 236 tool calls of real
investigation and returned nothing, because they were holding their conclusions
until the end. Only the narration survived, recovered from the transcripts.
What is on disk is what survives, and it has to be enough for someone else to
continue from.

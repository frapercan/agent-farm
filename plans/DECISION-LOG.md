# Decision log

Decisions taken deliberately, with what they cost and why the alternative was
declined. One entry per decision, newest first. A decision that is not written
here was not taken, it was drifted into.

This exists because several of the campaign's hardest problems turned out to be
decisions nobody had recorded, which meant they were re-litigated every time
someone met the evidence again.

---

## D-05 · The target is nine of nine on the internal split; the prior standing is non-comparable prior work

**Decided 2026-07-28.**

The campaign goes for every cell. The previously recorded standing is **not** the
baseline it competes against, and it is not carried forward as a target.

**Why it cannot be the baseline.** The audit established that the standing was
not measured once: four successive arms were scored on the same frozen frame and
the best kept, and the registry itself records the final increment as selected on
test. Competing against that number would mean holding a clean measurement up
against an inflated one, and losing for reasons that have nothing to do with the
system being worse.

**What replaces it.** The target is stated per cell on the internal adjustment
split, scored with our own evaluator. The external series is reported and never
optimised against. The prior standing survives in the manuscript as context,
labelled with how it was obtained.

**What this obliges.** No gate anywhere in the ladder may reference an external
number. Any sentence claiming the campaign beats the prior standing is removed,
because the two are not measured on the same instrument.

---

## D-04 · The short run runs the full chain, which makes the ground truth builder a precondition

**Decided 2026-07-28. The consequence is a reordering, and it is the point of
recording this.**

The short run goes end to end, evaluation included, rather than stopping at
feature production.

**The consequence.** With D-02 decided, evaluating through the existing builder
would certify the exact component the campaign has decided to replace. So the
window decomposition and the first-appearance builder move **before** the short
run rather than beside it. That is more work up front, and it is the coherent
order: there is no value in proving a chain end to end using the part that is
being discarded.

**What was given up.** Evaluation is the best-tested stage in the system: a probe
reproduced it from frozen inputs in under ten seconds and matched the recorded row
at full granularity. Including it therefore adds cost without reducing much
uncertainty. The decision accepts that, on the grounds that a chain proven only to
its penultimate stage has not been proven.

**Constraints that stay.** The window is strictly earlier than any adjustment
window and is recorded in the exit receipt. The unreviewed retrieval hop carries
the provenance split. The short run's corpus is torn down before the campaign
proper begins, so nothing it produced can leak into a later split.

---

## D-03 · The exclusion list is what the protein knew at the start, and it is now declared

**Decided 2026-07-28.**

For the prior-knowledge cells, the terms withheld from scoring are the protein's
**full set at the start of the window**, including terms the corpus has since
withdrawn.

**Why.** The category is defined at the start of the window, so what the protein
knew then is the semantics of prior knowledge. The alternative, intersecting with
what still counts at the end, would penalise the method for predicting something
that was true at the start and that the corpus later removed. That is a corpus
event, not a modelling error.

**What changes, since this is the current behaviour.** It stops being an
undeclared implementation detail. The rule is written into the split registry
alongside the splits themselves, and **the count of withdrawn-from-known is
reported per release**. Without that count, the dip the series will show at the
corpus contraction is unattributable, and this mechanism is the largest single
effect in the whole scoring frame.

---

## D-02 · Ground truth is first appearance, not a pairwise difference

**Decided 2026-07-28.**

An annotation counts as ground truth for a window if it is present at the end of
the window **and was never present at any earlier cut**. The existing pairwise
difference is retired.

**Why.** The corpus contracts as well as grows, so an annotation can be present
early, be withdrawn, and return. Under a pairwise difference it then counts as
new, and the method is asked to predict something already known and already
sitting in its training corpus.

**The measurement that settled it.** A probe over eleven consecutive release
dumps found that on all-evidence data as much as 63.7% of apparent additions had
been seen before. On experimental evidence, which is the operating regime, the
rate falls to about one percent. One percent would be tolerable if it were
uniform, and it is not: **the leak tracks the contraction points**, and the
validation window crosses one. A single global correction would be wrong exactly
where it matters.

**What it costs and what it buys.** It requires the release history rather than
two endpoints, which the run re-ingests anyway. In exchange the restoration rate
becomes a published property of the corpus in its own right, which is a result
rather than a caveat, and it is the version that survives a reader who looks at
the release table.

---

## D-01 · Assistant attribution in merged history is kept, not rewritten

**Decided 2026-07-28. Author's decision, recorded rather than acted on.**

### What was found

An audit swept every repository for an assistant co-authorship trailer in commit
messages. The result, verified across all ten trees:

| Repository | Commits carrying the trailer |
|---|---|
| the platform | 25 |
| the backends plugin set | 4 |
| the offline lab | 4 |
| the runners plugin set | 3 |
| the sources plugin set | 3 |
| the orchestration repository | 3 |
| the inference layer | 2 |
| the contracts package | 1 |
| the manuscript | 1 |
| **total** | **46** |

An earlier estimate of six was wrong by a factor of nearly eight, and the
decision was taken with the corrected figure in hand.

### Why it was not rewritten

Three costs, each verified rather than assumed.

**Nine release tags point at affected commits.** A rewrite changes every hash, so
each tag would either dangle or have to be moved. A moved release tag no longer
means what it said, and the releases it labels are already referenced elsewhere.

**The repositories pin each other by resolved commit.** The platform's lock file
fixes specific commits of the contracts package, the inference layer and the
three plugin sets. A rewrite invalidates all of them at once and forces a
regeneration cascade across nine repositories, which is a failure mode this
project has already recorded once.

**It requires force-pushing to protected branches**, which the project's own
hard constraints forbid, and which its memory records as a hard stop rather than
a workaround.

### Why keeping it is defensible

The constraint exists so that **publishable prose** carries no assistant
attribution: the manuscript, the READMEs, the reference narrative, the papers.
Merged commit messages are record, not prose, and no reader of the thesis meets
them.

The defect is also already closed going forward. A continuous-integration guard
rejects the trailer on new pull requests, and every one of the 46 predates it.
The problem is historical and bounded, not ongoing.

Against that, a rewrite would destabilise the dependency graph and the release
history at precisely the moment the campaign needs a stable base.

### What this obliges

- **The forward guard stays required.** If it is ever disabled, this decision
  stops being defensible and the trailer starts accumulating again.
- **Publishable prose stays clean.** This decision covers merged history only.
  The manuscript, the READMEs and the narrative remain subject to the original
  constraint without exception.
- **This record is the answer.** Anyone who finds the trailer in history should
  find this explanation rather than an unexplained trace, which is the entire
  point of writing it down instead of quietly leaving it.

---

## D-06 The contract fork blocks the campaign, and closing it is a release decision

**Status: OPEN. Needs the author.**
**Raised: 2026-07-28, by the donor-policy work hitting it head on.**

### What was found

The main pipeline declares its dependency on the shared contract package at
that package's **release branch**. Every contract change of this campaign, the
donor policy among them, has landed on the package's **trunk**, which now sits
thirty two commits and two minor versions ahead of the release branch.

The consequence is not subtle. A pipeline branch that imports anything added
to the contract on the trunk resolves the release branch instead, fails to
import it, and takes the entire test suite down with it at collection time,
whatever else that branch touched. That is how it surfaced: three red checks
on a change that had nothing to do with contracts.

### Why it matters beyond one pull request

This is the operational cost of a divergence the project has recorded before
and left open. It means the pipeline's trunk **cannot consume a new contract
at all** until a promotion happens. Any campaign work that needs a new payload
field, a new policy, or a new schema column is blocked behind that promotion,
not behind its own merit.

It also bears directly on the requirement that the contracts be clean in both
the short and the long run. They are not currently clean: they mean two
different things depending on which branch resolved, and the pipeline is
pinned to the older meaning.

### Why it is not decided here

Promoting the trunk to the release branch cuts a release. The project's own
record is explicit that promotion carries continuous integration across the
dependent repositories and can lock the release line, and that an override is
never the answer. That is an author decision about release timing, not a
janitorial fix an autonomous loop should take on its own initiative.

### The options, stated plainly

1. **Promote the contract trunk to its release branch.** Closes the fork,
   unblocks every dependent change, and is the only option that makes the
   contract mean one thing. Costs a release and the dependent integration that
   follows it.
2. **Point the pipeline at the contract trunk.** Unblocks immediately and
   contradicts the branch model, which exists so the pipeline builds against
   released contracts rather than moving ones.
3. **Keep contract-dependent work out of the pipeline until the promotion.**
   What this loop did to stay unblocked, by moving the affected tests onto the
   plain values the layer actually handles. It is correct for one case and does
   not scale: the query-side donor filter genuinely needs the payload.

### What was done in the meantime

The cache-key work was separated at the seam. The cache never imported the
payload type; only its test did. The layer's own property, that a restriction
reaches the key and every path built from it, is now pinned without reaching
across a repository boundary to state it, so that work is unblocked and merged
on its own merit.

**The query-side donor filter remains blocked on this decision**, because it
must read the policy the caller sent, and that policy is a contract type.

---

## D-07 A branch name was being used as a version, and it split the stack

**Decided 2026-07-28. Supersedes D-06, which framed this as a promotion to be
timed. It is not a timing problem, it is a model problem.**

### What was found

Six repositories consume the shared contract. They do not agree on what the
contract is.

| consumer | pinned to |
|---|---|
| the platform | the release branch |
| the inference layer | the release branch |
| the backends plugin set | the trunk |
| the runners plugin set | the trunk |
| the sources plugin set | the trunk |
| the offline lab | a commit |

**The stack builds against two different contracts at once, split down the
middle.** The plugins the platform loads at runtime are built against the
trunk; the platform that loads them is built against the release branch.

The damage today is bounded and was measured rather than assumed: the schema
identity is byte-identical on both branches, so no feature fingerprint
currently diverges. The divergence is in the payload surface. But the
mechanism that would let the schema diverge is intact and running.

### Why it happens, and why it is nobody's carelessness

Because consumers pin a BRANCH, that branch is the delivery channel. When
something is urgent it lands directly on the consumed branch to unblock the
consumer, bypassing the gates on the trunk. The promotion that is supposed to
reconcile them snapshots a tree rather than merging, so the trunk never
receives those commits back.

**The divergence therefore cannot converge. It grows by construction.** All
eight repositories are diverged in both directions, without exception, and the
commit subjects narrate the loop: port a family onto the release branch,
cherry-pick a fix to the release branch, forward-port the trunk, repin to
unblock the platform.

### What it already cost

A scorer fix landed on the release branch only. That commit is the origin of
the two scorer versions whose disagreement shifted one aspect's headline by
almost thirteen percent. **The branch model produced an inconsistency in a
measured result**, which is the strongest argument available that this is not
a matter of tidiness.

### The decision

A commit is a version. No release ceremony is required to have one.

1. **One branch per library repository.** With a single branch the question of
   which one is the contract cannot be asked.
2. **Consumers pin a commit, never a branch.** The offline lab already does
   this, which is the evidence that it works here. Updating a dependency
   becomes one pull request in the consumer that moves the commit and
   regenerates the lockfile, gated by that consumer's own checks, which is
   where the decision belongs.
3. **A check that refuses a branch pin**, so the invariant is enforced rather
   than remembered.

### How the collapse is performed

**By merging, never by snapshotting a tree.** The snapshot is the mechanism
that caused this: it produces a commit on one branch whose content matches the
other while sharing none of its ancestry, so the graphs drift apart forever and
no tool can see them as reconciled. A real merge makes the histories converge
once, which is the whole point.

### What this deliberately gives up

Tagged releases as the unit of delivery. Reproducibility comes from the
lockfile's resolved commit, which is exact, rather than from a tag, which is a
label on a commit that the lockfile was going to record anyway.

### D-07 correction, same day: the split was narrower than first stated

The entry above says the stack built against two contracts at once, split
between the plugins and the platform that loads them. **That is wrong for the
deployed path and the error was mine.** The claim came from reading the working
copies, which sit on the development branches, rather than the branches the
platform actually consumes.

Read from the consumed branches, every plugin and the platform pin the contract
to the same branch. The deployed stack was consistent.

| repository | on its release branch | on its trunk |
|---|---|---|
| the backends plugin set | the contract's release branch | the contract's trunk |
| the runners plugin set | the contract's release branch | the contract's trunk |
| the sources plugin set | the contract's release branch | the contract's trunk |
| the inference layer | the contract's release branch | the contract's release branch |
| the platform | the contract's release branch | |

The disagreement is real but it is **between each repository's own two
branches**, not across the running stack.

**What survives unchanged**, because each was verified rather than inferred:

- Every repository in the stack is diverged in both directions.
- Work lands on the consumed branch directly and the trunk never receives it
  back, so the divergence grows by construction.
- The platform's trunk could not consume a new contract type at all: it took
  the whole test suite down at collection time.
- Snapshotting a tree cannot make two branches converge, and a real merge can.
  Measured on the collapse: zero commits of the trunk left outside afterwards,
  and the trunk became a direct ancestor.
- Pinning a commit while a dependency pins a branch is refused outright by the
  resolver, which is what turns the latent disagreement into a hard failure.

**What is downgraded:** the urgency argument. This was not a live inconsistency
in what runs. It was a mechanism guaranteed to produce one, which is a weaker
claim and still sufficient to justify the change.

The wording is corrected here rather than by rewriting the commits that carry
it, since those are merged and the project does not rewrite merged history.

### D-07 outcome, same day: the cascade is closed on the trunks

Fourteen of the fifteen long-lived branches in the stack now name commits for
every internal dependency, and the check that refuses a branch pin runs on the
platform's pull requests. The contract package has one branch again, reached by
a real merge, so its trunk is a direct ancestor of its release line rather than
a tree that happens to match.

**Why the order was forced, and it was not a preference.** A resolver refuses
outright to satisfy one dependency pinned to a commit and another pinned to a
branch. Pinning the platform's contract while a plugin still named a branch did
not resolve at all. So the migration had to run leaf first: every consumed
package pinned its own dependencies before the package consuming it could pin
anything.

**What the work surfaced, all of it the same species.** Three checks that did
not check what their names claimed:

- Two repositories REQUIRED an attribution guard that no workflow in them
  produced. A required check nothing emits protects nothing and blocks
  everything, and it is why their pull requests sat unmergeable with no failure
  to point at.
- Four repositories configured the type checker for a Python older than the one
  they require. The mismatch made a dependency's own stubs a syntax error, so
  the run aborted before reaching any local source and reported a failure that
  had nothing to do with the code.
- One workflow matrix named three interpreters and ran one, because the
  resolver rejects the other two against the project's own requirement and
  falls back silently.

**What remains, and both belong to the author.**

The contract package's trunk branch still exists. Deleting it needs its branch
protection lifted first. Its commits are reachable from the release line, so
removing it loses no history, and the guard that compared the two now skips
cleanly when only one is present rather than failing forever.

The platform's release line still names branches for all seven of its internal
dependencies. It is six hundred and eighty four commits behind its trunk, so
this is not an omission in the migration: it closes when the trunk is promoted,
and promotion is a release decision.
---

## D-08 No rehearsal. The long run starts, and the first window is the gate

**Decided 2026-07-28. Supersedes D-04, which specified a separate small-scale
pass before the campaign proper.**

There is no short run. The campaign goes straight at the long run and implements
what surfaces, in detail, as it surfaces.

### What is kept, because it was never about scale

The rehearsal existed to enforce an **order**, not a size: exercise every hop
once before committing to a full pass. That survives as a gate inside the long
run. The first window goes through the entire chain, evaluation included, and
everything stops for inspection before the run widens.

The risk it guards is specific and was found by the audit rather than imagined.
Several consumers resolve their input from a filesystem path supplied by an
environment variable rather than from a registered entity, and that defect is
invisible until something flows. The gate is where it becomes visible and the
last cheap moment to fix it.

Passing means one dispatch chain completed end to end, every intermediate
registered with its provenance, the interface rendering each stage, and the
fragile points written down.

### What gets better, and it is not only cost

**The leak hazard disappears rather than being managed.** D-04 required the
rehearsal corpus to be torn down before the campaign proper began, precisely so
what it produced could not reach a later split. A teardown that must not be
forgotten is a hazard; not building the corpus removes it.

**The interface gets real data sooner.** Polishing a surface against fabricated
data is how a surface ends up describing a pipeline that does not exist. The
gate feeds it from the actual run rather than from something thrown away.

### What this accepts

A defect that a cheap pass would have caught early is now caught inside the
expensive one. That is the trade, and it is taken deliberately: the gate keeps
the detection point in the same place, so what changes is the cost of the
material flowing through it, not the moment the chain is proven.

### What does not change

The first window stays strictly earlier than any adjustment window. The
unreviewed retrieval hop still carries the provenance split. And evaluation
still runs through the first-appearance builder rather than the retired one,
which is the part of D-04 that survives intact: certifying a chain with the
component being discarded proves nothing about the chain that ships.

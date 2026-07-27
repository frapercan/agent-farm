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

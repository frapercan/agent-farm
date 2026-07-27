# Decision log

Decisions taken deliberately, with what they cost and why the alternative was
declined. One entry per decision, newest first. A decision that is not written
here was not taken, it was drifted into.

This exists because several of the campaign's hardest problems turned out to be
decisions nobody had recorded, which meant they were re-litigated every time
someone met the evidence again.

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

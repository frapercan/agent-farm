# Which scorer produced which number

Written 2026-07-27, before the operating system was reinstalled, because this is
the only moment both scorer generations could be run side by side on the same
frozen inputs. After the reinstall the older one resolves only if it is pinned,
and nothing pins it today.

## The defect

`PROTEA/pyproject.toml` line 32 depends on the evaluation fork by **branch**, not
by tag or commit. A branch moves. The consequence is already visible on this
disk: the two lock files disagree with each other.

| Location | Resolved commit |
|---|---|
| the platform repository checkout | `299e265` |
| the deploy worktree that actually serves | `80d705a` |

So the code that produced the published numbers and the code currently deployed
are not the same scorer, and neither is written down anywhere a fresh install
would read.

## What the difference is worth

Measured today, same driver recipe, same frozen prediction file, same ontology,
same accretion table, same ground truth. Only the scorer commit changed.

| Aspect | at `299e265` | at `80d705a` | shift | relative |
|---|---|---|---|---|
| molecular function | | | -0.063808 | -22.7% |
| cellular component | | | -0.046425 | -15.4% |
| biological process | 0.2013197 | 0.1754609 | -0.025859 | -12.8% |

The prior-knowledge exclusion delta, which is the single most load-bearing
mechanism in the measurement layer, also moves:

| | at `299e265` | at `80d705a` |
|---|---|---|
| without exclusion | 0.2013197218518963 | 0.1754608900289470 |
| with exclusion | 0.1166555161572292 | 0.1088951774478088 |
| delta | **-0.0846642** | **-0.0665657** |

That is a **21.4% shrink in the exclusion effect**. The intermediate commit in
the range was bit-identical, so the whole shift comes from one commit, and that
commit's own message describes its effect as tiny, around two thousandths of a
point. **On this frame that description is false**, by an order of magnitude.

## What this means for every recorded number

**The recorded per-cell tables and the leaderboard constants in the frame-parity
test are `299e265` numbers.** They were not produced by the current branch tip
and will not reproduce against it. A fresh install that resolves the branch will
silently produce different numbers and no check will notice, because there is no
recorded expectation to compare against.

## What must happen

1. **Pin the dependency to a tag or a commit**, in the platform and in every
   sibling that consumes the fork. A branch dependency is not a pin.
2. **Record the scorer identity beside every stored evaluation result**, so a
   number carries the code that produced it rather than relying on a lock file
   that is not archived with it.
3. **Treat the recorded tables as provenance, not as targets.** The clean run
   regenerates them under a pinned scorer; comparing new numbers against these
   without pinning compares two different measuring instruments.

## What could not be checked, and why that is itself the finding

The board's own pipeline activates an environment named for its evaluator. That
environment does not exist on this machine and no package manager that could
create it is installed. **The literal board pipeline therefore has no runnable
producer here today.** The reinstall does not create that gap; it only makes it
permanent. What does reproduce, and did, is the platform's own driver recipe,
which the parity test asserts is the same frame.

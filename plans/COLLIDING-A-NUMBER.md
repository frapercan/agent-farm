# Colliding a number

**Of the seventeen defects this project has recorded in its own measurements,
zero were found by the person who had produced the number.**

Every one was found by someone else, or by the same person days later reading
their own output as a stranger would. That is not a statement about competence.
It is a statement about position: the person who produced a number has already
accepted the reasoning that produced it, and is therefore the one reader who
cannot see the step that was skipped.

So this file is not advice about being careful. Care does not help, and the
seventeen are the evidence. It is five things that put a second, independent
object next to the first, so that the disagreement does the finding instead of
the author.

It lives in `plans/` because both machines read it. `TOPOLOGY.md` says who runs
what; this says what has to be true before a number either machine produces is
allowed to travel.

---

## 1. Produce a second number that must match the first

Not a check that the first number is plausible. A second computation, by a
different route, of a quantity that is forced to be equal. Then assert equality.

The value is entirely in the independence. A check that reads the same
intermediate the number was built from will agree with anything.

**The case.** `_run_cafa_grid_artifact._eligible` asserts that the evaluation
kernel's own eligibility mask and the producer's `n_gt > 0` select the same
rows. Two modules, two code paths, one required equality. When `cafaeval` was
changed upstream, that check was the thing that could still fire, and the gate
next to it, `_check_pooled`, was retired precisely because after the change it
could no longer fire at all.

**What it costs to skip.** The pooled sums defect lived in a published metric
for the length of a campaign. It was found by recomposing `f_micro_w` from the
kept rows and finding 1.0 where the frame published 0.8824.

---

## 2. Publish the first number with enough breakdown that someone else can collide it

A single summary figure cannot be collided by anyone. Publish the counts, the
denominators, the per-cell populations and the direction of the comparison, and
a reader who disagrees can say so with arithmetic instead of with an opinion.

This is the rule that makes rule 1 work at a distance, across two machines and
across days.

**The cases, all of them mine.**

- I reported NOT propagation as a "2.5x understatement". The 2.5 came from
  comparing denials against pairs, which are different objects. The real figure
  is 465 to 527 denials, plus 13 per cent. Caught by the other machine, from the
  breakdown, within the hour.
- I reported a per-protein rule at `+0.0514`. It was one artefact with no
  cross-fit. Run properly, the median was `+0.0136`, four times smaller.
- I wrote that "abstention is a property of short candidate lists". Measured:
  17.8 per cent against 18.4. Identical.

None of those survived contact with their own breakdown. All three would have
survived indefinitely as summary figures.

---

## 3. A deduction from a definition is not a measurement

If the conclusion arrives by reasoning from what a thing is defined to be, it
has the same standing as a hypothesis and needs colliding exactly like a number
does.

The specific trap: **a correct definition can group two distinct things.** The
reasoning is valid, the definition is right, and the conclusion is still false,
because the definition covers a case the reasoner was not picturing. Only a
constructed minimal case separates them, and constructing it is the work.

**The cases.**

- Two different sets are both called "experimental" in this codebase.
  `evidence_codes.EXPERIMENTAL` is thirteen codes and includes IC and TAS;
  `ia_regimes.EXPERIMENTAL_EVIDENCE` is six. Every sentence saying
  "experimental" is ambiguous until it says which.
- Four statistics are all called F. `fmax` and `fmax_w` average per protein;
  `f_micro` and `f_micro_w` pool. And "macro unweighted" further splits into
  F-of-means and mean-of-F, which are not interchangeable.
- I deduced that ancestor closure equals additions for no-knowledge proteins.
  It is false, and I had measured the 93 per cent figure that refutes it myself,
  hours earlier.
- The "obvious" hard negative for an ontology encoder, a parent paired with a
  sibling of its child, is a TRUE subsumption 78 per cent of the time. It looks
  false by construction and is not.

**How to discharge it.** Build the smallest case where the two things the
definition groups would differ, and run it. If you cannot build one, say the
claim is a deduction and has not been collided, in the sentence that makes it.

---

## 4. A negative check only counts if you looked where the thing would be if it existed

"I checked and found nothing" is worth exactly as much as the reach of the
check. A search in the wrong place, at the wrong time, or over the wrong
population returns the same clean zero as a search that genuinely found nothing,
and the two are indistinguishable from the output.

So state where you looked, and satisfy yourself that the thing would have been
there.

**The cases.**

- A sparse-code module's entire test suite was green while the model collapsed
  in training. Every assertion ran at initialisation and the collapse happens
  under gradient. Measured both ways afterwards: the tests that existed are 8
  green against the broken module; the tests that look during training are 4
  red against the same module.
- With too few atoms, containment in that same module becomes *symmetric*,
  which is the one property it exists to provide, and a symmetric containment
  passes every other assertion in the file.
- Today, waiting on CI, I read "0 checks pending" and called a pull request
  green. It was zero pending out of a list GitHub had not created yet. A count
  of an empty set, read as a verdict.
- `own_k` was declared in a config, recorded where a reader would trust it, and
  never governed the computation. That is the fourth instance in this project of
  the same class: a parameter accepted, recorded, and inert.

**The shape to distrust.** A zero, a green suite, an empty diff, a control that
passes. Each is evidence only if the check could have failed. Say out loud what
would have made it fail.

---

## 5. Look at the distribution before the summary

The mean, the median and the headline are all summaries of a shape you have not
looked at. Look at the shape first. It is cheap and it repeatedly says the
opposite of the summary.

**The cases.**

- I hypothesised that the deployed system emits far too much. At the median it
  is false: the excess runs 0.6x to 2.0x. But the top decile emits 182 terms
  against a median of 10 **at the same ground-truth mass**, with recall 0.75
  against 0.29. There is no "the system emits too much". There is a tail.
- Depth is monotone in 70 of 72 series and the winner is always the edge, so
  there is no optimum to find. A summary reporting a best depth would have been
  reporting the boundary of the sweep.
- A generative descent lost to a top-1 frequency prior at 0.0987 against 0.1640.
  The summary says "the generator is worse". The distribution says recall is
  identical, 0.2202 against 0.2219, and precision is exactly half. Those are two
  different problems and only one of them is visible in the summary.

---

## Using this

Before a number leaves the machine that produced it, it should be able to
answer:

1. What is the second computation that must agree with this, and does it?
2. Is the breakdown published, or only the figure?
3. Which parts of this are deduced rather than measured, and are they marked?
4. For every negative or zero here, where did I look, and would it have been
   there?
5. Have I looked at the distribution, or only at its summary?

Five questions, not a process. If the answer to any of them is uncomfortable,
that discomfort is the finding, and it is cheaper now than after the number has
been cited.

None of this applies to exploration. Look at whatever you like, guess freely,
run the wrong thing on purpose. It applies at the moment a number is written
down somewhere another person or another machine will read it as true.

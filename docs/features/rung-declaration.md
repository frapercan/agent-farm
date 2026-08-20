---
name: rung-declaration
section: "12-ci-gates"
state: working
owner: agent-farm conductor loop
source:
  - .github/workflows/rung-declaration.yml
  - plans/rungs.yaml
  - scripts/check_rung_declaration.py
runbook: plans/CAMPAIGN.md
smoke: python3 scripts/check_rung_declaration.py
---

# rung-declaration

Pull-request gate that makes the experimental ladder a claim something can
refuse.

`plans/CAMPAIGN.md` section 5 declares five rungs, each with one question
and one gate. It has been right and unread. On 2026-08-19 a grid ran 48
arms of the declared rung 1 while varying two of its three axes, the third
pinned by omission to the weakest available scorer; four hundred jobs were
then tagged with a rung number invented at dispatch time. Nothing objected
to either, because prose cannot refuse a job.

`plans/rungs.yaml` carries the same ladder in a form a script can read, and
this gate checks it.

## Source coordinates

- `.github/workflows/rung-declaration.yml`
- `plans/rungs.yaml`
- `scripts/check_rung_declaration.py`
- `tests/test_rung_declaration.py`

## What it refuses

- A rung missing any of question, axes, held constants, gate, winner scope
  or status.
- A **dependency pointing upwards**. Each rung names the rung that decided
  each constant it holds, so rung N's held values are rung N-1's answers.
  A ladder standing on its own shoulders would not propagate an answer
  that later changed.
- A constant **held anonymously**, with nobody named as having decided it.
  That is a constant nobody can invalidate.
- An axis with **no field**, or a null field with no note saying why it
  cannot be checked against a job. An unnamed axis is a wish.
- A rung **parked without a reason**. Six weeks later, a rung nobody got to
  and a rung somebody decided against look identical.

## What it does not do yet

The runtime half. A dispatched job declaring `rung: N` should be refused
when the axes it actually varies contradict rung N's declaration, and that
check needs the job table, so it belongs in PROTEA rather than here. Until
it exists this gate protects the declaration and not the dispatch, which is
the half that failed on 2026-08-19.

## State

working. Runs on pull requests touching the declaration, the checker, its
tests or the workflow. Two steps: the checker over the shipped ladder, then
the test suite that covers what the checker must catch. Each test is a
thing that happened or nearly did, not a hypothetical.

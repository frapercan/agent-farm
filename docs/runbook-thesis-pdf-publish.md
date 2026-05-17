# Runbook: thesis PDF publish via deploy-keeper (FARM-1.8)

## What this does

`protea.ngrok.app/thesis.pdf` serves the doctoral thesis PDF for
external readers (co-supervisors, reviewers, the user himself when on
mobile). The PDF is a build artefact, NOT a tracked file in the thesis
repo (PR #30 untracked it on 2026-05-12 to stop parallel thesis-writer
PRs from cascading DIRTY on the binary).

The deploy-keeper service rebuilds the PDF from `origin/main` of the
thesis repo and copies it to the deploy worktree on every tick. The
Next.js static-file middleware at `apps/web/public/` then serves it.

## Components

| Component | Path | Role |
| --- | --- | --- |
| Publisher | `scripts/services/lib/protea_thesis_pdf_publish.sh` | Builds + atomically copies the PDF |
| Caller | `scripts/services/deploy-keeper-tick.sh` step 3 | Invokes the publisher each tick |
| Publish worktree | `~/Thesis2/worktrees/_thesis-publish/` | Detached git worktree of `thesis@origin/main`; auto-bootstrapped |
| Marker | `agent-farm/state/thesis_pdf_published.sha` | Last successfully published commit; idempotency guard |
| Build log | `agent-farm/state/logs/thesis_pdf_build.log` | Last latexmk stdout/stderr (truncated to last build) |
| Publish log | `agent-farm/state/logs/thesis_pdf_publish.log` | All publisher activity (rotating append) |
| Served file | `~/Thesis2/worktrees/protea-deploy/apps/web/public/thesis.pdf` | What Next.js serves |
| Public URL | `https://protea.ngrok.app/thesis.pdf` | What humans hit |

## Happy-path tick

1. `deploy-keeper-tick.sh` finishes the docker redeploy + ngrok ensure.
2. It invokes `protea_thesis_pdf_publish.sh`.
3. The publisher fetches `origin/main` of the thesis repo.
4. If `origin/main` matches the marker SHA, it returns 0 immediately
   (no latex rebuild). Cost: 1 fetch, ~50ms.
5. Otherwise it hard-resets the publish worktree to `origin/main`,
   runs `latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error`,
   copies `thesis.pdf` to the deploy public dir atomically, and updates
   the marker.

## When the PDF stops updating

### Symptom: `protea.ngrok.app/thesis.pdf` is older than the latest thesis commit on `main`

1. Check the publish log:
   ```bash
   tail -50 ~/Thesis2/agent-farm/state/logs/thesis_pdf_publish.log
   ```
2. Compare published SHA to remote HEAD:
   ```bash
   cat ~/Thesis2/agent-farm/state/thesis_pdf_published.sha
   git -C ~/Thesis2/thesis rev-parse origin/main
   ```
   If equal, the publisher is doing the right thing and the served PDF
   matches the source. Likely the ngrok layer is caching; force-refresh
   with `curl -I https://protea.ngrok.app/thesis.pdf`.

3. If unequal, look at the most recent build log:
   ```bash
   tail -40 ~/Thesis2/agent-farm/state/logs/thesis_pdf_build.log
   ```
   Common failures:
   - `! LaTeX Error: File ... not found` (a new include path; thesis-writer
     forgot to add a figure source file)
   - em-dash linter / bibtex / glossary errors

### Symptom: deploy-keeper logs `thesis PDF publish: skipped`

The publisher returned 2 (environment). Causes:
- `latexmk` not installed on the host.
- `~/Thesis2/worktrees/protea-deploy/apps/web/public/` is missing (deploy
  worktree was wiped; see `feedback_deploy_worktree_bootstrap.md`).
  The parent redeploy step in the tick should recreate the deploy
  worktree first; if it does not, fix that separately and the next
  tick will publish.
- `~/Thesis2/thesis/.git` is missing (thesis clone was deleted).

### Manual force-publish

```bash
rm -f ~/Thesis2/agent-farm/state/thesis_pdf_published.sha
AGENT_FARM_ROOT=~/Thesis2/agent-farm \
  bash ~/Thesis2/agent-farm/scripts/services/lib/protea_thesis_pdf_publish.sh
```

The next deploy-keeper tick (default 5 min) will also do this without
the manual rm, as long as `origin/main` has advanced.

### Hard reset of the publish worktree

The publisher hard-resets `~/Thesis2/worktrees/_thesis-publish/` on every
non-noop build, so manual edits there are pointless. If the worktree
itself is broken, delete it; the publisher will recreate it from
`origin/main`:

```bash
git -C ~/Thesis2/thesis worktree remove --force ~/Thesis2/worktrees/_thesis-publish
# next publisher invocation will bootstrap a fresh one
```

## Why deploy-keeper, not GitHub Actions

The thesis repo's `.github/workflows/build.yml` does build the PDF on
every PR and uploads it as an artefact (`thesis-pdf`, 30-day retention).
That artefact is for review purposes; it is NOT what
`protea.ngrok.app/thesis.pdf` serves. The deploy-keeper publish path
keeps the served PDF in lock-step with the rest of the stack (the same
service that publishes the docs portal and ngrok tunnel), so there is
one source of truth for "what's live".

## Operational verification

After both this slice's PRs merge, run on the host:

1. Trigger one publish manually to confirm the wiring:
   ```bash
   rm -f ~/Thesis2/agent-farm/state/thesis_pdf_published.sha
   AGENT_FARM_ROOT=~/Thesis2/agent-farm \
     bash ~/Thesis2/agent-farm/scripts/services/lib/protea_thesis_pdf_publish.sh
   ```
   Expect: `OK published <short-sha> (<bytes>) to .../apps/web/public/thesis.pdf`.

2. Confirm the served URL returns the freshly built PDF (size should
   match the local copy):
   ```bash
   curl -sI https://protea.ngrok.app/thesis.pdf | grep -i content-length
   stat -c%s ~/Thesis2/worktrees/protea-deploy/apps/web/public/thesis.pdf
   ```

3. (Optional, follow-up) Spawn 3 parallel thesis-writer agents on
   different smoke-chapter edits. Verify that none of them cascade
   DIRTY on `thesis.pdf` after the first PR merges.

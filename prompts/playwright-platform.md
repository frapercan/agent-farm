# playwright-platform

You e2e test the PROTEA platform UI — the Next.js app at
`~/Thesis2/repositories/PROTEA/apps/web/` — running live at
`https://protea.ngrok.app/en/` (the platform root; i18n default locale).
Reuse the project's existing playwright config, do NOT reinvent.

## Targets (resolved at run time, ask conductor if unclear)

- Live deploy: `https://protea.ngrok.app` (public, served by deploy-keeper)
- Platform routes (Next.js, what you test): `/en/`, `/en/jobs/`,
  `/en/farm/`, `/en/farm/<id>/`, `/en/farm/plan/`, `/en/farm/cost/`, and
  any sub-routes discovered by inspecting `apps/web/app/` directory
  structure
- NOT your concern: `/sphinx/` (Sphinx docs portal, different stack) and
  `/thesis.pdf` (static PDF). Those have separate health checks.
- Existing spec files (in your worktree): `apps/web/e2e/mobile-check.spec.ts`,
  `apps/web/e2e/tablet-check.spec.ts`,
  `apps/web/e2e/farm-mobile.spec.ts` (FARM-UI.8, mobile 390x844 farm coverage),
  `apps/web/e2e/farm-tablet.spec.ts` (FARM-UI.8, tablet 768x1024 farm coverage)

## Workflow

### 1. Setup (in your ephemeral worktree)

```bash
cd apps/web
npm ci --silent           # install playwright + Next deps; fast if cache warm
npx playwright install chromium --with-deps 2>&1 | tail -3
```

### 2. Override baseURL to hit the live deploy

```bash
export PLAYWRIGHT_BASE_URL=https://protea.ngrok.app
```

The existing `playwright.config.ts` has `baseURL: "http://localhost:3000"`
hardcoded. Either:
- (preferred) edit it temporarily in your worktree to read from
  `process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000"` and pass via env
- OR pass `--config` with a small override file you write in your worktree

### 3. Run

```bash
npx playwright test --reporter=json,list \
  --output=test-results \
  > playwright-output.json 2> playwright-stderr.log
RC=$?

# FARM-UI.8 — emit a single heartbeat with level=warn into the events
# table whenever playwright exits non-zero, so the agent-farm
# dashboard surfaces a red dot without operator polling. TASK_ID is
# injected by the conductor when spawning this subagent.
if [ "$RC" -ne 0 ]; then
  FAIL_SUMMARY=$(grep -E "^\s*[0-9]+ failed" playwright-output.json 2>/dev/null \
    | head -1 \
    | tr -d '\n' \
    || echo "playwright exit=$RC")
  python3 "$AGENT_FARM_ROOT/scripts/lib/db.py" heartbeat "$TASK_ID" warn \
    "playwright-platform: ${FAIL_SUMMARY:-non-zero exit ($RC)}"
fi
```

The heartbeat call also writes a row into the `events` table (kind=
`heartbeat`, level=`warn`) via the shared `_emit_event` helper in
`scripts/lib/db.py` — the FARM-2.1 events table is the canonical fan-out
sink consumed by `events_view.py` and the Grafana dashboard added in
FARM-UI.7a.

### 4. Parse the JSON report and summarize

Pull from `playwright-output.json`:
- Total / passed / failed per project (mobile, tablet)
- For each failure: spec file, test name, error message, screenshot path

Also collect screenshots from `apps/web/test-results/` and reference them in
your report (paths only, don't paste binary).

### 5. Report

Return a summary like:

```
playwright-platform smoke @ <ts>
Target: https://protea.ngrok.app/en/
Specs: mobile-check.spec.ts (3 tests), tablet-check.spec.ts (2 tests)

Results:
- mobile  : 3/3 passed
- tablet  : 1/2 passed (1 failed)

Failures:
- tablet/tablet-check.spec.ts › "jobs list renders" — timed out waiting
  for selector .jobs-row (5s) on /en/jobs/. Screenshot:
  test-results/tablet-jobs-list/screenshot.png

Recommendation: <next-step suggestion if there are failures>
```

If everything passes:

```
playwright-platform smoke @ <ts>
Target: https://protea.ngrok.app/en/
Specs: 5/5 passed (mobile 3/3, tablet 2/2)
ALL OK
```

## Hard constraints

- Read-only on the live platform. Don't POST forms, don't trigger mutations.
  If a spec file has a destructive action, SKIP it and report.
- Stay inside ephemeral worktree. Don't leak edits back.
- If protea.ngrok.app is unreachable, halt + report — that's deploy-keeper's
  job, not yours.
- Cap total run time at ~10min. If specs hang, kill them with a timeout.

## Token discipline

Haiku, mechanical. The JSON report does the heavy lifting — your job is
to read it, summarize, and call out actionable failures. Don't paste raw
JSON. Don't speculate about root causes you can't verify.

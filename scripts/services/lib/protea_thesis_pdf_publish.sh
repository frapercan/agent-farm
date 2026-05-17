#!/usr/bin/env bash
# protea_thesis_pdf_publish.sh — Rebuild the thesis PDF from origin/main
# and publish it to the deploy worktree so protea.ngrok.app/thesis.pdf
# serves the freshest build on every deploy-keeper tick.
#
# This is the runtime publisher that closes FARM-1.8: thesis.pdf is now
# a build artefact in the thesis repo (PR #30 untracked it; PR #49
# documented the regen path). The deploy-keeper is the publisher.
#
# Design choices:
#   * A stable detached worktree at $THESIS_PUBLISH_DIR mirrors origin/main
#     of the thesis repo. We do NOT use ~/Thesis2/thesis (the developer's
#     workspace) and we do NOT clone-on-tick (costs disk + bandwidth).
#   * Idempotent: a marker file records the last successfully published
#     commit; if origin/main has not moved we skip the latex build.
#   * Build failure is NOT a hard tick failure. We log + return 1 so the
#     caller can heartbeat a warn and continue.
#
# Exit codes:
#   0   published OK (PDF copied to deploy worktree) or no-op (HEAD unchanged)
#   1   build attempted but failed (PDF unchanged, tick should NOT fail)
#   2   environment problem (missing latexmk, missing thesis clone, missing
#       deploy worktree). Caller should still continue (returns 1 here means
#       skip not fail).
#
# Required env (read-only): none. All paths overridable via env vars.

set -uo pipefail

AGENT_FARM_ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"

THESIS_SRC="${THESIS_SRC:-$HOME/Thesis2/thesis}"
THESIS_PUBLISH_DIR="${THESIS_PUBLISH_DIR:-$HOME/Thesis2/worktrees/_thesis-publish}"
DEPLOY_PATH="${PROTEA_DEPLOY_PATH:-$HOME/Thesis2/worktrees/protea-deploy}"
PUBLIC_DIR="${THESIS_PDF_PUBLIC_DIR:-$DEPLOY_PATH/apps/web/public}"
LOG_FILE="${THESIS_PDF_LOG:-$AGENT_FARM_ROOT/state/logs/thesis_pdf_publish.log}"
MARKER_FILE="${THESIS_PDF_MARKER:-$AGENT_FARM_ROOT/state/thesis_pdf_published.sha}"

mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$(dirname "$MARKER_FILE")"

ts() { date -Is; }
log() { printf '[%s] %s\n' "$(ts)" "$*" | tee -a "$LOG_FILE"; }

# Preflight: latex toolchain.
if ! command -v latexmk >/dev/null 2>&1; then
  log "ERR latexmk not installed; skipping thesis PDF publish"
  exit 2
fi

# Preflight: thesis source clone (we read git refs, never write).
if [[ ! -d "$THESIS_SRC/.git" ]]; then
  log "ERR thesis source not a git clone at $THESIS_SRC; skipping"
  exit 2
fi

# Preflight: deploy worktree public dir must exist. If the deploy
# worktree was wiped (cf. feedback_deploy_worktree_bootstrap memory)
# the redeploy step in the parent tick handles recreation; here we
# just refuse to fabricate a directory tree.
if [[ ! -d "$PUBLIC_DIR" ]]; then
  log "ERR public dir $PUBLIC_DIR missing; skipping (deploy worktree not bootstrapped?)"
  exit 2
fi

# Ensure the thesis-publish worktree exists. Detached so it never
# conflicts with whatever branch the developer has out in $THESIS_SRC.
if [[ ! -d "$THESIS_PUBLISH_DIR/.git" && ! -f "$THESIS_PUBLISH_DIR/.git" ]]; then
  log "bootstrap: creating detached publish worktree at $THESIS_PUBLISH_DIR"
  if ! git -C "$THESIS_SRC" worktree add --detach "$THESIS_PUBLISH_DIR" origin/main >>"$LOG_FILE" 2>&1; then
    log "ERR could not create publish worktree"
    exit 2
  fi
fi

# Sync the publish worktree to origin/main HEAD without touching the
# developer's working tree in $THESIS_SRC.
if ! git -C "$THESIS_SRC" fetch --quiet origin main >>"$LOG_FILE" 2>&1; then
  log "ERR fetch origin main failed"
  exit 1
fi

REMOTE_SHA=$(git -C "$THESIS_SRC" rev-parse origin/main 2>/dev/null || true)
if [[ -z "$REMOTE_SHA" ]]; then
  log "ERR could not resolve origin/main of thesis"
  exit 1
fi

# Idempotency: if last-published marker matches origin/main and the
# published PDF still exists, skip the (expensive) latex build.
PUBLISHED_PDF="$PUBLIC_DIR/thesis.pdf"
if [[ -f "$MARKER_FILE" && -f "$PUBLISHED_PDF" ]]; then
  LAST_SHA=$(cat "$MARKER_FILE" 2>/dev/null | tr -d '[:space:]')
  if [[ "$LAST_SHA" == "$REMOTE_SHA" ]]; then
    log "noop on $REMOTE_SHA (marker matches published PDF)"
    exit 0
  fi
fi

# Hard-reset the publish worktree to origin/main. We use reset --hard
# because this worktree is owned by the publisher; no human work lives here.
if ! git -C "$THESIS_PUBLISH_DIR" fetch --quiet origin main >>"$LOG_FILE" 2>&1; then
  log "ERR fetch in publish worktree failed"
  exit 1
fi
if ! git -C "$THESIS_PUBLISH_DIR" reset --hard "$REMOTE_SHA" >>"$LOG_FILE" 2>&1; then
  log "ERR reset --hard $REMOTE_SHA in publish worktree failed"
  exit 1
fi
# Drop any stray build artefacts from prior failed builds so we never
# publish a stale partial PDF.
git -C "$THESIS_PUBLISH_DIR" clean -fdx -e .git >>"$LOG_FILE" 2>&1 || true

log "rebuilding thesis PDF at $(git -C "$THESIS_PUBLISH_DIR" rev-parse --short HEAD)"

# Build the PDF. The thesis Makefile target `all` runs pdflatex + biber
# + makeglossaries + 2x pdflatex; latexmk -pdf reproduces the same with
# auto-rerun until convergence. We prefer latexmk because the CI workflow
# in thesis/.github/workflows/build.yml uses the same incantation, which
# keeps local builds and CI builds reproducible.
BUILD_LOG="$AGENT_FARM_ROOT/state/logs/thesis_pdf_build.log"
mkdir -p "$(dirname "$BUILD_LOG")"
if ! ( cd "$THESIS_PUBLISH_DIR" && \
       latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error \
               -file-line-error thesis.tex ) >"$BUILD_LOG" 2>&1; then
  log "ERR latex build failed (see $BUILD_LOG, last 5 lines below)"
  tail -5 "$BUILD_LOG" 2>/dev/null | sed 's/^/  /' | tee -a "$LOG_FILE"
  exit 1
fi

if [[ ! -f "$THESIS_PUBLISH_DIR/thesis.pdf" ]]; then
  log "ERR build returned 0 but thesis.pdf is missing"
  exit 1
fi

# Atomic publish: write to a temp file in the same dir, then rename.
# Avoids serving a half-written PDF if the cp gets interrupted.
TMP="$PUBLIC_DIR/.thesis.pdf.$$"
if ! cp "$THESIS_PUBLISH_DIR/thesis.pdf" "$TMP"; then
  log "ERR could not copy PDF to $TMP"
  rm -f "$TMP"
  exit 1
fi
if ! mv -f "$TMP" "$PUBLISHED_PDF"; then
  log "ERR could not rename $TMP to $PUBLISHED_PDF"
  rm -f "$TMP"
  exit 1
fi

# Record successful publish.
printf '%s' "$REMOTE_SHA" > "$MARKER_FILE"

BYTES=$(stat -c%s "$PUBLISHED_PDF" 2>/dev/null || echo "?")
log "OK published $(git -C "$THESIS_PUBLISH_DIR" rev-parse --short HEAD) (${BYTES} bytes) to $PUBLISHED_PDF"
exit 0

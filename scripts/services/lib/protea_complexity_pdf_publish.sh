#!/usr/bin/env bash
# protea_complexity_pdf_publish.sh — Build the complexity companion paper PDF
# from the LOCAL complexity-paper repo (pinned to its latest annotated tag)
# and publish it to the deploy worktree so protea.ngrok.app/complexity.pdf
# is served alongside /thesis.pdf.
#
# This closes FARM-DEPLOY.2. The source repo has NO git remote; we resolve
# the latest annotated tag locally via `git describe --tags --abbrev=0` and
# check it out into a stable detached worktree so the developer's working
# tree in ~/Thesis2/complexity-paper is never disturbed.
#
# Design (mirrors protea_thesis_pdf_publish.sh / FARM-1.8):
#   * A stable detached worktree at $COMPLEXITY_PUBLISH_DIR is checked out
#     at the latest annotated tag commit. We recreate it only when the tag
#     has advanced since the last publish.
#   * Idempotent: the marker file records the last-published tag commit SHA;
#     if the tag has not moved we skip the latex build (noop).
#   * Build failure is NOT a hard tick failure. We return 1 so the caller
#     can heartbeat a warn and continue.
#   * No `git fetch` is attempted (repo has no remote).
#
# Exit codes:
#   0   published OK or noop (tag unchanged + PDF already on disk)
#   1   build attempted but failed (prior PDF unchanged; tick MUST NOT fail)
#   2   environment problem (missing latexmk, missing source repo, missing
#       deploy worktree). Caller should still continue.
#
# Required env (all overridable):
#   COMPLEXITY_SRC          path to the local complexity-paper git repo
#   COMPLEXITY_PUBLISH_DIR  stable detached worktree for publisher
#   PROTEA_DEPLOY_PATH      root of the deploy worktree
#   COMPLEXITY_PDF_PUBLIC_DIR  override for the public dir (rarely needed)
#   AGENT_FARM_ROOT         agent-farm root (for logs + state)

set -uo pipefail

AGENT_FARM_ROOT="${AGENT_FARM_ROOT:-$HOME/Thesis2/agent-farm}"

COMPLEXITY_SRC="${COMPLEXITY_SRC:-$HOME/Thesis2/complexity-paper}"
COMPLEXITY_PUBLISH_DIR="${COMPLEXITY_PUBLISH_DIR:-$HOME/Thesis2/worktrees/_complexity-publish}"
DEPLOY_PATH="${PROTEA_DEPLOY_PATH:-$HOME/Thesis2/worktrees/protea-deploy}"
PUBLIC_DIR="${COMPLEXITY_PDF_PUBLIC_DIR:-$DEPLOY_PATH/apps/web/public}"
LOG_FILE="${COMPLEXITY_PDF_LOG:-$AGENT_FARM_ROOT/state/logs/complexity_pdf_publish.log}"
MARKER_FILE="${COMPLEXITY_PDF_MARKER:-$AGENT_FARM_ROOT/state/complexity_pdf_published.sha}"

mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$(dirname "$MARKER_FILE")"

ts() { date -Is; }
log() { printf '[%s] %s\n' "$(ts)" "$*" | tee -a "$LOG_FILE"; }

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------

if ! command -v latexmk >/dev/null 2>&1; then
  log "ERR latexmk not installed; skipping complexity PDF publish"
  exit 2
fi

if [[ ! -d "$COMPLEXITY_SRC/.git" ]]; then
  log "ERR complexity-paper source not a git repo at $COMPLEXITY_SRC; skipping"
  exit 2
fi

if [[ ! -d "$PUBLIC_DIR" ]]; then
  log "ERR public dir $PUBLIC_DIR missing; skipping (deploy worktree not bootstrapped?)"
  exit 2
fi

# ---------------------------------------------------------------------------
# Resolve latest annotated tag (no remote; purely local)
# ---------------------------------------------------------------------------

# We want the globally latest annotated tag across all refs. Sort by
# version semantics first (--sort=-version:refname) so v1.10 > v1.9 > v1.0,
# then break ties by creatordate. We use two-pass: sort by creatordate to
# break exact version ties, then sort by version refname (git processes
# multi-sort left-to-right, last key wins in descending).
# Practical effect: newest semantic version is selected; within same version
# string the most recently created tag wins.
LATEST_TAG=$(git -C "$COMPLEXITY_SRC" tag \
               --sort=-creatordate \
               --sort=-version:refname \
               --format='%(refname:short)' \
               2>/dev/null | head -1)

if [[ -z "$LATEST_TAG" ]]; then
  log "ERR no annotated or lightweight tags found in $COMPLEXITY_SRC; skipping"
  exit 2
fi

# Dereference the tag to its underlying commit SHA.
TAG_COMMIT=$(git -C "$COMPLEXITY_SRC" rev-parse "${LATEST_TAG}^{commit}" 2>/dev/null || true)
if [[ -z "$TAG_COMMIT" ]]; then
  log "ERR could not resolve tag $LATEST_TAG to a commit; skipping"
  exit 2
fi

log "complexity-paper latest tag: $LATEST_TAG ($TAG_COMMIT)"

# ---------------------------------------------------------------------------
# Idempotency: skip if marker matches the tag commit and PDF exists
# ---------------------------------------------------------------------------

PUBLISHED_PDF="$PUBLIC_DIR/complexity.pdf"
if [[ -f "$MARKER_FILE" && -f "$PUBLISHED_PDF" ]]; then
  LAST_SHA=$(cat "$MARKER_FILE" 2>/dev/null | tr -d '[:space:]')
  if [[ "$LAST_SHA" == "$TAG_COMMIT" ]]; then
    log "noop on $LATEST_TAG ($TAG_COMMIT) (marker matches published PDF)"
    exit 0
  fi
fi

# ---------------------------------------------------------------------------
# Ensure the complexity-publish worktree exists (detached at tag commit)
# ---------------------------------------------------------------------------

# A worktree has a .git file (not dir) when created via `git worktree add`.
if [[ ! -d "$COMPLEXITY_PUBLISH_DIR/.git" && ! -f "$COMPLEXITY_PUBLISH_DIR/.git" ]]; then
  log "bootstrap: creating detached publish worktree at $COMPLEXITY_PUBLISH_DIR (tag $LATEST_TAG)"
  if ! git -C "$COMPLEXITY_SRC" worktree add --detach "$COMPLEXITY_PUBLISH_DIR" "$TAG_COMMIT" >>"$LOG_FILE" 2>&1; then
    log "ERR could not create publish worktree"
    exit 2
  fi
fi

# Hard-reset the publish worktree to the tag commit. We own this worktree;
# no human work lives here.
if ! git -C "$COMPLEXITY_PUBLISH_DIR" reset --hard "$TAG_COMMIT" >>"$LOG_FILE" 2>&1; then
  log "ERR reset --hard $TAG_COMMIT in publish worktree failed"
  exit 1
fi

# Drop stray build artefacts from prior failed builds so we never serve a
# stale partial PDF.
git -C "$COMPLEXITY_PUBLISH_DIR" clean -fdx -e .git >>"$LOG_FILE" 2>&1 || true

SHORT=$(git -C "$COMPLEXITY_PUBLISH_DIR" rev-parse --short HEAD 2>/dev/null || echo "${TAG_COMMIT:0:7}")
log "rebuilding complexity PDF at tag $LATEST_TAG ($SHORT)"

# ---------------------------------------------------------------------------
# Build the PDF via the Makefile pdf target
# The Makefile runs: latexmk -pdf -interaction=nonstopmode -halt-on-error
#   -bibtex main.tex && cp main.pdf complexity.pdf
# ---------------------------------------------------------------------------

BUILD_LOG="$AGENT_FARM_ROOT/state/logs/complexity_pdf_build.log"
mkdir -p "$(dirname "$BUILD_LOG")"
if ! ( cd "$COMPLEXITY_PUBLISH_DIR" && make pdf ) >"$BUILD_LOG" 2>&1; then
  log "ERR latex build failed (see $BUILD_LOG, last 5 lines below)"
  tail -5 "$BUILD_LOG" 2>/dev/null | sed 's/^/  /' | tee -a "$LOG_FILE"
  exit 1
fi

if [[ ! -f "$COMPLEXITY_PUBLISH_DIR/complexity.pdf" ]]; then
  log "ERR build returned 0 but complexity.pdf is missing"
  exit 1
fi

# ---------------------------------------------------------------------------
# Atomic publish: write to temp then rename to avoid a partial read window
# ---------------------------------------------------------------------------

TMP="$PUBLIC_DIR/.complexity.pdf.$$"
if ! cp "$COMPLEXITY_PUBLISH_DIR/complexity.pdf" "$TMP"; then
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
printf '%s' "$TAG_COMMIT" > "$MARKER_FILE"

BYTES=$(stat -c%s "$PUBLISHED_PDF" 2>/dev/null || echo "?")
log "OK published $LATEST_TAG ($SHORT) (${BYTES} bytes) to $PUBLISHED_PDF"
exit 0

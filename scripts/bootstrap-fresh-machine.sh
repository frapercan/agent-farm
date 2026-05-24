#!/usr/bin/env bash
# bootstrap-fresh-machine.sh — idempotent installer for the PROTEA dev stack on Ubuntu/Debian.
#
# What it installs (skips steps already present):
#   - build-essential + curl + git + gnupg + ca-certificates + lsb-release
#   - postgresql-client (psql)
#   - Python 3.12 (via deadsnakes PPA on Ubuntu; Debian bookworm+ ships it natively)
#   - pip / pipx
#   - Poetry (via pipx)
#   - Node.js 20 (via NodeSource)
#   - npm (bundled with Node)
#   - Docker Engine + Compose plugin (via Docker CE apt repo)
#   - ngrok (binary only; no auth token configured here)
#   - Terraform latest stable (HashiCorp apt repo)
#
# After install the script prints next-step guidance.
#
# Usage:
#   bash scripts/bootstrap-fresh-machine.sh
#   bash scripts/bootstrap-fresh-machine.sh --dry-run   # print plan, do nothing
#
# Re-running on an already-bootstrapped box is safe (no-op).

set -euo pipefail

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BOLD=$'\033[1m'
RESET=$'\033[0m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
RED=$'\033[0;31m'

log()    { echo "${GREEN}[bootstrap]${RESET} $*"; }
warn()   { echo "${YELLOW}[bootstrap][warn]${RESET} $*" >&2; }
err()    { echo "${RED}[bootstrap][error]${RESET} $*" >&2; }
banner() { echo; echo "${BOLD}==> $*${RESET}"; }

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  warn "dry-run mode: printing plan only, nothing will be installed."
fi

run() {
  if $DRY_RUN; then
    echo "  [dry-run] $*"
  else
    "$@"
  fi
}

# ---------------------------------------------------------------------------
# Distro guard
# ---------------------------------------------------------------------------

if [[ ! -f /etc/os-release ]]; then
  err "Cannot detect OS (/etc/os-release missing). Only Ubuntu/Debian are supported."
  exit 1
fi

# shellcheck source=/dev/null
source /etc/os-release
case "${ID:-}${ID_LIKE:-}" in
  *ubuntu*|*debian*)
    log "Detected distro: ${PRETTY_NAME:-$ID}"
    ;;
  *)
    err "Unsupported distro: ${PRETTY_NAME:-$ID}."
    err "This script targets Ubuntu 22.04+ / Debian 11+. Exiting."
    exit 1
    ;;
esac

DISTRO_ID="${ID}"
DISTRO_CODENAME="${VERSION_CODENAME:-$(lsb_release -cs 2>/dev/null || echo 'jammy')}"

# ---------------------------------------------------------------------------
# Root / sudo check
# ---------------------------------------------------------------------------

if [[ $EUID -eq 0 ]]; then
  SUDO=""
else
  if ! command -v sudo &>/dev/null; then
    err "Not running as root and sudo is not available. Cannot install packages."
    exit 1
  fi
  SUDO="sudo"
fi

# ---------------------------------------------------------------------------
# Step 0: apt housekeeping
# ---------------------------------------------------------------------------

banner "Step 0: apt update + base packages"

run $SUDO apt-get update -qq

BASE_PKGS=(
  build-essential
  curl
  git
  gnupg
  ca-certificates
  lsb-release
  software-properties-common
  apt-transport-https
  unzip
  jq
)

MISSING_BASE=()
for pkg in "${BASE_PKGS[@]}"; do
  if ! dpkg -s "$pkg" &>/dev/null; then
    MISSING_BASE+=("$pkg")
  fi
done

if [[ ${#MISSING_BASE[@]} -gt 0 ]]; then
  log "Installing base packages: ${MISSING_BASE[*]}"
  run $SUDO apt-get install -y -qq "${MISSING_BASE[@]}"
else
  log "Base packages already present."
fi

# ---------------------------------------------------------------------------
# Step 1: postgresql-client
# ---------------------------------------------------------------------------

banner "Step 1: postgresql-client (psql)"

if ! command -v psql &>/dev/null; then
  log "Installing postgresql-client..."
  run $SUDO apt-get install -y -qq postgresql-client
else
  log "psql already present: $(psql --version | head -1)"
fi

# ---------------------------------------------------------------------------
# Step 2: Python 3.12
# ---------------------------------------------------------------------------

banner "Step 2: Python 3.12"

if ! command -v python3.12 &>/dev/null; then
  log "Python 3.12 not found, installing..."
  if [[ "$DISTRO_ID" == "ubuntu" ]]; then
    # deadsnakes PPA — safe for Ubuntu only
    if ! grep -qr "deadsnakes" /etc/apt/sources.list.d/ 2>/dev/null; then
      log "Adding deadsnakes PPA..."
      run $SUDO add-apt-repository -y ppa:deadsnakes/ppa
      run $SUDO apt-get update -qq
    fi
  fi
  run $SUDO apt-get install -y -qq python3.12 python3.12-venv python3.12-dev python3-pip
else
  log "Python 3.12 already present: $(python3.12 --version)"
fi

# Ensure python3 default is 3.12 if older version exists
if command -v update-alternatives &>/dev/null && ! $DRY_RUN; then
  $SUDO update-alternatives --install /usr/bin/python3 python3 "$(command -v python3.12)" 100 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# Step 3: pipx + Poetry
# ---------------------------------------------------------------------------

banner "Step 3: pipx + Poetry"

if ! command -v pipx &>/dev/null; then
  log "Installing pipx..."
  run python3.12 -m pip install --user -q pipx
  # Ensure ~/.local/bin is on PATH for this session
  export PATH="$HOME/.local/bin:$PATH"
else
  log "pipx already present."
fi

if ! command -v poetry &>/dev/null; then
  log "Installing poetry via pipx..."
  run pipx install poetry
  export PATH="$HOME/.local/bin:$PATH"
else
  log "poetry already present: $(poetry --version)"
fi

# ---------------------------------------------------------------------------
# Step 4: Node.js 20 + npm
# ---------------------------------------------------------------------------

banner "Step 4: Node.js 20 + npm"

NODE_MAJOR=20

if ! command -v node &>/dev/null || [[ "$(node --version | cut -d. -f1 | tr -d 'v')" -lt "$NODE_MAJOR" ]]; then
  log "Installing Node.js ${NODE_MAJOR} via NodeSource..."
  NODESOURCE_SCRIPT="$(mktemp)"
  if ! $DRY_RUN; then
    curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" -o "$NODESOURCE_SCRIPT"
    $SUDO bash "$NODESOURCE_SCRIPT"
    rm -f "$NODESOURCE_SCRIPT"
    $SUDO apt-get install -y -qq nodejs
  else
    echo "  [dry-run] curl https://deb.nodesource.com/setup_${NODE_MAJOR}.x | sudo bash"
    echo "  [dry-run] sudo apt-get install -y nodejs"
  fi
else
  log "Node.js already present: $(node --version)"
fi

if ! command -v npm &>/dev/null; then
  log "npm not found, installing..."
  run $SUDO apt-get install -y -qq npm
else
  log "npm already present: $(npm --version)"
fi

# ---------------------------------------------------------------------------
# Step 5: Docker Engine + Compose plugin
# ---------------------------------------------------------------------------

banner "Step 5: Docker Engine + Compose plugin"

if ! command -v docker &>/dev/null; then
  log "Docker not found, installing Docker CE..."

  DOCKER_KEYRING=/etc/apt/keyrings/docker.gpg

  if ! $DRY_RUN; then
    $SUDO install -m 0755 -d /etc/apt/keyrings
    curl -fsSL "https://download.docker.com/linux/${DISTRO_ID}/gpg" \
      | $SUDO gpg --dearmor -o "$DOCKER_KEYRING"
    $SUDO chmod a+r "$DOCKER_KEYRING"

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=${DOCKER_KEYRING}] \
https://download.docker.com/linux/${DISTRO_ID} ${DISTRO_CODENAME} stable" \
      | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null

    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq \
      docker-ce docker-ce-cli containerd.io \
      docker-buildx-plugin docker-compose-plugin
  else
    echo "  [dry-run] would add Docker CE apt repo and install docker-ce + docker-compose-plugin"
  fi

  # Add current user to docker group (no-op if already member)
  if [[ $EUID -ne 0 ]]; then
    run $SUDO usermod -aG docker "$USER" || true
    warn "Added $USER to 'docker' group. Log out and back in for it to take effect."
  fi
else
  log "Docker already present: $(docker --version)"
fi

if ! docker compose version &>/dev/null 2>&1; then
  log "Docker Compose plugin not found, installing..."
  run $SUDO apt-get install -y -qq docker-compose-plugin
else
  log "Docker Compose plugin already present: $(docker compose version --short 2>/dev/null || true)"
fi

# ---------------------------------------------------------------------------
# Step 6: ngrok (binary install, no auth token)
# ---------------------------------------------------------------------------

banner "Step 6: ngrok"

if ! command -v ngrok &>/dev/null; then
  log "Installing ngrok..."
  NGROK_URL="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
  NGROK_TMP="$(mktemp -d)"
  if ! $DRY_RUN; then
    curl -fsSL "$NGROK_URL" -o "$NGROK_TMP/ngrok.tgz"
    tar -xzf "$NGROK_TMP/ngrok.tgz" -C "$NGROK_TMP"
    $SUDO install -m 0755 "$NGROK_TMP/ngrok" /usr/local/bin/ngrok
    rm -rf "$NGROK_TMP"
    log "ngrok installed. Configure auth token separately: ngrok authtoken <token>"
  else
    echo "  [dry-run] would download + install ngrok binary to /usr/local/bin/ngrok"
  fi
else
  log "ngrok already present: $(ngrok version 2>/dev/null || true)"
fi

# ---------------------------------------------------------------------------
# Step 7: Terraform (HashiCorp apt repo)
# ---------------------------------------------------------------------------

banner "Step 7: Terraform (latest stable)"

if ! command -v terraform &>/dev/null; then
  log "Installing Terraform..."
  HASHICORP_KEYRING=/etc/apt/keyrings/hashicorp-archive-keyring.gpg
  if ! $DRY_RUN; then
    $SUDO install -m 0755 -d /etc/apt/keyrings
    curl -fsSL "https://apt.releases.hashicorp.com/gpg" \
      | $SUDO gpg --dearmor -o "$HASHICORP_KEYRING"

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=${HASHICORP_KEYRING}] \
https://apt.releases.hashicorp.com ${DISTRO_CODENAME} main" \
      | $SUDO tee /etc/apt/sources.list.d/hashicorp.list >/dev/null

    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq terraform
  else
    echo "  [dry-run] would add HashiCorp apt repo and install terraform"
  fi
else
  log "Terraform already present: $(terraform version -json 2>/dev/null | jq -r '.terraform_version' 2>/dev/null || terraform version | head -1)"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

echo
echo "${BOLD}${GREEN}bootstrap done${RESET} -- next steps:"
echo "  1. Log out and back in so docker group membership takes effect."
echo "  2. Clone repos:"
echo "       mkdir -p ~/Thesis2/repositories"
echo "       for repo in PROTEA protea-method protea-backends protea-reranker-lab \\"
echo "                   protea-runners protea-sources protea-contracts cafaeval-protea; do"
echo "         git clone git@github.com:frapercan/\$repo ~/Thesis2/repositories/\$repo"
echo "       done"
echo "  3. Copy + edit secrets:"
echo "       mkdir -p ~/.secrets"
echo "       cp ~/Thesis2/repositories/PROTEA/.env.example ~/.secrets/protea.env"
echo "       chmod 600 ~/.secrets/protea.env"
echo "       # Edit ~/.secrets/protea.env with real credentials"
echo "       ln -s ~/.secrets/protea.env ~/Thesis2/repositories/PROTEA/.env"
echo "  4. Restore database backup (see scripts/restore-from-backup.sh from FARM-INFRA.3 if available):"
echo "       bash ~/Thesis2/agent-farm/scripts/restore-from-backup.sh --apply --yes"
echo "  5. Start the stack:"
echo "       set -a && source ~/.secrets/protea.env && set +a"
echo "       bash ~/Thesis2/repositories/PROTEA/manage.sh start"
echo "  6. Health-check:"
echo "       curl -sf http://localhost:8000/jobs && echo 'Stack up.'"

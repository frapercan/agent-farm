---
name: bootstrap-fresh-machine
section: "11-backup-recovery"
state: working
owner: agent-farm conductor loop
source:
  - scripts/bootstrap-fresh-machine.sh
runbook: docs/features/bootstrap-fresh-machine.md
smoke: bash -n scripts/bootstrap-fresh-machine.sh
---

# bootstrap-fresh-machine

Single idempotent bash script that turns a bare Ubuntu 22.04+ (or Debian 11+)
machine into a working PROTEA dev environment. Re-running it on an already
configured box is a no-op: every step is gated on `command -v <tool>` or
`dpkg -s <pkg>` before acting.

## What it installs

| Component | Version pinned | Method |
|-----------|---------------|--------|
| build-essential, curl, git, gnupg, ca-certificates | distro default | apt |
| postgresql-client (psql) | distro default | apt |
| Python | 3.12 | deadsnakes PPA (Ubuntu) / apt (Debian) |
| pipx | latest | pip install --user |
| Poetry | latest stable | pipx |
| Node.js | 20 | NodeSource setup script |
| npm | bundled with Node | apt |
| Docker Engine | latest CE | Docker apt repo |
| Docker Compose plugin | latest | Docker apt repo |
| ngrok | v3 stable | binary from equinox CDN |
| Terraform | latest stable | HashiCorp apt repo |

ngrok is installed as a binary only. No auth token is configured by the
script; that is a post-install step requiring a personal account token.

## When to use it

- Provisioning a new developer workstation or a fresh VM for reproducibility.
- After a complete OS reinstall on the thesis machine.
- CI/CD pre-flight on a blank runner image (use `--dry-run` to verify the
  plan first).

## Usage

```bash
# Full install (requires sudo for apt steps)
bash scripts/bootstrap-fresh-machine.sh

# Print what would happen without changing anything
bash scripts/bootstrap-fresh-machine.sh --dry-run
```

## Post-bootstrap ceremony

After the script completes, follow these steps in order:

### 1. Re-login (docker group)

The script adds your user to the `docker` group. The change only takes effect
after you log out and back in (or run `newgrp docker`).

### 2. Clone the 8 repositories

```bash
mkdir -p ~/Thesis2/repositories
for repo in PROTEA protea-method protea-backends protea-reranker-lab \
            protea-runners protea-sources protea-contracts cafaeval-protea; do
  git clone git@github.com:frapercan/$repo ~/Thesis2/repositories/$repo
done
```

### 3. Configure secrets

The canonical secrets file lives outside any repo to prevent accidental leaks:

```bash
mkdir -p ~/.secrets
cp ~/Thesis2/repositories/PROTEA/.env.example ~/.secrets/protea.env
chmod 600 ~/.secrets/protea.env
# Edit ~/.secrets/protea.env: fill in JWT_SECRET, DB credentials, ngrok token, etc.
ln -s ~/.secrets/protea.env ~/Thesis2/repositories/PROTEA/.env
```

Important: AUTHN_REQUIRED defaults to true. If JWT_SECRET is missing the
stack aborts on startup (see project memory `project_stack_env_not_sourced_outage`).
Always source the env file before starting the stack:

```bash
set -a && source ~/.secrets/protea.env && set +a
```

### 4. Restore the database

If a pg_dump backup is available, restore it before starting the stack. When
FARM-INFRA.3 lands this is a one-liner:

```bash
bash ~/Thesis2/agent-farm/scripts/restore-from-backup.sh --apply --yes
```

Until then, restore manually:

```bash
# Find the newest dump
DUMP=$(ls -t ~/Thesis2/backups/protea-*.dump 2>/dev/null | head -1)
# Bring postgres up alone first
docker compose -f ~/Thesis2/repositories/PROTEA/docker-compose.yml up -d db
# Restore (takes ~28 min on first run; see project_db_volume_landmine)
pg_restore -h localhost -U protea -d protea "$DUMP"
# Run migrations
cd ~/Thesis2/repositories/PROTEA && poetry run alembic upgrade head
```

### 5. Start the stack

```bash
set -a && source ~/.secrets/protea.env && set +a
bash ~/Thesis2/repositories/PROTEA/manage.sh start
```

### 6. Health-check

```bash
curl -sf http://localhost:8000/jobs && echo "Stack up."
```

A 200 response confirms the API is running correctly.

## Idempotency guarantees

- Package installs: gated on `dpkg -s` / `command -v`.
- Apt repo additions: only added if the keyring file does not exist.
- User/group changes: `usermod -aG` is a no-op if membership already exists.
- No data is modified; no volumes are created by the bootstrap script itself.

## Current owner

agent-farm conductor loop (FARM-INFRA.2).

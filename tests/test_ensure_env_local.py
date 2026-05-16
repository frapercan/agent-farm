"""Tests for ensure_env_local() in scripts/services/lib/protea_redeploy.sh.

ensure_env_local is the self-seed helper that writes the deploy
worktree's .env.local with `export PROTEA_JWT_SECRET=...`. manage.sh
starts uvicorn via setsid + & so the env vars MUST be exported (not
shell-local). PROTEA's scripts/deploy.sh additionally does
`set -a; source .env.local; set +a` so plain KEY=VAL lines also work,
but the file must exist with sane content.

Cases covered:
  - file missing -> created with all three lines, mode 0600,
    generated secret
  - file present but missing `export ` prefix -> regenerated,
    preserving the existing secret value
  - file already correct -> idempotent no-op (mtime unchanged within
    1ms of the prior write); permissions left at original
"""

from __future__ import annotations

import os
import stat
import subprocess
import textwrap
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REDEPLOY_SH = REPO_ROOT / "scripts" / "services" / "lib" / "protea_redeploy.sh"


def _run_ensure_env_local(deploy_path: Path) -> subprocess.CompletedProcess:
    """Source protea_redeploy.sh in dry-source mode and invoke ensure_env_local.

    The script is normally end-to-end (refresh siblings -> redeploy). We
    only need the helper, so we source it under `__DRY_SOURCE=1` after
    short-circuiting the bottom of the file via a sentinel. The cheaper
    approach used here is: extract the function body into a temp script
    that re-defines just the variables ensure_env_local needs, then
    invoke the function. This decouples the test from sibling refresh +
    git fetch side effects.
    """
    helper = textwrap.dedent(
        f"""\
        #!/usr/bin/env bash
        set -uo pipefail
        DEPLOY_PATH={deploy_path!s}
        LOG_FILE=$(mktemp)
        ts() {{ date -Is; }}
        log() {{ printf '[%s] %s\\n' "$(ts)" "$*" >>"$LOG_FILE"; }}

        # Inline-extract ensure_env_local from the real script. We grep the
        # function definition + body (between `ensure_env_local() {{` and
        # the matching closing brace at column 0) so any drift in the real
        # script is caught here.
        eval "$(awk '/^ensure_env_local\\(\\) \\{{/,/^\\}}/' {REDEPLOY_SH!s})"

        ensure_env_local
        """
    )
    return subprocess.run(
        ["bash", "-c", helper], capture_output=True, text=True, check=False,
    )


@pytest.fixture
def deploy_dir(tmp_path: Path) -> Path:
    d = tmp_path / "protea-deploy"
    d.mkdir()
    return d


def _file_lines(p: Path) -> list[str]:
    return p.read_text().splitlines()


def _hex_secret(line: str) -> str:
    return line.split("=", 1)[1].strip()


class TestEnsureEnvLocal:
    def test_creates_file_when_missing(self, deploy_dir: Path) -> None:
        env = deploy_dir / ".env.local"
        assert not env.exists()

        res = _run_ensure_env_local(deploy_dir)
        assert res.returncode == 0, res.stderr

        assert env.exists()
        lines = _file_lines(env)
        assert any(l.startswith("export PROTEA_JWT_SECRET=") for l in lines)
        assert "export PROTEA_AUTHN_REQUIRED=true" in lines
        assert "export PROTEA_ADMIN_TOKEN=protea-admin" in lines

        secret_line = next(
            l for l in lines if l.startswith("export PROTEA_JWT_SECRET=")
        )
        secret = _hex_secret(secret_line)
        # openssl rand -hex 32 -> 64 hex chars
        assert len(secret) == 64
        assert all(c in "0123456789abcdefABCDEF" for c in secret)

    def test_file_mode_is_0600_when_created(self, deploy_dir: Path) -> None:
        env = deploy_dir / ".env.local"

        res = _run_ensure_env_local(deploy_dir)
        assert res.returncode == 0, res.stderr

        mode = stat.S_IMODE(env.stat().st_mode)
        assert mode == 0o600, f"got {oct(mode)}"

    def test_preserves_existing_secret_when_missing_export_prefix(
        self, deploy_dir: Path,
    ) -> None:
        env = deploy_dir / ".env.local"
        existing = "deadbeef" * 8  # 64 hex
        env.write_text(
            f"PROTEA_JWT_SECRET={existing}\n"
            "PROTEA_AUTHN_REQUIRED=true\n",
        )

        res = _run_ensure_env_local(deploy_dir)
        assert res.returncode == 0, res.stderr

        lines = _file_lines(env)
        secret_line = next(
            l for l in lines if l.startswith("export PROTEA_JWT_SECRET=")
        )
        assert _hex_secret(secret_line) == existing
        # Required and admin lines should now be there with export.
        assert "export PROTEA_AUTHN_REQUIRED=true" in lines
        assert "export PROTEA_ADMIN_TOKEN=protea-admin" in lines

    def test_idempotent_when_already_correct(self, deploy_dir: Path) -> None:
        env = deploy_dir / ".env.local"
        good = (
            "export PROTEA_JWT_SECRET=" + "ab" * 32 + "\n"
            "export PROTEA_AUTHN_REQUIRED=true\n"
            "export PROTEA_ADMIN_TOKEN=protea-admin\n"
        )
        env.write_text(good)
        os.chmod(env, 0o600)
        before_mtime = env.stat().st_mtime_ns
        before_content = env.read_text()

        # Sleep so a re-write would bump mtime perceptibly.
        time.sleep(0.05)

        res = _run_ensure_env_local(deploy_dir)
        assert res.returncode == 0, res.stderr

        after_mtime = env.stat().st_mtime_ns
        after_content = env.read_text()

        assert after_content == before_content, "content was rewritten"
        assert after_mtime == before_mtime, "mtime changed; not idempotent"

    def test_regenerates_when_secret_missing_entirely(
        self, deploy_dir: Path,
    ) -> None:
        env = deploy_dir / ".env.local"
        env.write_text("# pre-existing comment\nFOO=bar\n")

        res = _run_ensure_env_local(deploy_dir)
        assert res.returncode == 0, res.stderr

        lines = _file_lines(env)
        secret_line = next(
            l for l in lines if l.startswith("export PROTEA_JWT_SECRET=")
        )
        secret = _hex_secret(secret_line)
        assert len(secret) == 64

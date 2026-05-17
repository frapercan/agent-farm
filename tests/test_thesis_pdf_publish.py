"""Tests for scripts/services/lib/protea_thesis_pdf_publish.sh.

The publisher rebuilds the doctoral thesis PDF from the thesis repo's
origin/main and copies it into the deploy-keeper public dir on every
tick. Real latex builds are slow + need toolchain on CI, so these
tests stub `latexmk` via a `PATH` prefix that writes a fake thesis.pdf.

Coverage:
- happy path: builds + atomically publishes + writes marker
- noop when marker matches origin/main
- noop is robust when the published PDF still exists
- environment failures return 2 (missing latexmk; missing deploy dir;
  missing thesis clone) without crashing the parent tick
- build failure (stub latexmk exits non-zero) returns 1 and leaves the
  prior PDF untouched
"""

from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLISHER = REPO_ROOT / "scripts" / "services" / "lib" / "protea_thesis_pdf_publish.sh"


def _init_thesis_clone(thesis_src: Path, marker_text: str = "% smoke chapter\n") -> str:
    """Create a tiny git repo with a thesis.tex + a remote, return origin/main SHA."""
    upstream = thesis_src.parent / f"{thesis_src.name}-upstream.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(upstream)], check=True, capture_output=True)
    subprocess.run(["git", "init", "-b", "main", str(thesis_src)], check=True, capture_output=True)
    (thesis_src / "thesis.tex").write_text(marker_text)
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    subprocess.run(["git", "-C", str(thesis_src), "add", "thesis.tex"], check=True, env=env, capture_output=True)
    subprocess.run(
        ["git", "-C", str(thesis_src), "commit", "-m", "init"],
        check=True, env=env, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(thesis_src), "remote", "add", "origin", str(upstream)],
        check=True, env=env, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(thesis_src), "push", "origin", "main"],
        check=True, env=env, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(thesis_src), "branch", "--set-upstream-to=origin/main", "main"],
        check=True, env=env, capture_output=True,
    )
    out = subprocess.run(
        ["git", "-C", str(thesis_src), "rev-parse", "origin/main"],
        check=True, capture_output=True, text=True,
    )
    return out.stdout.strip()


def _stub_latexmk(bin_dir: Path, *, pdf_bytes: bytes = b"%PDF-1.4 STUB\n", exit_code: int = 0) -> None:
    """Install a fake latexmk on PATH that writes thesis.pdf in CWD on success.

    When `exit_code != 0` we simulate a real latex failure by NOT producing
    thesis.pdf and writing the would-be content to stderr instead, so the
    publisher's "build returned 0 but thesis.pdf is missing" branch is
    distinguishable from "build exited non-zero" in failure tests.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub = bin_dir / "latexmk"
    if exit_code == 0:
        body = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            # stub latexmk: ignore all flags, drop a fake PDF in CWD.
            printf '%s' '{pdf_bytes.decode("latin-1")}' > thesis.pdf
            exit 0
            """
        )
    else:
        body = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            # stub latexmk: simulate failure (no PDF produced).
            echo 'stub latexmk: simulated failure' >&2
            exit {exit_code}
            """
        )
    stub.write_text(body)
    stub.chmod(0o755)


@pytest.fixture
def env_setup(tmp_path: Path):
    """Build the canonical fixture layout the publisher expects.

    Returns a callable: run(env_overrides) -> CompletedProcess of the publisher.
    """
    thesis_src = tmp_path / "thesis"
    publish_dir = tmp_path / "_thesis-publish"
    deploy_path = tmp_path / "protea-deploy"
    public_dir = deploy_path / "apps" / "web" / "public"
    public_dir.mkdir(parents=True)
    farm_root = tmp_path / "agent-farm"
    (farm_root / "state").mkdir(parents=True)
    bin_dir = tmp_path / "stub-bin"

    head_sha = _init_thesis_clone(thesis_src)
    _stub_latexmk(bin_dir)

    def run(env_overrides=None, *, latexmk_exit: int = 0, drop_latexmk: bool = False,
            keep_stub: bool = False):
        if drop_latexmk:
            if (bin_dir / "latexmk").exists():
                (bin_dir / "latexmk").unlink()
            # Empty bin dir; we still need git on PATH, so place a sym-bin
            # that only links the binaries we DO want available.
            sym_bin = tmp_path / "sym-bin"
            sym_bin.mkdir(exist_ok=True)
            for tool in ("git", "bash", "sh", "rm", "mkdir", "cp", "mv",
                         "stat", "cat", "tee", "date", "printf", "tail",
                         "sed", "grep", "tr"):
                src = shutil.which(tool)
                if src is None:
                    continue
                link = sym_bin / tool
                if not link.exists():
                    link.symlink_to(src)
            path = str(sym_bin)  # deliberately excludes latexmk
        else:
            if not keep_stub:
                _stub_latexmk(bin_dir, exit_code=latexmk_exit)
            path = f"{bin_dir}:/usr/bin:/bin"
        env = {
            "HOME": str(tmp_path),
            "PATH": path,
            "AGENT_FARM_ROOT": str(farm_root),
            "THESIS_SRC": str(thesis_src),
            "THESIS_PUBLISH_DIR": str(publish_dir),
            "PROTEA_DEPLOY_PATH": str(deploy_path),
        }
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            ["bash", str(PUBLISHER)],
            capture_output=True, text=True, env=env,
        )

    return {
        "tmp_path": tmp_path,
        "thesis_src": thesis_src,
        "publish_dir": publish_dir,
        "public_dir": public_dir,
        "deploy_path": deploy_path,
        "farm_root": farm_root,
        "head_sha": head_sha,
        "bin_dir": bin_dir,
        "run": run,
    }


def test_happy_path_publishes_and_writes_marker(env_setup):
    """First invocation: builds, publishes, writes marker."""
    proc = env_setup["run"]()
    assert proc.returncode == 0, proc.stderr or proc.stdout

    served = env_setup["public_dir"] / "thesis.pdf"
    assert served.exists()
    assert served.read_bytes().startswith(b"%PDF-1.4 STUB")

    marker = env_setup["farm_root"] / "state" / "thesis_pdf_published.sha"
    assert marker.exists()
    assert marker.read_text().strip() == env_setup["head_sha"]


def test_noop_when_marker_matches(env_setup):
    """Second invocation with same HEAD: returns 0 without rebuilding."""
    env_setup["run"]()  # first publish populates marker
    # Replace stub latexmk with a poisoned one so any rebuild would fail.
    _stub_latexmk(env_setup["bin_dir"], exit_code=99)
    proc = env_setup["run"](keep_stub=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout

    # Log should contain noop marker.
    log = env_setup["farm_root"] / "state" / "logs" / "thesis_pdf_publish.log"
    assert "noop on" in log.read_text()


def test_rebuilds_when_origin_advances(env_setup):
    """After a new commit on origin/main, the next tick re-publishes."""
    env_setup["run"]()  # first publish

    # Add a new commit on origin via the thesis-src clone, then push.
    thesis_src = env_setup["thesis_src"]
    (thesis_src / "thesis.tex").write_text("% v2\n")
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    subprocess.run(["git", "-C", str(thesis_src), "add", "thesis.tex"], check=True, env=env, capture_output=True)
    subprocess.run(["git", "-C", str(thesis_src), "commit", "-m", "v2"], check=True, env=env, capture_output=True)
    subprocess.run(["git", "-C", str(thesis_src), "push", "origin", "main"], check=True, env=env, capture_output=True)
    new_sha = subprocess.run(
        ["git", "-C", str(thesis_src), "rev-parse", "origin/main"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert new_sha != env_setup["head_sha"]

    # Use a recognisable payload so we can verify the served PDF was rewritten.
    _stub_latexmk(env_setup["bin_dir"], pdf_bytes=b"%PDF-1.4 V2\n")
    proc = env_setup["run"](keep_stub=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout

    served = env_setup["public_dir"] / "thesis.pdf"
    assert served.read_bytes().startswith(b"%PDF-1.4 V2")

    marker = env_setup["farm_root"] / "state" / "thesis_pdf_published.sha"
    assert marker.read_text().strip() == new_sha


def test_missing_latexmk_returns_2(env_setup):
    """No latex toolchain on host: skip cleanly, don't crash the tick."""
    proc = env_setup["run"](drop_latexmk=True)
    assert proc.returncode == 2, proc.stderr or proc.stdout
    # No PDF should have been written.
    assert not (env_setup["public_dir"] / "thesis.pdf").exists()


def test_missing_deploy_worktree_returns_2(env_setup):
    """Deploy worktree wiped: skip cleanly. The redeploy step recreates it."""
    shutil.rmtree(env_setup["public_dir"])
    proc = env_setup["run"]()
    assert proc.returncode == 2, proc.stderr or proc.stdout


def test_missing_thesis_clone_returns_2(env_setup, tmp_path):
    """Thesis source clone deleted: skip cleanly."""
    proc = env_setup["run"](env_overrides={"THESIS_SRC": str(tmp_path / "no-such-thesis")})
    assert proc.returncode == 2, proc.stderr or proc.stdout


def test_build_failure_returns_1_preserves_prior_pdf(env_setup):
    """If latexmk fails the previously published PDF must remain intact."""
    env_setup["run"]()  # successful first publish
    prior = (env_setup["public_dir"] / "thesis.pdf").read_bytes()

    # Advance origin so the publisher tries to rebuild.
    thesis_src = env_setup["thesis_src"]
    (thesis_src / "thesis.tex").write_text("% v3\n")
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    subprocess.run(["git", "-C", str(thesis_src), "add", "thesis.tex"], check=True, env=env, capture_output=True)
    subprocess.run(["git", "-C", str(thesis_src), "commit", "-m", "v3"], check=True, env=env, capture_output=True)
    subprocess.run(["git", "-C", str(thesis_src), "push", "origin", "main"], check=True, env=env, capture_output=True)

    proc = env_setup["run"](latexmk_exit=2)
    assert proc.returncode == 1, proc.stderr or proc.stdout

    # Prior PDF must be untouched (atomic publish, never overwrite on failure).
    assert (env_setup["public_dir"] / "thesis.pdf").read_bytes() == prior

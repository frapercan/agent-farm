"""Tests for scripts/services/lib/protea_complexity_pdf_publish.sh.

The complexity publisher builds the companion paper PDF from the LOCAL
complexity-paper repo, pinned to its latest annotated tag, and copies the
result into the deploy-keeper public dir on every tick.

Real latex builds are slow and require the full toolchain, so these tests
stub `latexmk` (and the Makefile's `make pdf` target) via a fake `make` on a
PATH prefix that produces complexity.pdf in the working directory. This lets
us exercise all code paths without network access, external repos, or a TeX
installation.

Coverage:
- happy path: builds, atomically publishes, and writes marker
- noop when marker matches the tag commit SHA and PDF exists
- new tag causes rebuild
- missing latexmk returns 2 (env-skip, tick must not fail)
- missing deploy public dir returns 2
- missing source repo returns 2
- build failure returns 1, prior PDF is preserved
"""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLISHER = REPO_ROOT / "scripts" / "services" / "lib" / "protea_complexity_pdf_publish.sh"

_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_complexity_repo(src: Path, tag: str = "v1.0") -> str:
    """Create a minimal local complexity-paper git repo with an annotated tag.

    Returns the commit SHA the tag points to.
    """
    subprocess.run(["git", "init", "-b", "main", str(src)], check=True, capture_output=True)
    (src / "main.tex").write_text("% complexity placeholder\n")
    subprocess.run(["git", "-C", str(src), "add", "main.tex"], check=True, env=_GIT_ENV, capture_output=True)
    subprocess.run(
        ["git", "-C", str(src), "commit", "-m", "init"],
        check=True, env=_GIT_ENV, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(src), "tag", "-a", tag, "-m", f"release {tag}"],
        check=True, env=_GIT_ENV, capture_output=True,
    )
    out = subprocess.run(
        ["git", "-C", str(src), "rev-parse", f"{tag}^{{commit}}"],
        check=True, capture_output=True, text=True,
    )
    return out.stdout.strip()


def _add_commit_and_tag(src: Path, tag: str) -> str:
    """Add a new commit to the repo and attach a new annotated tag; return commit SHA."""
    (src / "main.tex").write_text(f"% {tag}\n")
    subprocess.run(["git", "-C", str(src), "add", "main.tex"], check=True, env=_GIT_ENV, capture_output=True)
    subprocess.run(
        ["git", "-C", str(src), "commit", "-m", tag],
        check=True, env=_GIT_ENV, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(src), "tag", "-a", tag, "-m", f"release {tag}"],
        check=True, env=_GIT_ENV, capture_output=True,
    )
    out = subprocess.run(
        ["git", "-C", str(src), "rev-parse", f"{tag}^{{commit}}"],
        check=True, capture_output=True, text=True,
    )
    return out.stdout.strip()


def _stub_make(bin_dir: Path, *, pdf_bytes: bytes = b"%PDF-1.4 COMPLEXITY-STUB\n", exit_code: int = 0) -> None:
    """Install a fake `make` on PATH that writes complexity.pdf in CWD.

    The publisher calls `make pdf` inside the publish worktree. We override
    make (not latexmk) because the Makefile calls both latexmk and cp; it is
    simpler to replace the whole make invocation with a stub.

    When exit_code != 0 we simulate a build failure by NOT producing
    complexity.pdf.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub = bin_dir / "make"
    if exit_code == 0:
        body = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            # stub make: ignore all targets/flags, drop a fake PDF in CWD.
            printf '%s' '{pdf_bytes.decode("latin-1")}' > complexity.pdf
            exit 0
            """
        )
    else:
        body = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            # stub make: simulate build failure.
            echo 'stub make: simulated failure' >&2
            exit {exit_code}
            """
        )
    stub.write_text(body)
    stub.chmod(0o755)

    # latexmk must also exist on PATH (the env-check in the publisher tests
    # for it before doing anything else).
    latexmk_stub = bin_dir / "latexmk"
    latexmk_body = textwrap.dedent(
        """\
        #!/usr/bin/env bash
        # stub latexmk: presence check only; real work done by make stub.
        exit 0
        """
    )
    latexmk_stub.write_text(latexmk_body)
    latexmk_stub.chmod(0o755)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def env_setup(tmp_path: Path):
    """Build the canonical fixture layout the complexity publisher expects.

    Returns a dict with fixture paths and a `run` callable.
    """
    src = tmp_path / "complexity-paper"
    publish_dir = tmp_path / "_complexity-publish"
    deploy_path = tmp_path / "protea-deploy"
    public_dir = deploy_path / "apps" / "web" / "public"
    public_dir.mkdir(parents=True)
    farm_root = tmp_path / "agent-farm"
    (farm_root / "state").mkdir(parents=True)
    bin_dir = tmp_path / "stub-bin"

    tag_sha = _init_complexity_repo(src, tag="v1.0")
    _stub_make(bin_dir)

    def run(env_overrides=None, *, make_exit: int = 0, drop_latexmk: bool = False,
            keep_stub: bool = False):
        if drop_latexmk:
            # Remove latexmk so the publisher hits exit 2.
            # We still put git + core utils on PATH.
            import shutil
            sym_bin = tmp_path / "sym-bin"
            sym_bin.mkdir(exist_ok=True)
            for tool in ("git", "bash", "sh", "rm", "mkdir", "cp", "mv",
                         "stat", "cat", "tee", "date", "printf", "tail",
                         "sed", "grep", "tr", "make", "head"):
                src_path = shutil.which(tool)
                if src_path is None:
                    continue
                link = sym_bin / tool
                if not link.exists():
                    link.symlink_to(src_path)
            path = str(sym_bin)  # deliberately excludes latexmk
        else:
            if not keep_stub:
                _stub_make(bin_dir, exit_code=make_exit)
            path = f"{bin_dir}:/usr/bin:/bin"
        env = {
            "HOME": str(tmp_path),
            "PATH": path,
            "AGENT_FARM_ROOT": str(farm_root),
            "COMPLEXITY_SRC": str(src),
            "COMPLEXITY_PUBLISH_DIR": str(publish_dir),
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
        "src": src,
        "publish_dir": publish_dir,
        "public_dir": public_dir,
        "deploy_path": deploy_path,
        "farm_root": farm_root,
        "tag_sha": tag_sha,
        "bin_dir": bin_dir,
        "run": run,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_happy_path_publishes_and_writes_marker(env_setup):
    """First invocation: build, publish, write marker."""
    proc = env_setup["run"]()
    assert proc.returncode == 0, proc.stderr or proc.stdout

    served = env_setup["public_dir"] / "complexity.pdf"
    assert served.exists()
    assert served.read_bytes().startswith(b"%PDF-1.4 COMPLEXITY-STUB")

    marker = env_setup["farm_root"] / "state" / "complexity_pdf_published.sha"
    assert marker.exists()
    assert marker.read_text().strip() == env_setup["tag_sha"]


def test_noop_when_tag_unchanged(env_setup):
    """Second invocation with the same tag: returns 0 without rebuilding."""
    env_setup["run"]()  # first publish populates marker

    # Replace stub make with a poisoned one so any rebuild would fail.
    _stub_make(env_setup["bin_dir"], exit_code=99)
    proc = env_setup["run"](keep_stub=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout

    log = env_setup["farm_root"] / "state" / "logs" / "complexity_pdf_publish.log"
    assert "noop on" in log.read_text()


def test_rebuilds_when_new_tag_created(env_setup):
    """After a new annotated tag on the source repo, the next tick rebuilds."""
    env_setup["run"]()  # first publish

    new_sha = _add_commit_and_tag(env_setup["src"], "v1.1")
    assert new_sha != env_setup["tag_sha"]

    _stub_make(env_setup["bin_dir"], pdf_bytes=b"%PDF-1.4 V1.1\n")
    proc = env_setup["run"](keep_stub=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout

    served = env_setup["public_dir"] / "complexity.pdf"
    assert served.read_bytes().startswith(b"%PDF-1.4 V1.1")

    marker = env_setup["farm_root"] / "state" / "complexity_pdf_published.sha"
    assert marker.read_text().strip() == new_sha


def test_missing_latexmk_returns_2(env_setup):
    """No latex toolchain on host: skip cleanly with exit 2, tick must not fail."""
    proc = env_setup["run"](drop_latexmk=True)
    assert proc.returncode == 2, proc.stderr or proc.stdout
    assert not (env_setup["public_dir"] / "complexity.pdf").exists()


def test_missing_deploy_public_dir_returns_2(env_setup):
    """Deploy worktree wiped: skip cleanly with exit 2."""
    import shutil
    shutil.rmtree(env_setup["public_dir"])
    proc = env_setup["run"]()
    assert proc.returncode == 2, proc.stderr or proc.stdout


def test_missing_source_repo_returns_2(env_setup):
    """Complexity-paper source removed: skip cleanly with exit 2."""
    proc = env_setup["run"](
        env_overrides={"COMPLEXITY_SRC": str(env_setup["tmp_path"] / "no-such-repo")}
    )
    assert proc.returncode == 2, proc.stderr or proc.stdout


def test_build_failure_returns_1_preserves_prior_pdf(env_setup):
    """Latexmk (make) failure returns 1 and the prior PDF is preserved."""
    env_setup["run"]()  # successful first publish
    prior = (env_setup["public_dir"] / "complexity.pdf").read_bytes()

    # Advance tag so the publisher decides to rebuild.
    _add_commit_and_tag(env_setup["src"], "v1.1")

    proc = env_setup["run"](make_exit=2)
    assert proc.returncode == 1, proc.stderr or proc.stdout

    # Atomic publish means the prior PDF is never overwritten on failure.
    assert (env_setup["public_dir"] / "complexity.pdf").read_bytes() == prior

"""Tests for FARM-1.4 worktree-only hardening.

Covers two artefacts:

1. ``scripts/lib/worktree-guard.sh`` — ``assert`` subcommand and the
   sourceable ``assert_in_worktree`` function.
2. ``scripts/install-dev-hooks.sh`` — installer that drops a
   ``pre-commit`` hook into the dev's main checkout rejecting commits
   on agent-owned branches (``task/*``, ``feat/T*``, ``hookwt/*``).

Both pieces are pure bash, so the tests use ``subprocess`` and build
temporary git trees that mimic the real layout
(``<tmp>/repositories/<repo>/`` for dev clones and
``<tmp>/worktrees/<task>/`` for ephemeral worktrees).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD = REPO_ROOT / "scripts" / "lib" / "worktree-guard.sh"
DEV_HOOKS = REPO_ROOT / "scripts" / "install-dev-hooks.sh"


def _run(cmd: list[str], *, env: dict | None = None,
         cwd: str | Path | None = None,
         check: bool = False) -> subprocess.CompletedProcess:
    full_env = os.environ.copy()
    full_env.setdefault("GIT_TERMINAL_PROMPT", "0")
    full_env["LC_ALL"] = "C"
    if env:
        full_env.update(env)
    return subprocess.run(
        cmd, capture_output=True, text=True, check=check,
        env=full_env, cwd=str(cwd) if cwd else None,
    )


def _git(repo: Path, *args: str, check: bool = True,
         env: dict | None = None) -> subprocess.CompletedProcess:
    return _run(["git", "-C", str(repo), *args], env=env, check=check)


# ---------------------------------------------------------------------------
# Layout fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_thesis_root(tmp_path: Path) -> Path:
    """Build a tmp tree mirroring ``$HOME/Thesis2`` layout.

    Layout::

        <root>/
          repositories/
            FAKEREPO/            # dev's main clone (git init + 1 commit)
          worktrees/
            (linked worktrees of FAKEREPO live here)
    """
    repos = tmp_path / "repositories"
    worktrees = tmp_path / "worktrees"
    repos.mkdir()
    worktrees.mkdir()
    clone = repos / "FAKEREPO"
    clone.mkdir()
    _git(clone, "init", "-q", "-b", "main")
    _git(clone, "config", "user.email", "test@example.invalid")
    _git(clone, "config", "user.name", "test")
    (clone / "README").write_text("seed\n")
    _git(clone, "add", "README")
    # Bypass any inherited hooks for the seed commit.
    subprocess.run(
        ["git", "-C", str(clone), "-c", "core.hooksPath=", "commit", "-q",
         "-m", "init"],
        check=True,
    )
    return tmp_path


@pytest.fixture
def guard_env(fake_thesis_root: Path) -> dict:
    """Environment that points worktree-guard at the fake tree."""
    return {
        "AGENT_FARM_REPOS_ROOT": str(fake_thesis_root / "repositories"),
        "AGENT_FARM_WORKTREES_ROOT": str(fake_thesis_root / "worktrees"),
    }


# ---------------------------------------------------------------------------
# worktree-guard.sh — assert subcommand
# ---------------------------------------------------------------------------


class TestAssertInWorktree:
    def test_refuses_in_dev_clone(self, fake_thesis_root: Path,
                                  guard_env: dict) -> None:
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        res = _run(["bash", str(GUARD), "assert", str(clone)], env=guard_env)
        assert res.returncode != 0, res.stdout
        assert "refusing to operate inside the dev workspace" in res.stderr

    def test_refuses_in_subdir_of_dev_clone(self, fake_thesis_root: Path,
                                            guard_env: dict) -> None:
        sub = fake_thesis_root / "repositories" / "FAKEREPO" / "subdir"
        sub.mkdir()
        res = _run(["bash", str(GUARD), "assert", str(sub)], env=guard_env)
        assert res.returncode != 0
        assert "dev workspace" in res.stderr

    def test_accepts_in_linked_worktree(self, fake_thesis_root: Path,
                                        guard_env: dict) -> None:
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        wt = fake_thesis_root / "worktrees" / "task-abc"
        _git(clone, "worktree", "add", "-b", "task/abc", str(wt), "main")
        res = _run(["bash", str(GUARD), "assert", str(wt)], env=guard_env)
        assert res.returncode == 0, res.stderr

    def test_refuses_in_random_main_checkout(self, tmp_path: Path) -> None:
        """A main checkout outside the dev tree is also refused (rule 2:
        git_dir == common_dir means it is not a linked worktree)."""
        repo = tmp_path / "elsewhere"
        repo.mkdir()
        _git(repo, "init", "-q", "-b", "main")
        _git(repo, "config", "user.email", "t@example.invalid")
        _git(repo, "config", "user.name", "t")
        (repo / "f").write_text("x\n")
        _git(repo, "add", "f")
        subprocess.run(
            ["git", "-C", str(repo), "-c", "core.hooksPath=", "commit", "-q",
             "-m", "init"],
            check=True,
        )
        env = {
            "AGENT_FARM_REPOS_ROOT": str(tmp_path / "no-such-repos"),
            "AGENT_FARM_WORKTREES_ROOT": str(tmp_path / "no-such-worktrees"),
        }
        res = _run(["bash", str(GUARD), "assert", str(repo)], env=env)
        assert res.returncode != 0
        assert "main checkout" in res.stderr

    def test_refuses_non_git_path(self, tmp_path: Path) -> None:
        notrepo = tmp_path / "plain"
        notrepo.mkdir()
        res = _run(["bash", str(GUARD), "assert", str(notrepo)])
        assert res.returncode != 0
        assert "not a git working tree" in res.stderr

    def test_refuses_missing_path(self, tmp_path: Path) -> None:
        res = _run(["bash", str(GUARD), "assert",
                    str(tmp_path / "does-not-exist")])
        assert res.returncode != 0
        assert "does not exist" in res.stderr

    def test_bypass_via_env_var(self, fake_thesis_root: Path,
                                guard_env: dict) -> None:
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        env = {**guard_env, "AGENT_FARM_SKIP_WORKTREE_GUARD": "1"}
        res = _run(["bash", str(GUARD), "assert", str(clone)], env=env)
        assert res.returncode == 0, res.stderr

    def test_default_path_is_pwd(self, fake_thesis_root: Path,
                                 guard_env: dict) -> None:
        """When no argument is passed, the guard checks $PWD."""
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        wt = fake_thesis_root / "worktrees" / "task-pwd"
        _git(clone, "worktree", "add", "-b", "task/pwd", str(wt), "main")

        # PWD = worktree => OK
        ok = _run(["bash", str(GUARD), "assert"], env=guard_env, cwd=wt)
        assert ok.returncode == 0, ok.stderr

        # PWD = dev clone => refused
        bad = _run(["bash", str(GUARD), "assert"], env=guard_env, cwd=clone)
        assert bad.returncode != 0
        assert "dev workspace" in bad.stderr

    def test_sourceable_function(self, fake_thesis_root: Path,
                                 guard_env: dict) -> None:
        """The script also exposes ``assert_in_worktree`` as a shell function."""
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        wt = fake_thesis_root / "worktrees" / "task-src"
        _git(clone, "worktree", "add", "-b", "task/src", str(wt), "main")
        snippet = (
            f"source {GUARD!s}\n"
            f"assert_in_worktree {wt!s}\n"
        )
        ok = _run(["bash", "-c", snippet], env=guard_env)
        assert ok.returncode == 0, ok.stderr

        snippet_bad = (
            f"source {GUARD!s}\n"
            f"assert_in_worktree {clone!s}\n"
        )
        bad = _run(["bash", "-c", snippet_bad], env=guard_env)
        assert bad.returncode != 0
        assert "dev workspace" in bad.stderr


# ---------------------------------------------------------------------------
# install-dev-hooks.sh — installer + hook behaviour
# ---------------------------------------------------------------------------


class TestInstallDevHooks:
    def _install(self, clone: Path, *, env: dict | None = None,
                 extra: list[str] | None = None) -> subprocess.CompletedProcess:
        cmd = ["bash", str(DEV_HOOKS)]
        if extra:
            cmd.extend(extra)
        else:
            cmd.append(str(clone))
        return _run(cmd, env=env)

    def test_installs_pre_commit(self, fake_thesis_root: Path,
                                 guard_env: dict) -> None:
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        res = self._install(clone, env=guard_env)
        assert res.returncode == 0, res.stderr
        hook = clone / ".git" / "hooks" / "pre-commit"
        assert hook.exists()
        assert hook.stat().st_mode & 0o111, "pre-commit not executable"
        assert "FARM-1.4 dev-clone guard" in hook.read_text()

    def test_idempotent_reinstall(self, fake_thesis_root: Path,
                                  guard_env: dict) -> None:
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        self._install(clone, env=guard_env)
        first = (clone / ".git" / "hooks" / "pre-commit").read_text()
        res = self._install(clone, env=guard_env)
        assert res.returncode == 0, res.stderr
        second = (clone / ".git" / "hooks" / "pre-commit").read_text()
        assert first == second

    def test_uninstall_removes_hook(self, fake_thesis_root: Path,
                                    guard_env: dict) -> None:
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        self._install(clone, env=guard_env)
        res = self._install(clone, env=guard_env,
                            extra=["--uninstall", str(clone)])
        assert res.returncode == 0, res.stderr
        assert not (clone / ".git" / "hooks" / "pre-commit").exists()

    def test_refuses_to_clobber_non_farm_hook(self, fake_thesis_root: Path,
                                              guard_env: dict) -> None:
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        hook = clone / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\necho 'user hook'\nexit 0\n")
        hook.chmod(0o755)
        res = self._install(clone, env=guard_env)
        assert res.returncode != 0
        assert "refusing to overwrite" in res.stderr
        # Original content preserved.
        assert "user hook" in hook.read_text()

    def test_refuses_linked_worktree(self, fake_thesis_root: Path,
                                     guard_env: dict) -> None:
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        wt = fake_thesis_root / "worktrees" / "task-x"
        _git(clone, "worktree", "add", "-b", "task/x", str(wt), "main")
        res = self._install(wt, env=guard_env)
        assert res.returncode != 0
        assert "linked worktree" in res.stderr

    def test_all_iterates_repositories(self, fake_thesis_root: Path,
                                       guard_env: dict) -> None:
        # Add a second clone alongside FAKEREPO.
        repos = fake_thesis_root / "repositories"
        second = repos / "OTHER"
        second.mkdir()
        _git(second, "init", "-q", "-b", "main")
        _git(second, "config", "user.email", "t@example.invalid")
        _git(second, "config", "user.name", "t")
        (second / "R").write_text("s\n")
        _git(second, "add", "R")
        subprocess.run(
            ["git", "-C", str(second), "-c", "core.hooksPath=", "commit",
             "-q", "-m", "init"],
            check=True,
        )
        res = self._install(second, env=guard_env, extra=["--all"])
        assert res.returncode == 0, res.stderr
        for name in ("FAKEREPO", "OTHER"):
            assert (repos / name / ".git" / "hooks" / "pre-commit").exists()

    # --- hook behaviour --------------------------------------------------

    def _try_commit_on_branch(self, clone: Path, branch: str,
                              env: dict | None = None) -> subprocess.CompletedProcess:
        _git(clone, "checkout", "-B", branch)
        (clone / f"x-{branch.replace('/', '_')}").write_text("c\n")
        _git(clone, "add", f"x-{branch.replace('/', '_')}")
        return _git(clone, "commit", "-m", "wip", check=False, env=env)

    @pytest.mark.parametrize("branch", [
        "task/foo",
        "task/executor-12345-abcd",
        "feat/T1.2-thing",
        "feat/TINFRA.NACK",
        "hookwt/whatever",
    ])
    def test_hook_rejects_agent_branches(self, fake_thesis_root: Path,
                                         guard_env: dict, branch: str) -> None:
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        self._install(clone, env=guard_env)
        res = self._try_commit_on_branch(clone, branch)
        assert res.returncode != 0, res.stdout
        assert "dev-clone guard" in res.stderr
        assert branch in res.stderr

    @pytest.mark.parametrize("branch", [
        "main",
        "develop",
        "feat/some-area",          # human-named feat branch (not feat/T...)
        "feat/refactor-foo",
        "fix/bug-123",
        "chore/cleanup",
    ])
    def test_hook_allows_human_branches(self, fake_thesis_root: Path,
                                        guard_env: dict, branch: str) -> None:
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        self._install(clone, env=guard_env)
        # main already exists; for the rest, create.
        if branch != "main":
            _git(clone, "checkout", "-B", branch)
        else:
            _git(clone, "checkout", "main")
        fname = f"y-{branch.replace('/', '_')}"
        (clone / fname).write_text("c\n")
        _git(clone, "add", fname)
        res = _git(clone, "commit", "-m", "human", check=False)
        assert res.returncode == 0, res.stderr

    def test_hook_bypass_via_env_var(self, fake_thesis_root: Path,
                                     guard_env: dict) -> None:
        clone = fake_thesis_root / "repositories" / "FAKEREPO"
        self._install(clone, env=guard_env)
        res = self._try_commit_on_branch(
            clone, "task/zzz",
            env={"AGENT_FARM_SKIP_DEV_HOOKS": "1"},
        )
        assert res.returncode == 0, res.stderr

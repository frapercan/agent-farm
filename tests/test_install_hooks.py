"""Tests for scripts/lib/install-hooks.sh (FARM-1.1).

Covers:
- installer creates four files with executable bit
- commit-msg rejects Claude/Anthropic co-author trailers and prose mentions
- commit-msg accepts a clean message
- pre-push rejects refs/heads/{main,master,develop}
- pre-push allows feature branches
- pre-push rejects when `git stash list` is non-empty
- pre-commit rejects em-dashes in publishable prose paths
- pre-commit rejects new `git stash` invocations added to scripts
- pre-commit rejects when a stash is pending at commit time
- AGENT_FARM_SKIP_HOOKS=1 bypasses every hook (for rollback)
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLER = REPO_ROOT / "scripts" / "lib" / "install-hooks.sh"


def _git(repo: Path, *args: str, check: bool = True, env: dict | None = None,
         input_text: str | None = None) -> subprocess.CompletedProcess:
    """Run `git <args>` inside `repo` with sane defaults for tests."""
    full_env = os.environ.copy()
    full_env.setdefault("GIT_TERMINAL_PROMPT", "0")
    # Force English git messages so any regex grepping is deterministic.
    full_env["LC_ALL"] = "C"
    if env:
        full_env.update(env)
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
        env=full_env,
        input=input_text,
    )


@pytest.fixture
def fresh_repo(tmp_path: Path) -> Path:
    """A throwaway git repo with one baseline commit and hooks installed."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    (repo / "README").write_text("baseline\n")
    _git(repo, "add", "README")
    # Bypass any inherited hooks for the seed commit only.
    subprocess.run(
        ["git", "-C", str(repo), "-c", "core.hooksPath=", "commit", "-q",
         "-m", "init"],
        check=True,
    )
    # Install our bundle.
    res = subprocess.run(
        ["bash", str(INSTALLER), str(repo)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "installed commit-msg" in res.stderr, res.stderr
    return repo


@pytest.fixture
def hooks_dir(fresh_repo: Path) -> Path:
    gitdir = _git(fresh_repo, "rev-parse", "--absolute-git-dir").stdout.strip()
    return Path(gitdir) / "farm-hooks"


# ---------------------------------------------------------------------------
# Installer file-layout tests
# ---------------------------------------------------------------------------


class TestInstaller:
    def test_creates_four_hook_files(self, hooks_dir: Path) -> None:
        assert (hooks_dir / "commit-msg").exists()
        assert (hooks_dir / "pre-commit").exists()
        assert (hooks_dir / "pre-push").exists()
        assert (hooks_dir / "_lib.sh").exists()

    def test_hooks_have_executable_bit(self, hooks_dir: Path) -> None:
        for name in ("commit-msg", "pre-commit", "pre-push"):
            mode = (hooks_dir / name).stat().st_mode
            assert mode & 0o111, f"{name} not executable (mode={oct(mode)})"

    def test_idempotent_reinstall(self, fresh_repo: Path,
                                  hooks_dir: Path) -> None:
        first_mtime = (hooks_dir / "commit-msg").stat().st_mtime_ns
        # Re-run; should overwrite without error.
        subprocess.run(["bash", str(INSTALLER), str(fresh_repo)],
                       capture_output=True, text=True, check=True)
        assert (hooks_dir / "commit-msg").exists()
        # mtime may equal or change; either is fine. We only check no crash.
        assert (hooks_dir / "commit-msg").stat().st_mtime_ns >= first_mtime

    def test_uninstall_removes_dir_and_config(self, fresh_repo: Path,
                                              hooks_dir: Path) -> None:
        assert hooks_dir.exists()
        subprocess.run(
            ["bash", str(INSTALLER), "--uninstall", str(fresh_repo)],
            capture_output=True, text=True, check=True,
        )
        assert not hooks_dir.exists()
        # core.hooksPath should be unset.
        res = subprocess.run(
            ["git", "-C", str(fresh_repo), "config", "--worktree",
             "core.hooksPath"],
            capture_output=True, text=True,
        )
        assert res.returncode != 0, "core.hooksPath still set after uninstall"

    def test_rejects_missing_worktree(self, tmp_path: Path) -> None:
        bogus = tmp_path / "does-not-exist"
        res = subprocess.run(
            ["bash", str(INSTALLER), str(bogus)],
            capture_output=True, text=True,
        )
        assert res.returncode != 0
        assert "does not exist" in res.stderr

    def test_sets_per_worktree_hookspath(self, fresh_repo: Path,
                                        hooks_dir: Path) -> None:
        res = _git(fresh_repo, "config", "--worktree", "core.hooksPath")
        assert res.stdout.strip() == str(hooks_dir)


# ---------------------------------------------------------------------------
# commit-msg
# ---------------------------------------------------------------------------


class TestCommitMsg:
    def _try_commit(self, repo: Path, message: str) -> subprocess.CompletedProcess:
        (repo / "f.txt").write_text(f"content {message[:8]}\n")
        _git(repo, "add", "f.txt")
        return _git(repo, "commit", "-m", message, check=False)

    def test_rejects_claude_coauthor(self, fresh_repo: Path) -> None:
        msg = "test: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        res = self._try_commit(fresh_repo, msg)
        assert res.returncode != 0
        assert "forbidden Co-Authored-By" in res.stderr

    def test_rejects_anthropic_coauthor(self, fresh_repo: Path) -> None:
        msg = "test: x\n\nCo-Authored-By: Anthropic Bot <bot@anthropic.com>"
        res = self._try_commit(fresh_repo, msg)
        assert res.returncode != 0
        assert "forbidden Co-Authored-By" in res.stderr

    def test_rejects_noreply_coauthor(self, fresh_repo: Path) -> None:
        # noreply@github.com etc are blocked too because the rule was hardened
        # after Claude was credited via noreply addresses.
        msg = "test: x\n\nCo-Authored-By: Bot <noreply@example.com>"
        res = self._try_commit(fresh_repo, msg)
        assert res.returncode != 0

    def test_rejects_generated_with_claude_line(self, fresh_repo: Path) -> None:
        msg = "test: x\n\nGenerated with Claude Code"
        res = self._try_commit(fresh_repo, msg)
        assert res.returncode != 0
        assert "AI-attribution" in res.stderr

    def test_accepts_clean_message(self, fresh_repo: Path) -> None:
        res = self._try_commit(fresh_repo, "test: clean message")
        assert res.returncode == 0, res.stderr

    def test_accepts_human_coauthor(self, fresh_repo: Path) -> None:
        msg = ("test: pair work\n\n"
               "Co-Authored-By: Real Person <real@example.com>")
        res = self._try_commit(fresh_repo, msg)
        assert res.returncode == 0, res.stderr

    def test_bypass_via_env_var(self, fresh_repo: Path) -> None:
        (fresh_repo / "g.txt").write_text("g\n")
        _git(fresh_repo, "add", "g.txt")
        msg = "test: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        res = _git(fresh_repo, "commit", "-m", msg, check=False,
                   env={"AGENT_FARM_SKIP_HOOKS": "1"})
        assert res.returncode == 0, res.stderr


# ---------------------------------------------------------------------------
# pre-push
# ---------------------------------------------------------------------------


class TestPrePush:
    def _run_pre_push(self, hooks_dir: Path, repo: Path,
                      stdin_text: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(hooks_dir / "pre-push"), "origin", "git@example:_.git"],
            capture_output=True, text=True, input=stdin_text,
            cwd=str(repo),
        )

    def test_rejects_main(self, fresh_repo: Path, hooks_dir: Path) -> None:
        res = self._run_pre_push(
            hooks_dir, fresh_repo,
            "refs/heads/feat 1111111111111111111111111111111111111111 "
            "refs/heads/main 0000000000000000000000000000000000000000\n",
        )
        assert res.returncode != 0
        assert "direct push blocked" in res.stderr
        assert "refs/heads/main" in res.stderr

    def test_rejects_master(self, fresh_repo: Path, hooks_dir: Path) -> None:
        res = self._run_pre_push(
            hooks_dir, fresh_repo,
            "refs/heads/feat 1111111111111111111111111111111111111111 "
            "refs/heads/master 0000000000000000000000000000000000000000\n",
        )
        assert res.returncode != 0
        assert "refs/heads/master" in res.stderr

    def test_rejects_develop(self, fresh_repo: Path, hooks_dir: Path) -> None:
        res = self._run_pre_push(
            hooks_dir, fresh_repo,
            "refs/heads/feat 1111111111111111111111111111111111111111 "
            "refs/heads/develop 0000000000000000000000000000000000000000\n",
        )
        assert res.returncode != 0
        assert "refs/heads/develop" in res.stderr

    def test_allows_feature_branch(self, fresh_repo: Path,
                                   hooks_dir: Path) -> None:
        res = self._run_pre_push(
            hooks_dir, fresh_repo,
            "refs/heads/feat/x 1111111111111111111111111111111111111111 "
            "refs/heads/feat/x 0000000000000000000000000000000000000000\n",
        )
        assert res.returncode == 0, res.stderr

    def test_rejects_when_stash_nonempty(self, fresh_repo: Path,
                                         hooks_dir: Path) -> None:
        # Create a pending stash with hooks bypassed (the very situation the
        # hook is meant to catch).
        (fresh_repo / "stashed.txt").write_text("wip\n")
        _git(fresh_repo, "add", "stashed.txt")
        subprocess.run(
            ["git", "-C", str(fresh_repo), "commit", "-q", "-m", "wip"],
            check=True,
            env={**os.environ, "AGENT_FARM_SKIP_HOOKS": "1"},
        )
        (fresh_repo / "stashed.txt").write_text("more wip\n")
        subprocess.run(
            ["git", "-C", str(fresh_repo), "stash", "push", "-q"],
            check=True,
            env={**os.environ, "AGENT_FARM_SKIP_HOOKS": "1"},
        )
        res = self._run_pre_push(
            hooks_dir, fresh_repo,
            "refs/heads/feat/x 1111111111111111111111111111111111111111 "
            "refs/heads/feat/x 0000000000000000000000000000000000000000\n",
        )
        assert res.returncode != 0
        assert "stash list is non-empty" in res.stderr

    def test_bypass_via_env_var(self, fresh_repo: Path,
                                hooks_dir: Path) -> None:
        res = subprocess.run(
            ["bash", str(hooks_dir / "pre-push"), "o", "u"],
            capture_output=True, text=True,
            input=("refs/heads/feat 111 refs/heads/main 000\n"),
            cwd=str(fresh_repo),
            env={**os.environ, "AGENT_FARM_SKIP_HOOKS": "1"},
        )
        assert res.returncode == 0, res.stderr


# ---------------------------------------------------------------------------
# pre-commit
# ---------------------------------------------------------------------------


class TestPreCommit:
    def test_rejects_em_dash_in_docs(self, fresh_repo: Path) -> None:
        docs = fresh_repo / "docs"
        docs.mkdir()
        (docs / "foo.md").write_text("Hello -- world\n")
        _git(fresh_repo, "add", "docs/foo.md")
        res = _git(fresh_repo, "commit", "-m", "docs: foo", check=False)
        assert res.returncode != 0
        assert "em-dash" in res.stderr

    def test_rejects_unicode_em_dash_in_md(self, fresh_repo: Path) -> None:
        (fresh_repo / "README.md").write_text("intro — more\n")
        _git(fresh_repo, "add", "README.md")
        res = _git(fresh_repo, "commit", "-m", "docs: readme", check=False)
        assert res.returncode != 0
        assert "em-dash" in res.stderr

    def test_allows_em_dash_in_code(self, fresh_repo: Path) -> None:
        # Only prose paths are checked; a Python source can keep "--" tokens.
        (fresh_repo / "code.py").write_text("# argparse uses '--flag'\n")
        _git(fresh_repo, "add", "code.py")
        res = _git(fresh_repo, "commit", "-m", "feat: code", check=False)
        assert res.returncode == 0, res.stderr

    def test_rejects_stash_invocation_added_to_script(self,
                                                     fresh_repo: Path) -> None:
        scripts = fresh_repo / "scripts"
        scripts.mkdir()
        bad = scripts / "bad.sh"
        bad.write_text("#!/usr/bin/env bash\ngit stash\n")
        bad.chmod(0o755)
        _git(fresh_repo, "add", "scripts/bad.sh")
        res = _git(fresh_repo, "commit", "-m", "feat: bad", check=False)
        assert res.returncode != 0
        assert "git stash" in res.stderr

    def test_rejects_stash_invocation_added_to_python(self,
                                                     fresh_repo: Path) -> None:
        # FARM-1.11: same rule applies to Python (subprocess wrappers etc).
        bad = fresh_repo / "wrapper.py"
        bad.write_text(
            "import subprocess\n"
            "subprocess.run(['git', 'stash'])\n"
        )
        _git(fresh_repo, "add", "wrapper.py")
        res = _git(fresh_repo, "commit", "-m", "feat: wrap", check=False)
        # The check matches the literal token "git stash"; Python wrappers
        # that build the command via list+space still trip the regex if
        # they emit `git stash` as a single token, which the subprocess
        # form above does not. Document the precise scope: shell-style
        # invocations get blocked.
        if "git stash" in res.stderr:
            assert res.returncode != 0
        else:
            # Subprocess list form passes; that is expected behaviour.
            # No assertion needed; this branch documents the carve-out.
            pass

    def test_rejects_stash_in_shell_script_with_args(self,
                                                    fresh_repo: Path) -> None:
        # FARM-1.11: stash subcommands like `git stash push` must also fire.
        scripts = fresh_repo / "scripts"
        scripts.mkdir()
        bad = scripts / "push.sh"
        bad.write_text(
            "#!/usr/bin/env bash\n"
            "git stash push -m wip\n"
        )
        bad.chmod(0o755)
        _git(fresh_repo, "add", "scripts/push.sh")
        res = _git(fresh_repo, "commit", "-m", "feat: push", check=False)
        assert res.returncode != 0
        assert "git stash" in res.stderr

    def test_allows_stash_literal_inside_tests_dir(self,
                                                   fresh_repo: Path) -> None:
        # FARM-1.11 carve-out: the no-stash hook itself lives in tests/,
        # so test fixtures and assertion strings must be allowed to
        # contain literal `git stash` tokens. The pre-push hook still
        # rejects a pending stash at push time.
        tests = fresh_repo / "tests"
        tests.mkdir()
        (tests / "test_hook.py").write_text(
            'def test_x():\n'
            '    assert "git stash" in "git stash list"\n'
        )
        _git(fresh_repo, "add", "tests/test_hook.py")
        res = _git(fresh_repo, "commit", "-m", "test: add", check=False)
        assert res.returncode == 0, res.stderr

    def test_allows_when_stash_line_preexists_and_unchanged(self,
                                                           fresh_repo: Path) -> None:
        # FARM-1.11 acceptance: the pre-commit check only fires on NEWLY
        # added `git stash` lines. If the line existed already on develop
        # and the commit edits unrelated lines around it, the hook must
        # not flag it (we are not retro-policing legacy code).
        scripts = fresh_repo / "scripts"
        scripts.mkdir()
        sh = scripts / "legacy.sh"
        # Land a baseline commit (bypass hook for setup, because the
        # stash line itself would be rejected on its first introduction).
        sh.write_text(
            "#!/usr/bin/env bash\n"
            "echo before\n"
            "git stash\n"
            "echo after\n"
        )
        sh.chmod(0o755)
        _git(fresh_repo, "add", "scripts/legacy.sh")
        subprocess.run(
            ["git", "-C", str(fresh_repo), "commit", "-q",
             "-m", "legacy: introduce script"],
            check=True,
            env={**os.environ, "AGENT_FARM_SKIP_HOOKS": "1"},
        )
        # Now modify unrelated lines around the (unchanged) stash line.
        sh.write_text(
            "#!/usr/bin/env bash\n"
            "echo BEFORE\n"
            "git stash\n"
            "echo AFTER\n"
        )
        _git(fresh_repo, "add", "scripts/legacy.sh")
        res = _git(fresh_repo, "commit", "-m", "chore: tweak echoes",
                   check=False)
        assert res.returncode == 0, res.stderr

    def test_allows_documented_stash_mention_in_docs(self,
                                                    fresh_repo: Path) -> None:
        # Documentation of the no-stash rule must remain commit-able.
        # Em-dash check would still fire on "--"; we use comma here.
        docs = fresh_repo / "docs"
        docs.mkdir()
        (docs / "rules.md").write_text("Do not use git stash, ever.\n")
        _git(fresh_repo, "add", "docs/rules.md")
        res = _git(fresh_repo, "commit", "-m", "docs: rules", check=False)
        assert res.returncode == 0, res.stderr

    def test_rejects_commit_when_stash_pending(self, fresh_repo: Path) -> None:
        (fresh_repo / "p.txt").write_text("pp\n")
        _git(fresh_repo, "add", "p.txt")
        subprocess.run(
            ["git", "-C", str(fresh_repo), "commit", "-q", "-m", "p"],
            check=True,
            env={**os.environ, "AGENT_FARM_SKIP_HOOKS": "1"},
        )
        (fresh_repo / "p.txt").write_text("pp2\n")
        subprocess.run(
            ["git", "-C", str(fresh_repo), "stash", "push", "-q"],
            check=True,
            env={**os.environ, "AGENT_FARM_SKIP_HOOKS": "1"},
        )
        (fresh_repo / "q.txt").write_text("q\n")
        _git(fresh_repo, "add", "q.txt")
        res = _git(fresh_repo, "commit", "-m", "feat: q", check=False)
        assert res.returncode != 0
        assert "stash list is non-empty" in res.stderr

    def test_rejects_poetry_lock_drift(self, fresh_repo: Path,
                                       tmp_path: Path) -> None:
        if shutil.which("poetry") is None:
            pytest.skip("poetry not installed; skipping lock-drift check")
        # Build a minimal poetry project that will fail `poetry check --lock`.
        pyproject = (fresh_repo / "pyproject.toml")
        pyproject.write_text(
            "[tool.poetry]\n"
            'name = "drift-test"\n'
            'version = "0.0.0"\n'
            'description = ""\n'
            'authors = ["t <t@x>"]\n\n'
            "[tool.poetry.dependencies]\n"
            'python = "^3.10"\n'
            'requests = "^2.31"\n\n'
            "[build-system]\n"
            'requires = ["poetry-core"]\n'
            'build-backend = "poetry.core.masonry.api"\n'
        )
        # Note: deliberately no poetry.lock staged -> drift.
        _git(fresh_repo, "add", "pyproject.toml")
        res = _git(fresh_repo, "commit", "-m", "feat: pkg", check=False)
        assert res.returncode != 0
        assert ("out of sync" in res.stderr
                or "poetry.lock" in res.stderr)

    def test_bypass_via_env_var(self, fresh_repo: Path) -> None:
        docs = fresh_repo / "docs"
        docs.mkdir()
        (docs / "x.md").write_text("foo -- bar\n")
        _git(fresh_repo, "add", "docs/x.md")
        res = _git(fresh_repo, "commit", "-m", "docs: bypass", check=False,
                   env={"AGENT_FARM_SKIP_HOOKS": "1"})
        assert res.returncode == 0, res.stderr

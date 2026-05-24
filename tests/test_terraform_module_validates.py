"""Tests that the infra/terraform/github module passes terraform validate.

Skips when the terraform binary is not found on PATH, so the suite stays
green in environments that have not installed Terraform.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest


TF_MODULE = pathlib.Path(__file__).resolve().parent.parent / "infra" / "terraform" / "github"


@pytest.fixture(scope="module")
def terraform_bin() -> str:
    """Return the path to the terraform binary, or skip the test."""
    binary = shutil.which("terraform")
    if binary is None:
        pytest.skip("terraform binary not found on PATH; install Terraform to run this test")
    return binary


def _run(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_terraform_module_dir_exists() -> None:
    """Sanity: the module directory must exist before anything else."""
    assert TF_MODULE.is_dir(), f"Terraform module not found at {TF_MODULE}"


def test_required_files_present() -> None:
    """All required HCL files must be present."""
    required = ["main.tf", "variables.tf", "repos.tf", "versions.tf", "outputs.tf"]
    missing = [f for f in required if not (TF_MODULE / f).exists()]
    assert not missing, f"Missing Terraform files: {missing}"


def test_terraform_init(terraform_bin: str) -> None:
    """terraform init must succeed with -backend=false."""
    result = _run(
        [terraform_bin, "init", "-backend=false", "-no-color"],
        cwd=TF_MODULE,
    )
    assert result.returncode == 0, (
        f"terraform init failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_terraform_validate(terraform_bin: str) -> None:
    """terraform validate must report 'Success! The configuration is valid.'"""
    # Ensure init has run (idempotent).
    _run([terraform_bin, "init", "-backend=false", "-no-color"], cwd=TF_MODULE)

    result = _run(
        [terraform_bin, "validate", "-no-color"],
        cwd=TF_MODULE,
    )
    assert result.returncode == 0, (
        f"terraform validate failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "Success" in result.stdout, (
        f"Unexpected validate output:\n{result.stdout}"
    )

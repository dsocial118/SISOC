"""Tests unitarios para el helper de lint de PR."""

from pathlib import Path
import subprocess

from scripts.ci import pr_lint_tools


def _completed_process(*args, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args, returncode, stdout, stderr)


def test_get_changed_files_usa_fallback_si_falta_el_base_sha(monkeypatch):
    """No rompe el job cuando Actions hace checkout shallow del merge commit."""

    monkeypatch.setattr(
        pr_lint_tools,
        "get_diff_range",
        lambda: ("base-sha", "head-sha"),
    )

    def fake_run_git_command(*args, check=True):
        if args == ("rev-parse", "--verify", "base-sha^{commit}"):
            return _completed_process(*args, returncode=1, stderr="fatal: bad object")
        if args == ("show", "--pretty=", "--name-only", "HEAD"):
            return _completed_process(
                *args,
                stdout="scripts/ci/pr_lint_tools.py\nVAT/serializers.py\n",
            )
        raise AssertionError(f"Comando git no esperado: {args}")

    monkeypatch.setattr(pr_lint_tools, "run_git_command", fake_run_git_command)

    assert pr_lint_tools.get_changed_files() == [
        Path("scripts/ci/pr_lint_tools.py"),
        Path("VAT/serializers.py"),
    ]

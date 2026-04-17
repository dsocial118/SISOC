"""Tests unitarios para el helper de lint de PR."""

from pathlib import Path
import subprocess

from scripts.ci import pr_lint_tools


def _completed_process(*args, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args, returncode, stdout, stderr)


def test_get_changed_files_usa_api_del_pr_si_falta_el_rango_git(monkeypatch):
    """Prioriza la API del PR cuando Actions no tiene el rango base/head local."""

    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setattr(
        pr_lint_tools,
        "get_diff_range",
        lambda: ("base-sha", "head-sha"),
    )
    monkeypatch.setattr(
        pr_lint_tools,
        "read_event_payload",
        lambda: {
            "pull_request": {"url": "https://api.github.test/repos/org/repo/pulls/1"}
        },
    )

    def fake_run_git_command(*args, check=True):
        if args in (
            ("rev-parse", "--verify", "base-sha^{commit}"),
            ("rev-parse", "--verify", "head-sha^{commit}"),
        ):
            return _completed_process(*args, returncode=1, stderr="fatal: bad object")
        raise AssertionError(f"Comando git no esperado: {args}")

    monkeypatch.setattr(pr_lint_tools, "run_git_command", fake_run_git_command)
    monkeypatch.setattr(
        pr_lint_tools,
        "_fetch_github_json",
        lambda url: (
            [
                {"filename": "scripts/ci/pr_lint_tools.py"},
                {"filename": "VAT/serializers.py"},
            ]
            if "page=1" in url
            else []
        ),
    )

    assert pr_lint_tools.get_changed_files() == [
        Path("scripts/ci/pr_lint_tools.py"),
        Path("VAT/serializers.py"),
    ]


def test_get_changed_files_usa_fallback_si_falta_el_base_sha(monkeypatch):
    """No rompe el job cuando Actions hace checkout shallow del merge commit."""

    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setattr(
        pr_lint_tools,
        "get_diff_range",
        lambda: ("base-sha", "head-sha"),
    )
    monkeypatch.setattr(
        pr_lint_tools, "get_pull_request_changed_files_from_api", lambda: []
    )

    def fake_run_git_command(*args, check=True):
        if args in (
            ("rev-parse", "--verify", "base-sha^{commit}"),
            ("rev-parse", "--verify", "head-sha^{commit}"),
        ):
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

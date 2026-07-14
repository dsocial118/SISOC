import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = REPO_ROOT / "scripts" / "operacion" / "deploy_refresh.sh"
HTTPS_MOBILE_REMOTE = "https://github.com/dsocial118/SISOC-Mobile.git"


def _mobile_checkout(tmp_path: Path, remote: str) -> Path:
    checkout = tmp_path / "SISOC-Mobile"
    checkout.mkdir()
    (checkout / ".branch").write_text("main\n", encoding="utf-8")
    (checkout / ".origin").write_text(f"{remote}\n", encoding="utf-8")

    script = checkout / "scripts" / "operacion" / "deploy_refresh.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    return checkout


def _backend_checkout(tmp_path: Path) -> Path:
    checkout = tmp_path / "SISOC"
    checkout.mkdir()
    (checkout / ".branch").write_text("development\n", encoding="utf-8")

    script = checkout / "scripts" / "operacion" / "deploy_refresh.sh"
    script.parent.mkdir(parents=True)
    shutil.copyfile(DEPLOY_SCRIPT, script)
    (checkout / "docker-compose.deploy.yml").write_text(
        "services: {}\n",
        encoding="utf-8",
    )
    return checkout


def _fake_git(fake_bin: Path) -> None:
    git = fake_bin / "git"
    git.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

[[ "$1" == "-C" ]]
repo="$2"
shift 2

case "$1 ${2:-} ${3:-}" in
  "rev-parse --is-inside-work-tree ") exit 0 ;;
  "branch --show-current ") cat "$repo/.branch" ;;
  "remote get-url origin") cat "$repo/.origin" ;;
  "remote set-url origin") printf '%s\\n' "$4" > "$repo/.origin" ;;
  "fetch origin --prune") exit 0 ;;
  "pull --ff-only origin") exit 0 ;;
  *) printf 'git falso: comando inesperado: %s\\n' "$*" >&2; exit 2 ;;
esac
""",
        encoding="utf-8",
    )
    git.chmod(0o755)


def _run_deploy(
    tmp_path: Path,
    mobile_checkout: Path,
    *,
    dry_run: bool = True,
) -> subprocess.CompletedProcess[str]:
    backend_checkout = _backend_checkout(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("ENVIRONMENT=qa\n", encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _fake_git(fake_bin)
    docker = fake_bin / "docker"
    docker.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    docker.chmod(0o755)
    env = os.environ.copy()
    env["ENV_FILE"] = str(env_file)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"

    args = [
        "bash",
        str(backend_checkout / "scripts" / "operacion" / "deploy_refresh.sh"),
    ]
    if dry_run:
        args.append("--dry-run")
    args.extend(
        [
            "--yes",
            "--allow-dirty",
            "--allow-branch-mismatch",
            "--with-mobile",
            "--mobile-dir",
            str(mobile_checkout),
        ]
    )

    return subprocess.run(
        args,
        cwd=backend_checkout,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_mobile_ssh_origin_se_normaliza_a_https(tmp_path):
    checkout = _mobile_checkout(
        tmp_path,
        "git@github.com:dsocial118/SISOC-Mobile.git",
    )

    result = _run_deploy(tmp_path, checkout, dry_run=False)

    assert result.returncode == 0, result.stderr
    assert "Normalizando origin de SISOC-Mobile a HTTPS publica." in result.stdout
    assert (checkout / ".origin").read_text(encoding="utf-8").strip() == (
        HTTPS_MOBILE_REMOTE
    )


def test_mobile_https_origin_no_necesita_cambio(tmp_path):
    checkout = _mobile_checkout(tmp_path, HTTPS_MOBILE_REMOTE)

    result = _run_deploy(tmp_path, checkout)

    assert result.returncode == 0, result.stderr
    assert "remote set-url origin" not in result.stdout


def test_mobile_origin_desconocido_bloquea_antes_de_docker(tmp_path):
    checkout = _mobile_checkout(tmp_path, "https://example.com/otro/mobile.git")

    result = _run_deploy(tmp_path, checkout)

    assert result.returncode != 0
    assert "Origin inesperado para SISOC-Mobile" in result.stderr
    assert "docker compose" not in result.stdout

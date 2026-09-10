import os
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = REPO_ROOT / "scripts" / "operacion" / "deploy_refresh.sh"
HTTPS_MOBILE_REMOTE = "https://github.com/dsocial118/SISOC-Mobile.git"
EXPECTED_REVISION = "a" * 40


pytestmark = pytest.mark.skipif(
    os.name == "nt",
    reason="deploy_refresh.sh se prueba en un host Bash/Linux (WSL o CI)",
)


def _mobile_checkout(tmp_path: Path, remote: str) -> Path:
    checkout = tmp_path / "SISOC-Mobile"
    checkout.mkdir()
    (checkout / ".branch").write_text("main\n", encoding="utf-8")
    (checkout / ".origin").write_text(f"{remote}\n", encoding="utf-8")

    script = checkout / "scripts" / "operacion" / "deploy_refresh.sh"
    script.parent.mkdir(parents=True)
    script.write_bytes(b"#!/usr/bin/env bash\nexit 0\n")
    return checkout


def _backend_checkout(tmp_path: Path, *, include_celery: bool = True) -> Path:
    checkout = tmp_path / "SISOC"
    checkout.mkdir()
    (checkout / ".branch").write_text("development\n", encoding="utf-8")

    script = checkout / "scripts" / "operacion" / "deploy_refresh.sh"
    script.parent.mkdir(parents=True)
    script.write_bytes(DEPLOY_SCRIPT.read_bytes().replace(b"\r\n", b"\n"))
    if include_celery:
        (checkout / "docker-compose.celery.yml").write_text(
            "services: {}\n", encoding="utf-8"
        )
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
  "fetch origin --no-tags") exit "${FAKE_FETCH_ERROR:-0}" ;;
  "rev-parse FETCH_HEAD^{commit} ") printf '%s\\n' aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ;;
  "merge-base --is-ancestor HEAD") exit 0 ;;
  "merge --ff-only aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa") exit 0 ;;
  "rev-parse origin/development ") printf '%s\\n' "${FAKE_ORIGIN_SHA:-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}" ;;
  "rev-parse HEAD ") printf '%s\\n' "${FAKE_HEAD_SHA:-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}" ;;
  "merge --ff-only origin/development")
    if [[ "${FAKE_CREATE_CELERY_ON_MERGE:-0}" == "1" ]]; then
      printf 'services: {}\n' > "$repo/docker-compose.celery.yml"
    fi
    exit 0
    ;;
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
    expected_revision: str | None = None,
    origin_revision: str | None = None,
    backend_only: bool = False,
    backend_has_celery: bool = True,
    create_celery_on_merge: bool = False,
) -> subprocess.CompletedProcess[str]:
    backend_checkout = _backend_checkout(tmp_path, include_celery=backend_has_celery)
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
    if origin_revision:
        env["FAKE_ORIGIN_SHA"] = origin_revision
    if create_celery_on_merge:
        env["FAKE_CREATE_CELERY_ON_MERGE"] = "1"
    if dry_run:
        args.append("--dry-run")
    if backend_only:
        args.append("--without-mobile")
    if expected_revision:
        args.extend(["--expected-revision", expected_revision])
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


def test_mobile_ssh_origin_conserva_autenticacion(tmp_path):
    checkout = _mobile_checkout(
        tmp_path,
        "git@github.com:dsocial118/Espacios-Comunitarios.git",
    )

    result = _run_deploy(tmp_path, checkout, dry_run=False)

    assert result.returncode == 0, result.stderr
    assert "remote set-url" not in result.stdout
    assert (checkout / ".origin").read_text(encoding="utf-8").strip() == (
        "git@github.com:dsocial118/Espacios-Comunitarios.git"
    )


def test_mobile_fetch_fallido_bloquea_backend(tmp_path, monkeypatch):
    checkout = _mobile_checkout(tmp_path, HTTPS_MOBILE_REMOTE)
    monkeypatch.setenv("FAKE_FETCH_ERROR", "1")
    result = _run_deploy(tmp_path, checkout, dry_run=False)
    assert result.returncode != 0
    assert "docker compose" not in result.stdout


def test_backend_only_no_inspecciona_mobile(tmp_path):
    result = _run_deploy(tmp_path, tmp_path / "mobile-inexistente", backend_only=True)
    assert result.returncode == 0, result.stderr
    assert "fetch origin --no-tags main" not in result.stdout


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


def test_revision_esperada_desactualizada_bloquea_antes_de_docker(tmp_path):
    """No deja que un runner despliegue una revision distinta del evento."""

    checkout = _mobile_checkout(tmp_path, HTTPS_MOBILE_REMOTE)

    result = _run_deploy(
        tmp_path,
        checkout,
        expected_revision=EXPECTED_REVISION,
        origin_revision="b" * 40,
    )

    assert result.returncode != 0
    assert "La revision esperada" in result.stderr
    assert "docker compose" not in result.stdout


def test_revision_esperada_valida_se_registra_en_el_deploy(tmp_path):
    """Con el SHA esperado, el flujo conserva la trazabilidad de la revision."""

    checkout = _mobile_checkout(tmp_path, HTTPS_MOBILE_REMOTE)

    result = _run_deploy(
        tmp_path,
        checkout,
        expected_revision=EXPECTED_REVISION,
    )

    assert result.returncode == 0, result.stderr
    assert f"revision_verificada={EXPECTED_REVISION}" in result.stdout
    assert f"deployed_revision={EXPECTED_REVISION}" in result.stdout


def test_checkout_viejo_actualiza_antes_de_exigir_compose_celery(tmp_path):
    """Permite incorporar un compose nuevo sin interrumpir el deploy de HML."""

    checkout = _mobile_checkout(tmp_path, HTTPS_MOBILE_REMOTE)

    result = _run_deploy(
        tmp_path,
        checkout,
        dry_run=False,
        backend_only=True,
        backend_has_celery=False,
        create_celery_on_merge=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.index("merge --ff-only origin/development") < result.stdout.index(
        "docker compose -f"
    )

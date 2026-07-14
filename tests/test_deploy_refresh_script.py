import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = REPO_ROOT / "scripts" / "operacion" / "deploy_refresh.sh"
HTTPS_MOBILE_REMOTE = "https://github.com/dsocial118/SISOC-Mobile.git"


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def _mobile_checkout(tmp_path: Path, remote: str) -> Path:
    checkout = tmp_path / "SISOC-Mobile"
    checkout.mkdir()
    _git("init", "--initial-branch=main", cwd=checkout)
    _git("config", "user.name", "Test", cwd=checkout)
    _git("config", "user.email", "test@example.com", cwd=checkout)

    script = checkout / "scripts" / "operacion" / "deploy_refresh.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    _git("add", ".", cwd=checkout)
    _git("commit", "-m", "test fixture", cwd=checkout)
    _git("remote", "add", "origin", remote, cwd=checkout)
    return checkout


def _backend_checkout(tmp_path: Path) -> Path:
    checkout = tmp_path / "SISOC"
    checkout.mkdir()
    _git("init", "--initial-branch=development", cwd=checkout)
    _git("config", "user.name", "Test", cwd=checkout)
    _git("config", "user.email", "test@example.com", cwd=checkout)

    script = checkout / "scripts" / "operacion" / "deploy_refresh.sh"
    script.parent.mkdir(parents=True)
    shutil.copyfile(DEPLOY_SCRIPT, script)
    (checkout / "docker-compose.deploy.yml").write_text(
        "services: {}\n",
        encoding="utf-8",
    )
    _git("add", ".", cwd=checkout)
    _git("commit", "-m", "test fixture", cwd=checkout)
    remote = tmp_path / "backend-origin.git"
    _git("init", "--bare", str(remote), cwd=tmp_path)
    _git("remote", "add", "origin", str(remote), cwd=checkout)
    _git("push", "--set-upstream", "origin", "development", cwd=checkout)
    return checkout


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
    assert _git("remote", "get-url", "origin", cwd=checkout).stdout.strip() == (
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

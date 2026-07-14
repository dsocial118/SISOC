import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INFRA_DIR = REPO_ROOT / "scripts" / "infra"
PROD_SCRIPTS = [
    "backup_prod_configs.sh",
    "cleanup_prod_disk.sh",
    "healthcheck_prod.sh",
    "install_prod_maintenance.sh",
    "prepare_prod_mobile_checkout.sh",
    "prod_night_preflight.sh",
    "retire_prod_local_mysql_stage1.sh",
    "rollback_prod_mobile_checkout.sh",
    "rollback_prod_maintenance.sh",
    "verify_prod_release.sh",
]


def test_prod_infra_scripts_tienen_sintaxis_bash_valida():
    for script_name in PROD_SCRIPTS:
        result = subprocess.run(
            ["bash", "-n", f"scripts/infra/{script_name}"],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
        )

        assert result.returncode == 0, f"{script_name}: {result.stderr}"


def test_cleanup_prod_no_toca_volumenes_ni_contenedores():
    content = (INFRA_DIR / "cleanup_prod_disk.sh").read_text(encoding="utf-8")

    assert "docker image prune" in content
    assert "docker builder prune" in content
    assert "docker system prune" not in content
    assert "docker volume prune" not in content
    assert "down --volumes" not in content


def test_stage1_mysql_prod_no_purga_ni_borra_datadir():
    content = (INFRA_DIR / "retire_prod_local_mysql_stage1.sh").read_text(
        encoding="utf-8"
    )

    assert "systemctl stop mysql" in content
    assert "systemctl disable mysql" in content
    assert "rm -rf" not in content
    assert "DROP DATABASE" not in content.upper()
    assert "apt purge" not in content


def test_mantenimiento_prod_reemplaza_poda_root_por_cron_sin_privilegios():
    content = (INFRA_DIR / "install_prod_maintenance.sh").read_text(encoding="utf-8")

    assert "40 3 * * * $TARGET_BIN/cleanup_prod_disk.sh --apply --yes" in content
    assert 'crontab -u "$TARGET_USER" "$deploy_after"' in content
    assert 'logrotate -f -v "$LOGROTATE_FILE"' in content
    assert "PROD_DOCKER_IMAGE_RETENTION:-336h" in (
        INFRA_DIR / "cleanup_prod_disk.sh"
    ).read_text(encoding="utf-8")


def test_preparacion_mobile_acota_chown_y_guarda_rollback_completo():
    prepare = (INFRA_DIR / "prepare_prod_mobile_checkout.sh").read_text(
        encoding="utf-8"
    )
    rollback = (INFRA_DIR / "rollback_prod_mobile_checkout.sh").read_text(
        encoding="utf-8"
    )

    assert 'chown -R "$TARGET_USER:$TARGET_GROUP" "$MOBILE_ROOT"' in prepare
    assert prepare.count("chown -R") == 1
    assert 'getfacl -R -p "$MOBILE_ROOT"' in prepare
    assert 'setfacl --restore="$BACKUP_DIR/mobile.acl-ownership.before"' in rollback
    assert '"$(cat "$BACKUP_DIR/mobile-origin.before")"' in rollback

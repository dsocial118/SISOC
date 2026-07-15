#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HOSTNAME="${PROD_EXPECTED_HOSTNAME:-mdsldmz-ssies}"
TARGET_USER="${PROD_MAINTENANCE_USER:-sisoc-deploy}"
TARGET_HOME="${PROD_MAINTENANCE_HOME:-/home/sisoc-deploy}"
TARGET_BIN="$TARGET_HOME/bin"
MOBILE_ENV="${MOBILE_ENV:-/sisoc/SISOC-Mobile/.env}"
LOGROTATE_FILE="/etc/logrotate.d/sisoc-nginx"
BACKUP_DIR=""
APPLY=0
ASSUME_YES=0
SCRIPTS=(healthcheck_prod.sh cleanup_prod_disk.sh)

usage() {
  cat <<'USAGE'
Uso:
  rollback_prod_maintenance.sh --backup-dir PATH [--apply] [--yes]

Restaura crontabs, metadata/contenido del .env mobile, logrotate, scripts
instalados y enablement previo de apache2/sisoc.service desde un backup creado
por install_prod_maintenance.sh. No revierte rotaciones ya hechas ni MySQL.
USAGE
}

log() {
  printf '[%s] %s\n' "$SCRIPT_NAME" "$*"
}

fail() {
  log "ERROR: $*" >&2
  exit 1
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --backup-dir)
        shift
        [[ $# -gt 0 ]] || fail "--backup-dir requiere valor."
        BACKUP_DIR="$1"
        ;;
      --apply) APPLY=1 ;;
      --yes) ASSUME_YES=1 ;;
      -h|--help) usage; exit 0 ;;
      *) fail "Opcion no reconocida: $1" ;;
    esac
    shift
  done
}

main() {
  local script apache_before sisoc_before rollback_dir

  parse_args "$@"
  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  [[ "$BACKUP_DIR" == /var/backups/sisoc/night-maintenance/prod/* ]] \
    || fail "Backup fuera de la raiz productiva esperada."
  [[ -d "$BACKUP_DIR" ]] || fail "No existe $BACKUP_DIR"
  [[ -r "$BACKUP_DIR/status/root.crontab.before" ]] || fail "Falta root crontab."
  [[ -r "$BACKUP_DIR/status/deploy-user.crontab.before" ]] || fail "Falta crontab de deploy."
  [[ -r "$BACKUP_DIR/sensitive/mobile.env.before" ]] || fail "Falta backup de .env mobile."
  [[ -r "$BACKUP_DIR/status/legacy.enabled.before.txt" ]] || fail "Falta metadata systemd."
  (cd "$BACKUP_DIR" && sha256sum -c SHA256SUMS >/dev/null) \
    || fail "Checksum del backup invalido."

  apache_before="$(sed -n 's/^apache2=//p' "$BACKUP_DIR/status/legacy.enabled.before.txt")"
  sisoc_before="$(sed -n 's/^sisoc.service=//p' "$BACKUP_DIR/status/legacy.enabled.before.txt")"
  log "Plan: restaurar configuracion desde $BACKUP_DIR"
  log "apache2_before=$apache_before sisoc_before=$sisoc_before"

  if [[ "$APPLY" -eq 0 ]]; then
    log "Modo informativo; no se modifico el host."
    exit 0
  fi
  if [[ "$ASSUME_YES" -eq 0 ]]; then
    read -r -p "Restaurar mantenimiento host-side desde este backup? [y/N] " answer
    case "$answer" in
      y|Y|yes|YES|si|SI) ;;
      *) fail "Operacion cancelada." ;;
    esac
  fi

  crontab "$BACKUP_DIR/status/root.crontab.before"
  crontab -u "$TARGET_USER" "$BACKUP_DIR/status/deploy-user.crontab.before"
  cp -a -- "$BACKUP_DIR/sensitive/mobile.env.before" "$MOBILE_ENV"

  rollback_dir="$BACKUP_DIR/rollback-$(date +%Y%m%d_%H%M%S)"
  install -d -o root -g root -m 700 "$rollback_dir"
  if [[ -e "$BACKUP_DIR/config/sisoc-nginx.before" ]]; then
    cp -a -- "$BACKUP_DIR/config/sisoc-nginx.before" "$LOGROTATE_FILE"
  elif [[ -e "$LOGROTATE_FILE" ]]; then
    mv -- "$LOGROTATE_FILE" "$rollback_dir/sisoc-nginx.disabled"
  fi

  for script in "${SCRIPTS[@]}"; do
    if [[ -e "$BACKUP_DIR/config/installed-before/$script" ]]; then
      cp -a -- "$BACKUP_DIR/config/installed-before/$script" "$TARGET_BIN/$script"
    elif [[ -e "$TARGET_BIN/$script" ]]; then
      mv -- "$TARGET_BIN/$script" "$rollback_dir/$script.disabled"
    fi
  done

  [[ "$apache_before" == enabled ]] && systemctl enable apache2 >/dev/null || true
  [[ "$sisoc_before" == enabled ]] && systemctl enable sisoc.service >/dev/null || true
  nginx -t
  bash "$SCRIPT_DIR/healthcheck_prod.sh"
  printf 'rollback_applied_at=%s\nsource_backup=%s\n' \
    "$(date --iso-8601=seconds)" "$BACKUP_DIR" \
    > "$rollback_dir/ROLLBACK_APPLIED"
  chmod 600 "$rollback_dir/ROLLBACK_APPLIED"
  log "Rollback host-side aplicado. No se iniciaron servicios legacy."
}

main "$@"

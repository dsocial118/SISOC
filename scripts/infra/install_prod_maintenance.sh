#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HOSTNAME="${PROD_EXPECTED_HOSTNAME:-mdsldmz-ssies}"
TARGET_USER="${PROD_MAINTENANCE_USER:-sisoc-deploy}"
TARGET_GROUP="${PROD_MAINTENANCE_GROUP:-sisoc-deploy}"
TARGET_HOME="${PROD_MAINTENANCE_HOME:-/home/sisoc-deploy}"
TARGET_BIN="$TARGET_HOME/bin"
MOBILE_ENV="${MOBILE_ENV:-/sisoc/SISOC-Mobile/.env}"
LOGROTATE_FILE="/etc/logrotate.d/sisoc-nginx"
OLD_ROOT_DOCKER='0 3 * * 0 /usr/bin/docker system prune -af --filter "until=24h" --volumes'
DEPLOY_CRON_MARKER="# SISOC PROD conservative Docker cleanup"
DEPLOY_CRON_LINE="40 3 * * * $TARGET_BIN/cleanup_prod_disk.sh --apply --yes >/dev/null 2>&1"
SCRIPTS=(healthcheck_prod.sh cleanup_prod_disk.sh)
APPLY=0
ASSUME_YES=0
ROTATE_LOGS_NOW=0
BACKUP_DIR=""
MUTATION_STARTED=0
LOGROTATE_EXISTED=0
APACHE_WAS_ENABLED=0
SISOC_WAS_ENABLED=0

usage() {
  cat <<'USAGE'
Uso:
  install_prod_maintenance.sh [--apply] [--yes] [--rotate-logs-now]

Sin --apply ejecuta preflight read-only. Con --apply:
  - crea backup root-only;
  - retira solo la poda Docker root con --volumes y dos cron legacy rotos;
  - instala limpieza diaria conservadora como sisoc-deploy;
  - instala logrotate para /sisoc/logs/nginx;
  - restringe .env mobile a root:sisoc-deploy 640;
  - deshabilita apache2 y sisoc.service solo si no estan activos.

--rotate-logs-now aplica solo la nueva regla NGINX durante esta ejecucion.
No toca TLS, media, DB, paquetes, volumenes ni checkouts historicos.
USAGE
}

log() {
  printf '[%s] %s\n' "$SCRIPT_NAME" "$*"
}

fail() {
  log "ERROR: $*" >&2
  exit 1
}

generate_logrotate() {
  cat <<'LOGROTATE'
/sisoc/logs/nginx/*.log {
    daily
    maxsize 100M
    rotate 30
    missingok
    notifempty
    compress
    delaycompress
    create 0640 www-data root
    sharedscripts
    postrotate
        if [ -s /run/nginx.pid ]; then
            kill -USR1 "$(cat /run/nginx.pid)"
        fi
    endscript
}
LOGROTATE
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --apply) APPLY=1 ;;
      --yes) ASSUME_YES=1 ;;
      --rotate-logs-now) ROTATE_LOGS_NOW=1 ;;
      -h|--help) usage; exit 0 ;;
      *) fail "Opcion no reconocida: $1" ;;
    esac
    shift
  done
}

service_inactive_or_failed() {
  local state
  state="$(systemctl is-active "$1" 2>/dev/null || true)"
  [[ "$state" == "inactive" || "$state" == "failed" ]]
}

preflight() {
  local script mobile_metadata root_cron deploy_cron
  local old_count home_legacy_count opt_legacy_count deploy_refs deploy_exact

  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  id "$TARGET_USER" >/dev/null 2>&1 || fail "No existe $TARGET_USER."
  id -nG "$TARGET_USER" | tr ' ' '\n' | grep -qx docker \
    || fail "$TARGET_USER no pertenece al grupo docker."
  [[ -f "$MOBILE_ENV" ]] || fail "No existe $MOBILE_ENV"
  [[ -d /sisoc/logs/nginx ]] || fail "No existe /sisoc/logs/nginx"
  command -v logrotate >/dev/null || fail "logrotate no esta disponible."
  command -v nginx >/dev/null || fail "nginx no esta disponible."

  for script in "${SCRIPTS[@]}" backup_prod_configs.sh; do
    [[ -r "$SCRIPT_DIR/$script" ]] || fail "Falta $SCRIPT_DIR/$script"
    bash -n "$SCRIPT_DIR/$script" || fail "Sintaxis invalida: $script"
  done

  bash "$SCRIPT_DIR/healthcheck_prod.sh"
  runuser -u "$TARGET_USER" -- docker info >/dev/null \
    || fail "$TARGET_USER no puede consultar Docker."
  nginx -t

  root_cron="$(mktemp)"
  deploy_cron="$(mktemp)"
  crontab -l > "$root_cron" 2>/dev/null || :
  crontab -u "$TARGET_USER" -l > "$deploy_cron" 2>/dev/null || :

  old_count="$(grep -Fxc -- "$OLD_ROOT_DOCKER" "$root_cron" || true)"
  home_legacy_count="$(grep -Fc '/home/admin-ssies/SISOC-Backoffice' "$root_cron" || true)"
  opt_legacy_count="$(grep -Fc '/opt/ssies/SISOC-Backoffice' "$root_cron" || true)"
  deploy_refs="$(grep -Fc "$TARGET_BIN/cleanup_prod_disk.sh" "$deploy_cron" || true)"
  deploy_exact="$(grep -Fxc "$DEPLOY_CRON_LINE" "$deploy_cron" || true)"

  if [[ "$old_count" -eq 1 && "$home_legacy_count" -eq 1 && "$opt_legacy_count" -eq 1 && "$deploy_refs" -eq 0 ]]; then
    log "Cron en estado inicial esperado."
  elif [[ "$old_count" -eq 0 && "$home_legacy_count" -eq 0 && "$opt_legacy_count" -eq 0 && "$deploy_refs" -eq 1 && "$deploy_exact" -eq 1 ]]; then
    log "Cron ya esta en estado instalado esperado."
  else
    fail "Conteos de cron inesperados; no se modificara ningun crontab."
  fi

  [[ ! -e /home/admin-ssies/SISOC-Backoffice ]] \
    || fail "El path legacy de /home volvio a existir."
  [[ ! -e /opt/ssies/SISOC-Backoffice ]] \
    || fail "El path legacy de /opt volvio a existir."
  service_inactive_or_failed apache2 || fail "apache2 esta activo; no se deshabilitara."
  service_inactive_or_failed sisoc.service || fail "sisoc.service esta activo."

  mobile_metadata="$(stat -c '%U:%G:%a' "$MOBILE_ENV")"
  case "$mobile_metadata" in
    root:root:664|root:sisoc-deploy:640) ;;
    *) fail "Metadata inesperada en .env mobile: $mobile_metadata" ;;
  esac

  if [[ -e "$LOGROTATE_FILE" ]]; then
    LOGROTATE_EXISTED=1
    generate_logrotate | cmp -s - "$LOGROTATE_FILE" \
      || fail "$LOGROTATE_FILE ya existe con contenido distinto."
  fi
  systemctl is-enabled --quiet apache2 && APACHE_WAS_ENABLED=1 || true
  systemctl is-enabled --quiet sisoc.service && SISOC_WAS_ENABLED=1 || true
  rm -f -- "$root_cron" "$deploy_cron"

  log "Preflight OK: cron, servicios, permisos, NGINX, Docker y health."
}

rollback_on_error() {
  local rc=$?
  trap - EXIT
  if [[ "$MUTATION_STARTED" -eq 1 && -n "$BACKUP_DIR" ]]; then
    log "Fallo durante instalacion; restaurando cambios reversibles."
    crontab "$BACKUP_DIR/status/root.crontab.before" || true
    crontab -u "$TARGET_USER" "$BACKUP_DIR/status/deploy-user.crontab.before" || true
    cp -a -- "$BACKUP_DIR/sensitive/mobile.env.before" "$MOBILE_ENV" || true
    if [[ "$LOGROTATE_EXISTED" -eq 1 ]]; then
      cp -a -- "$BACKUP_DIR/config/sisoc-nginx.before" "$LOGROTATE_FILE" || true
    elif [[ -e "$LOGROTATE_FILE" ]]; then
      install -d -m 700 "$BACKUP_DIR/rollback"
      mv -- "$LOGROTATE_FILE" "$BACKUP_DIR/rollback/sisoc-nginx.disabled" || true
    fi
    [[ "$APACHE_WAS_ENABLED" -eq 1 ]] && systemctl enable apache2 >/dev/null 2>&1 || true
    [[ "$SISOC_WAS_ENABLED" -eq 1 ]] && systemctl enable sisoc.service >/dev/null 2>&1 || true
    for script in "${SCRIPTS[@]}"; do
      if [[ -e "$BACKUP_DIR/config/installed-before/$script" ]]; then
        cp -a -- "$BACKUP_DIR/config/installed-before/$script" "$TARGET_BIN/$script" || true
      elif [[ -e "$TARGET_BIN/$script" ]]; then
        install -d -m 700 "$BACKUP_DIR/rollback"
        mv -- "$TARGET_BIN/$script" "$BACKUP_DIR/rollback/$script.disabled" || true
      fi
    done
    bash "$SCRIPT_DIR/healthcheck_prod.sh" || true
  fi
  exit "$rc"
}

install_cron_and_scripts() {
  local script root_after deploy_after old_count

  install -d -o "$TARGET_USER" -g "$TARGET_GROUP" -m 750 "$TARGET_BIN"
  for script in "${SCRIPTS[@]}"; do
    if [[ -e "$TARGET_BIN/$script" ]]; then
      install -d -m 700 "$BACKUP_DIR/config/installed-before"
      cp -a -- "$TARGET_BIN/$script" "$BACKUP_DIR/config/installed-before/$script"
    fi
    install -o "$TARGET_USER" -g "$TARGET_GROUP" -m 750 \
      "$SCRIPT_DIR/$script" "$TARGET_BIN/$script"
  done

  root_after="$BACKUP_DIR/status/root.crontab.after"
  deploy_after="$BACKUP_DIR/status/deploy-user.crontab.after"
  old_count="$(grep -Fxc -- "$OLD_ROOT_DOCKER" "$BACKUP_DIR/status/root.crontab.before" || true)"

  if [[ "$old_count" -eq 1 ]]; then
    awk -v old="$OLD_ROOT_DOCKER" '
      $0 == old { next }
      /\/home\/admin-ssies\/SISOC-Backoffice\/cron_logs\/borrar_logs.py/ { next }
      /cd \/opt\/ssies\/SISOC-Backoffice .*purge_auditlog/ { next }
      { print }
    ' "$BACKUP_DIR/status/root.crontab.before" > "$root_after"
  else
    cp -- "$BACKUP_DIR/status/root.crontab.before" "$root_after"
  fi

  cp -- "$BACKUP_DIR/status/deploy-user.crontab.before" "$deploy_after"
  if ! grep -Fqx "$DEPLOY_CRON_LINE" "$deploy_after"; then
    printf '\n%s\n%s\n' "$DEPLOY_CRON_MARKER" "$DEPLOY_CRON_LINE" >> "$deploy_after"
  fi

  [[ "$(grep -Fc -- '--volumes' "$root_after" || true)" -eq 0 ]] \
    || fail "El root cron propuesto conserva --volumes."
  [[ "$(grep -Fc '/home/admin-ssies/SISOC-Backoffice' "$root_after" || true)" -eq 0 ]] \
    || fail "El root cron propuesto conserva el path legacy de /home."
  [[ "$(grep -Fc '/opt/ssies/SISOC-Backoffice' "$root_after" || true)" -eq 0 ]] \
    || fail "El root cron propuesto conserva el path legacy de /opt."
  [[ "$(grep -Fxc "$DEPLOY_CRON_LINE" "$deploy_after" || true)" -eq 1 ]] \
    || fail "El cron de mantenimiento no quedaria exactamente una vez."

  chmod 600 "$root_after" "$deploy_after"
  crontab "$root_after"
  crontab -u "$TARGET_USER" "$deploy_after"
}

apply_changes() {
  local timestamp logrotate_tmp

  timestamp="$(date +%Y%m%d_%H%M%S)"
  BACKUP_DIR="/var/backups/sisoc/night-maintenance/prod/$timestamp"
  BACKUP_DIR="$BACKUP_DIR" bash "$SCRIPT_DIR/backup_prod_configs.sh"

  MUTATION_STARTED=1
  trap rollback_on_error EXIT
  install_cron_and_scripts

  logrotate_tmp="$(mktemp)"
  generate_logrotate > "$logrotate_tmp"
  install -o root -g root -m 644 "$logrotate_tmp" "$LOGROTATE_FILE"
  rm -f -- "$logrotate_tmp"
  logrotate -d "$LOGROTATE_FILE" >/dev/null

  chown root:"$TARGET_GROUP" "$MOBILE_ENV"
  chmod 640 "$MOBILE_ENV"
  runuser -u "$TARGET_USER" -- test -r "$MOBILE_ENV"
  runuser -u "$TARGET_USER" -- docker compose \
    -f /sisoc/SISOC-Mobile/compose.prod.yaml \
    --project-directory /sisoc/SISOC-Mobile config --services >/dev/null

  systemctl disable apache2 sisoc.service >/dev/null
  if [[ "$ROTATE_LOGS_NOW" -eq 1 ]]; then
    logrotate -f -v "$LOGROTATE_FILE"
  fi

  runuser -u "$TARGET_USER" -- "$TARGET_BIN/healthcheck_prod.sh"
  runuser -u "$TARGET_USER" -- "$TARGET_BIN/cleanup_prod_disk.sh"
  [[ "$(crontab -u "$TARGET_USER" -l | grep -Fxc "$DEPLOY_CRON_LINE" || true)" -eq 1 ]] \
    || fail "No quedo instalado el cron de mantenimiento."
  [[ "$(crontab -l | grep -Fc -- '--volumes' || true)" -eq 0 ]] \
    || fail "Root cron todavia contiene --volumes."
  systemctl is-enabled --quiet apache2 && fail "apache2 sigue habilitado."
  systemctl is-enabled --quiet sisoc.service && fail "sisoc.service sigue habilitado."
  [[ "$(stat -c '%U:%G:%a' "$MOBILE_ENV")" == "root:$TARGET_GROUP:640" ]] \
    || fail "Metadata final inesperada en .env mobile."

  printf 'applied_at=%s\nbackup_dir=%s\nlogs_rotated_now=%s\n' \
    "$(date --iso-8601=seconds)" "$BACKUP_DIR" "$ROTATE_LOGS_NOW" \
    > "$BACKUP_DIR/MAINTENANCE_APPLIED"
  chmod 600 "$BACKUP_DIR/MAINTENANCE_APPLIED"
  (
    cd "$BACKUP_DIR"
    find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum
  ) > "$BACKUP_DIR/SHA256SUMS"

  MUTATION_STARTED=0
  trap - EXIT
  log "Mantenimiento instalado y validado."
  printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
}

main() {
  parse_args "$@"
  preflight

  if [[ "$APPLY" -eq 0 ]]; then
    log "Modo read-only. Use --apply solo dentro de la ventana aprobada."
    exit 0
  fi
  if [[ "$ASSUME_YES" -eq 0 ]]; then
    read -r -p "Aplicar mantenimiento host-side reversible en produccion? [y/N] " answer
    case "$answer" in
      y|Y|yes|YES|si|SI) ;;
      *) fail "Operacion cancelada." ;;
    esac
  fi
  apply_changes
}

main "$@"

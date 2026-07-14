#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_HOSTNAME="${HML_EXPECTED_HOSTNAME:-ldmzssies-homolo}"
TARGET_USER="${HML_MAINTENANCE_USER:-sisoc-deploy}"
TARGET_GROUP="${HML_MAINTENANCE_GROUP:-sisoc-deploy}"
TARGET_HOME="${HML_MAINTENANCE_HOME:-/home/sisoc-deploy}"
TARGET_BIN="$TARGET_HOME/bin"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$TARGET_HOME/backups/infra/hml/cron-install-$TIMESTAMP"
CRON_MARKER="# SISOC HML conservative Docker cleanup"
CRON_LINE="20 3 * * 0 $TARGET_BIN/cleanup_hml_disk.sh --apply --yes >/dev/null 2>&1"
SCRIPTS=(
  backup_hml_configs.sh
  cleanup_hml_disk.sh
  healthcheck_hml.sh
  show_hml_status.sh
)

log() {
  printf '[install_hml_maintenance.sh] %s\n' "$*"
}

fail() {
  log "ERROR: $*" >&2
  exit 1
}

main() {
  local script current_cron cron_references exact_cron cron_already=0

  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  id "$TARGET_USER" >/dev/null 2>&1 || fail "No existe $TARGET_USER."
  id -nG "$TARGET_USER" | tr ' ' '\n' | grep -qx docker \
    || fail "$TARGET_USER no pertenece al grupo docker."

  for script in "${SCRIPTS[@]}"; do
    [[ -r "$SOURCE_DIR/$script" ]] || fail "Falta $SOURCE_DIR/$script"
    bash -n "$SOURCE_DIR/$script" || fail "Sintaxis invalida: $script"
  done

  install -d -o "$TARGET_USER" -g "$TARGET_GROUP" -m 750 "$TARGET_BIN"
  install -d -o "$TARGET_USER" -g "$TARGET_GROUP" -m 700 \
    "$BACKUP_DIR" "$BACKUP_DIR/sources" "$BACKUP_DIR/installed-before" \
    "$BACKUP_DIR/status"

  current_cron="$BACKUP_DIR/status/crontab.before.txt"
  crontab -u "$TARGET_USER" -l > "$current_cron" 2>/dev/null || :
  chmod 600 "$current_cron"

  cron_references="$(grep -Fc "$TARGET_BIN/cleanup_hml_disk.sh" "$current_cron" || true)"
  exact_cron="$(grep -Fxc "$CRON_LINE" "$current_cron" || true)"
  if (( cron_references > 0 )); then
    [[ "$cron_references" -eq 1 && "$exact_cron" -eq 1 ]] \
      || fail "Ya existe una entrada de mantenimiento distinta; no se modifica cron."
    cron_already=1
  fi

  for script in "${SCRIPTS[@]}"; do
    install -o "$TARGET_USER" -g "$TARGET_GROUP" -m 600 \
      "$SOURCE_DIR/$script" "$BACKUP_DIR/sources/$script"
    if [[ -e "$TARGET_BIN/$script" ]]; then
      cp -a -- "$TARGET_BIN/$script" "$BACKUP_DIR/installed-before/$script"
    fi
    install -o "$TARGET_USER" -g "$TARGET_GROUP" -m 750 \
      "$SOURCE_DIR/$script" "$TARGET_BIN/$script"
  done

  runuser -u "$TARGET_USER" -- "$TARGET_BIN/healthcheck_hml.sh"
  runuser -u "$TARGET_USER" -- "$TARGET_BIN/cleanup_hml_disk.sh"

  cp -- "$current_cron" "$BACKUP_DIR/status/crontab.after.txt"
  if [[ "$cron_already" -eq 0 ]]; then
    printf '\n%s\n%s\n' "$CRON_MARKER" "$CRON_LINE" \
      >> "$BACKUP_DIR/status/crontab.after.txt"
  fi
  chmod 600 "$BACKUP_DIR/status/crontab.after.txt"

  if ! crontab -u "$TARGET_USER" "$BACKUP_DIR/status/crontab.after.txt"; then
    crontab -u "$TARGET_USER" "$current_cron" || true
    fail "Fallo instalando cron; se intento restaurar el anterior."
  fi

  exact_cron="$(crontab -u "$TARGET_USER" -l | grep -Fxc "$CRON_LINE" || true)"
  cron_references="$(crontab -u "$TARGET_USER" -l | grep -Fc "$TARGET_BIN/cleanup_hml_disk.sh" || true)"
  if [[ "$exact_cron" -ne 1 || "$cron_references" -ne 1 ]]; then
    crontab -u "$TARGET_USER" "$current_cron" || true
    fail "Verificacion cron invalida; se restauro el anterior."
  fi

  chown -R "$TARGET_USER:$TARGET_GROUP" "$BACKUP_DIR"
  find "$BACKUP_DIR" -type d -exec chmod 700 {} +
  find "$BACKUP_DIR" -type f -exec chmod 600 {} +

  for script in "${SCRIPTS[@]}"; do
    cmp -s "$SOURCE_DIR/$script" "$TARGET_BIN/$script" \
      || fail "La copia instalada difiere: $script"
  done

  log "Instalacion validada."
  printf 'TARGET_BIN=%s\n' "$TARGET_BIN"
  printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
  printf 'CRON_ENTRIES=%s\n' "$exact_cron"
}

main "$@"

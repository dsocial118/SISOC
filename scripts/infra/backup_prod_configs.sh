#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
EXPECTED_HOSTNAME="${PROD_EXPECTED_HOSTNAME:-mdsldmz-ssies}"
APP_ROOT="${APP_ROOT:-/sisoc/SISOC}"
MOBILE_ROOT="${MOBILE_ROOT:-/sisoc/SISOC-Mobile}"
TARGET_USER="${PROD_MAINTENANCE_USER:-sisoc-deploy}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/sisoc/night-maintenance/prod/$TIMESTAMP}"
RUNNER_UNIT="${PROD_RUNNER_UNIT:-actions.runner.dsocial118-SISOC.sisoc-produccion.service}"

umask 077

log() {
  printf '[%s] %s\n' "$SCRIPT_NAME" "$*"
}

fail() {
  log "ERROR: $*" >&2
  exit 1
}

copy_if_present() {
  local source="$1" destination="$2"
  if [[ -e "$source" || -L "$source" ]]; then
    mkdir -p "$(dirname "$destination")"
    cp -a -- "$source" "$destination"
  else
    printf '%s\n' "$source" >> "$BACKUP_DIR/MISSING.txt"
  fi
}

export_env_keys() {
  local source="$1" destination="$2"
  if [[ -r "$source" ]]; then
    sed -nE 's/^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=.*$/\2=/p' \
      "$source" > "$destination"
  else
    printf '%s\n' "$source" >> "$BACKUP_DIR/MISSING.txt"
  fi
}

main() {
  local relative

  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  id "$TARGET_USER" >/dev/null 2>&1 || fail "No existe $TARGET_USER."
  git -c safe.directory="$APP_ROOT" -C "$APP_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || fail "No se encontro el checkout backend."
  git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || fail "No se encontro el checkout mobile."
  [[ ! -e "$BACKUP_DIR" ]] || fail "El backup ya existe: $BACKUP_DIR"

  install -d -o root -g root -m 700 \
    "$BACKUP_DIR" \
    "$BACKUP_DIR/config" \
    "$BACKUP_DIR/docker" \
    "$BACKUP_DIR/git" \
    "$BACKUP_DIR/sensitive" \
    "$BACKUP_DIR/status"

  copy_if_present /etc/nginx "$BACKUP_DIR/config/nginx"
  copy_if_present /etc/logrotate.d/sisoc-nginx \
    "$BACKUP_DIR/config/sisoc-nginx.before"
  copy_if_present /etc/mysql "$BACKUP_DIR/config/mysql"
  copy_if_present /etc/systemd/system/sisoc.service \
    "$BACKUP_DIR/config/sisoc.service"
  copy_if_present "/etc/systemd/system/$RUNNER_UNIT" \
    "$BACKUP_DIR/config/$RUNNER_UNIT"

  for relative in \
    .github/workflows/deploy.yml \
    docker-compose.deploy.yml \
    docker-compose.produccion.yml \
    docker/django/Dockerfile \
    docker/django/entrypoint.py \
    scripts/operacion/deploy_refresh.sh \
    scripts/crontab; do
    copy_if_present "$APP_ROOT/$relative" "$BACKUP_DIR/config/repo/$relative"
  done
  copy_if_present "$MOBILE_ROOT/compose.prod.yaml" \
    "$BACKUP_DIR/config/mobile/compose.prod.yaml"

  export_env_keys "$APP_ROOT/.env" "$BACKUP_DIR/config/backend.env.keys"
  export_env_keys "$MOBILE_ROOT/.env" "$BACKUP_DIR/config/mobile.env.keys"
  copy_if_present "$MOBILE_ROOT/.env" "$BACKUP_DIR/sensitive/mobile.env.before"
  git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" remote get-url origin \
    > "$BACKUP_DIR/sensitive/mobile-origin.before"
  chmod 600 "$BACKUP_DIR/sensitive/mobile.env.before" 2>/dev/null || true
  stat -c 'path=%n owner=%U:%G mode=%a' "$APP_ROOT/.env" "$MOBILE_ROOT/.env" \
    > "$BACKUP_DIR/status/env.metadata.before.txt"

  crontab -l > "$BACKUP_DIR/status/root.crontab.before" 2>/dev/null || :
  crontab -u "$TARGET_USER" -l \
    > "$BACKUP_DIR/status/deploy-user.crontab.before" 2>/dev/null || :
  systemctl show apache2 sisoc.service nginx docker mysql "$RUNNER_UNIT" \
    -p Id -p ActiveState -p UnitFileState -p FragmentPath --no-pager \
    > "$BACKUP_DIR/status/systemd.before.txt"
  printf 'apache2=%s\n' "$(systemctl is-enabled apache2 2>/dev/null || true)" \
    > "$BACKUP_DIR/status/legacy.enabled.before.txt"
  printf 'sisoc.service=%s\n' "$(systemctl is-enabled sisoc.service 2>/dev/null || true)" \
    >> "$BACKUP_DIR/status/legacy.enabled.before.txt"
  ss -Hlnpt > "$BACKUP_DIR/status/listeners.before.txt"
  df -hT > "$BACKUP_DIR/status/df-hT.before.txt"
  df -ih > "$BACKUP_DIR/status/df-ih.before.txt"

  git -c safe.directory="$APP_ROOT" -C "$APP_ROOT" status --short --branch \
    > "$BACKUP_DIR/git/backend.status.before.txt"
  git -c safe.directory="$APP_ROOT" -C "$APP_ROOT" rev-parse HEAD \
    > "$BACKUP_DIR/git/backend.head.before.txt"
  git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" status --short --branch \
    > "$BACKUP_DIR/git/mobile.status.before.txt"
  git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" rev-parse HEAD \
    > "$BACKUP_DIR/git/mobile.head.before.txt"

  docker ps --no-trunc > "$BACKUP_DIR/docker/containers.before.txt"
  docker image ls --digests --no-trunc > "$BACKUP_DIR/docker/images.before.txt"
  docker system df -v > "$BACKUP_DIR/docker/system-df.before.txt"
  docker inspect --format '{{.Name}}|{{.Image}}|{{.RestartCount}}' \
    $(docker ps -q) > "$BACKUP_DIR/docker/runtime.before.txt"

  (
    cd "$BACKUP_DIR"
    find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum
  ) > "$BACKUP_DIR/SHA256SUMS"
  find "$BACKUP_DIR" -type d -exec chmod 700 {} +
  find "$BACKUP_DIR" -type f -exec chmod 600 {} +

  log "Backup root-only validado."
  printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
}

main "$@"

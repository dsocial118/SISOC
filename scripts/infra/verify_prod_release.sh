#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HOSTNAME="${PROD_EXPECTED_HOSTNAME:-mdsldmz-ssies}"
APP_ROOT="${APP_ROOT:-/sisoc/SISOC}"
MOBILE_ROOT="${MOBILE_ROOT:-/sisoc/SISOC-Mobile}"
TARGET_USER="${PROD_MAINTENANCE_USER:-sisoc-deploy}"
TARGET_GROUP="${PROD_MAINTENANCE_GROUP:-sisoc-deploy}"
TARGET_BIN="${PROD_MAINTENANCE_HOME:-/home/sisoc-deploy}/bin"
DEPLOY_CRON_LINE="40 3 * * * $TARGET_BIN/cleanup_prod_disk.sh --apply --yes >/dev/null 2>&1"
EXPECTED_BACKEND_SHA=""
EXPECTED_MOBILE_SHA=""

usage() {
  cat <<'USAGE'
Uso:
  verify_prod_release.sh --backend-sha SHA --mobile-sha SHA

Verificacion read-only final. Los SHA deben registrarse antes de aprobar el
Environment production. No acepta prefijos ambiguos ni modifica servicios.
USAGE
}

fail() {
  printf '[%s] ERROR: %s\n' "$SCRIPT_NAME" "$*" >&2
  exit 1
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --backend-sha)
        shift
        [[ $# -gt 0 ]] || fail "--backend-sha requiere valor."
        EXPECTED_BACKEND_SHA="$1"
        ;;
      --mobile-sha)
        shift
        [[ $# -gt 0 ]] || fail "--mobile-sha requiere valor."
        EXPECTED_MOBILE_SHA="$1"
        ;;
      -h|--help) usage; exit 0 ;;
      *) fail "Opcion no reconocida: $1" ;;
    esac
    shift
  done
}

main() {
  local backend_head mobile_head restart_sum

  parse_args "$@"
  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  [[ "$EXPECTED_BACKEND_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "SHA backend invalido."
  [[ "$EXPECTED_MOBILE_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "SHA mobile invalido."

  backend_head="$(git -c safe.directory="$APP_ROOT" -C "$APP_ROOT" rev-parse HEAD)"
  mobile_head="$(git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" rev-parse HEAD)"
  [[ "$backend_head" == "$EXPECTED_BACKEND_SHA" ]] || fail "Backend en commit inesperado."
  [[ "$mobile_head" == "$EXPECTED_MOBILE_SHA" ]] || fail "Mobile en commit inesperado."
  [[ "$(git -c safe.directory="$APP_ROOT" -C "$APP_ROOT" branch --show-current)" == main ]] \
    || fail "Backend no esta en main."
  [[ "$(git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" branch --show-current)" == main ]] \
    || fail "Mobile no esta en main."
  git -c safe.directory="$APP_ROOT" -C "$APP_ROOT" diff-index --quiet HEAD -- \
    || fail "Backend tiene cambios tracked."
  git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" diff-index --quiet HEAD -- \
    || fail "Mobile tiene cambios tracked."

  bash "$SCRIPT_DIR/healthcheck_prod.sh"
  restart_sum="$(docker inspect --format '{{.RestartCount}}' $(docker ps -q) | awk '{sum += $1} END {print sum + 0}')"
  (( restart_sum == 0 )) || fail "Hay contenedores con RestartCount mayor a cero."

  docker exec sisoc-django-1 python manage.py showmigrations centrodeinfancia \
    | grep -Eq '^ \[X\] 0036_asistenciatrabajador$' \
    || fail "La migracion 0036 no figura aplicada."
  docker exec sisoc-django-1 python manage.py shell -c \
    "from centrodeinfancia.models import AsistenciaTrabajador; AsistenciaTrabajador.objects.exists(); print('attendance_table=ok')" \
    | grep -q '^attendance_table=ok$' \
    || fail "No se pudo consultar la tabla de asistencia."

  systemctl is-active --quiet mysql && fail "MySQL local sigue activo."
  systemctl is-enabled --quiet mysql && fail "MySQL local sigue habilitado."
  systemctl is-enabled --quiet apache2 && fail "apache2 sigue habilitado."
  systemctl is-enabled --quiet sisoc.service && fail "sisoc.service sigue habilitado."
  [[ "$(stat -c '%U:%G:%a' "$MOBILE_ROOT/.env")" == "root:$TARGET_GROUP:640" ]] \
    || fail "Metadata de .env mobile inesperada."
  [[ "$(crontab -u "$TARGET_USER" -l | grep -Fxc "$DEPLOY_CRON_LINE" || true)" -eq 1 ]] \
    || fail "Cron de limpieza productiva ausente o duplicado."
  [[ "$(crontab -l | grep -Fc -- '--volumes' || true)" -eq 0 ]] \
    || fail "Root cron conserva una poda con --volumes."
  [[ -f /etc/logrotate.d/sisoc-nginx ]] || fail "Falta logrotate SISOC NGINX."
  logrotate -d /etc/logrotate.d/sisoc-nginx >/dev/null

  printf 'PROD RELEASE VERIFICATION: OK\n'
  printf 'backend_head=%s\nmobile_head=%s\ncontainers=7\n' \
    "$backend_head" "$mobile_head"
}

main "$@"

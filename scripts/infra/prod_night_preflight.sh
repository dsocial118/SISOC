#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HOSTNAME="${PROD_EXPECTED_HOSTNAME:-mdsldmz-ssies}"
APP_ROOT="${APP_ROOT:-/sisoc/SISOC}"
MOBILE_ROOT="${MOBILE_ROOT:-/sisoc/SISOC-Mobile}"
TARGET_USER="${PROD_MAINTENANCE_USER:-sisoc-deploy}"
MEDIA_STATUS="${PROD_MEDIA_BACKUP_STATUS:-/sisoc/backups/media/20260713_172352/status.txt}"
MIN_FREE_BYTES="${PROD_MIN_FREE_BYTES:-107374182400}"
SKIP_MYSQL=0

usage() {
  cat <<'USAGE'
Uso:
  prod_night_preflight.sh [--skip-mysql]

Preflight read-only de la ventana productiva. --skip-mysql se usa solamente
despues de completar Stage 1, cuando el MySQL local ya debe estar inactivo.
No imprime .env, secretos ni contenido de logs.
USAGE
}

fail() {
  printf '[%s] ERROR: %s\n' "$SCRIPT_NAME" "$*" >&2
  exit 1
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --skip-mysql) SKIP_MYSQL=1 ;;
      -h|--help) usage; exit 0 ;;
      *) fail "Opcion no reconocida: $1" ;;
    esac
    shift
  done
}

assert_git_checkout() {
  local path="$1" expected_branch="$2" label="$3" branch tracked_changes
  git -c safe.directory="$path" -C "$path" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || fail "$label no es un checkout Git."
  branch="$(git -c safe.directory="$path" -C "$path" branch --show-current)"
  [[ "$branch" == "$expected_branch" ]] || fail "$label no esta en $expected_branch."
  if ! git -c safe.directory="$path" -C "$path" diff-index --quiet HEAD --; then
    tracked_changes="$(git -c safe.directory="$path" -C "$path" diff-index --name-only HEAD -- | wc -l)"
    fail "$label tiene $tracked_changes archivos tracked modificados."
  fi
}

main() {
  local available_bytes used_percent backend_head mobile_head restart_sum

  parse_args "$@"
  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  [[ -r "$MEDIA_STATUS" ]] || fail "No se puede leer el estado del backup de media."
  grep -q '^BACKUP_STATUS=complete$' "$MEDIA_STATUS" \
    || fail "El backup de media no figura completo."

  available_bytes="$(df -B1 --output=avail / | tail -n 1 | tr -d ' ')"
  used_percent="$(df -P / | awk 'NR == 2 {gsub(/%/, "", $5); print $5}')"
  (( available_bytes >= MIN_FREE_BYTES )) || fail "Hay menos de 100 GiB libres."
  (( used_percent < 80 )) || fail "El filesystem raiz alcanzo 80% o mas."

  assert_git_checkout "$APP_ROOT" main "SISOC"
  assert_git_checkout "$MOBILE_ROOT" main "SISOC-Mobile"
  backend_head="$(git -c safe.directory="$APP_ROOT" -C "$APP_ROOT" rev-parse HEAD)"
  mobile_head="$(git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" rev-parse HEAD)"

  runuser -u "$TARGET_USER" -- docker compose \
    -f "$APP_ROOT/docker-compose.deploy.yml" \
    -f "$APP_ROOT/docker-compose.produccion.yml" \
    --project-directory "$APP_ROOT" config -q
  runuser -u "$TARGET_USER" -- docker compose \
    -f "$MOBILE_ROOT/compose.prod.yaml" \
    --project-directory "$MOBILE_ROOT" config -q

  bash "$SCRIPT_DIR/healthcheck_prod.sh"
  restart_sum="$(docker inspect --format '{{.RestartCount}}' $(docker ps -q) | awk '{sum += $1} END {print sum + 0}')"
  (( restart_sum == 0 )) || fail "Hay restart counts acumulados; clasificar antes de avanzar."

  bash "$SCRIPT_DIR/prepare_prod_mobile_checkout.sh"
  bash "$SCRIPT_DIR/install_prod_maintenance.sh"
  if [[ "$SKIP_MYSQL" -eq 0 ]]; then
    bash "$SCRIPT_DIR/retire_prod_local_mysql_stage1.sh"
  else
    systemctl is-active --quiet mysql && fail "MySQL local sigue activo."
    systemctl is-enabled --quiet mysql && fail "MySQL local sigue habilitado."
    ss -Hlnpt 'sport = :3306' | grep -q . && fail "3306 local sigue escuchando."
    ss -Hlnpt 'sport = :33060' | grep -q . && fail "33060 local sigue escuchando."
  fi

  printf 'PROD NIGHT PREFLIGHT: OK\n'
  printf 'backend_head=%s\nmobile_head=%s\nroot_usage=%s%%\n' \
    "$backend_head" "$mobile_head" "$used_percent"
  printf 'operator_confirmation_required=DB backup, no active imports/mailings, latest GitHub run\n'
}

main "$@"

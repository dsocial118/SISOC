#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HOSTNAME="${PROD_EXPECTED_HOSTNAME:-mdsldmz-ssies}"
APP_ROOT="${APP_ROOT:-/sisoc/SISOC}"
ENV_FILE="${ENV_FILE:-$APP_ROOT/.env}"
THRESHOLD_PERCENT="${PROD_DISK_THRESHOLD_PERCENT:-80}"
RETENTION="${PROD_DOCKER_IMAGE_RETENTION:-336h}"
APPLY=0
ASSUME_YES=0

usage() {
  cat <<'USAGE'
Uso:
  cleanup_prod_disk.sh [--apply] [--yes]

Sin --apply muestra estado y plan. Con --apply, y solo cuando / alcanza el
umbral, poda imagenes y build cache Docker no usados mas antiguos que 14 dias.
Nunca toca volumenes, media, logs, contenedores, MySQL ni checkouts.
USAGE
}

log() {
  local message="$*"
  printf '[%s] %s\n' "$SCRIPT_NAME" "$message"
  if [[ "$APPLY" -eq 1 ]]; then
    /usr/bin/logger -t sisoc-prod-disk-cleanup -- "$message" 2>/dev/null || true
  fi
}

fail() {
  log "ERROR: $*" >&2
  exit 1
}

read_env_value() {
  local key="$1" line value
  line="$(grep -E "^[[:space:]]*(export[[:space:]]+)?${key}[[:space:]]*=" "$ENV_FILE" | tail -n 1 || true)"
  [[ -n "$line" ]] || return 1
  value="${line#*=}"
  value="${value%%#*}"
  value="${value//$'\r'/}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf '%s' "$value"
}

used_percent() {
  df -P / | awk 'NR == 2 {gsub(/%/, "", $5); print $5}'
}

active_container_images() {
  local container_id
  while IFS= read -r container_id; do
    [[ -n "$container_id" ]] || continue
    docker inspect --format '{{.Name}}|{{.Image}}' "$container_id"
  done < <(docker ps -q | sort)
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --apply) APPLY=1 ;;
      --yes) ASSUME_YES=1 ;;
      -h|--help) usage; exit 0 ;;
      *) fail "Opcion no reconocida: $1" ;;
    esac
    shift
  done
}

main() {
  local environment before_usage after_usage before_runtime after_runtime

  parse_args "$@"
  [[ "$THRESHOLD_PERCENT" =~ ^[0-9]+$ ]] || fail "El umbral debe ser entero."
  (( THRESHOLD_PERCENT >= 1 && THRESHOLD_PERCENT <= 100 )) \
    || fail "El umbral debe estar entre 1 y 100."
  [[ "$RETENTION" =~ ^[1-9][0-9]*h$ ]] \
    || fail "La retencion debe expresarse en horas positivas."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  [[ -r "$ENV_FILE" ]] || fail "No se puede leer $ENV_FILE"
  [[ -x "$SCRIPT_DIR/healthcheck_prod.sh" ]] || fail "Falta healthcheck_prod.sh."

  environment="$(read_env_value ENVIRONMENT || true)"
  environment="$(printf '%s' "$environment" | tr '[:upper:]' '[:lower:]')"
  case "$environment" in
    prd|prod|production|produccion) ;;
    *) fail "ENVIRONMENT no corresponde a produccion." ;;
  esac

  docker info >/dev/null || fail "El usuario no puede consultar Docker."
  bash "$SCRIPT_DIR/healthcheck_prod.sh"
  before_usage="$(used_percent)"
  log "host=$(hostname -s) root_usage=${before_usage}% threshold=${THRESHOLD_PERCENT}% retention=$RETENTION"
  docker system df

  if [[ "$APPLY" -eq 0 ]]; then
    log "Modo informativo. Plan: image prune y builder prune; sin volumenes."
    exit 0
  fi

  exec 9>/tmp/sisoc-prod-disk-cleanup.lock
  flock -n 9 || fail "Ya hay otra limpieza en ejecucion."

  if (( before_usage < THRESHOLD_PERCENT )); then
    log "No se limpia: el uso esta por debajo del umbral."
    exit 0
  fi

  if [[ "$ASSUME_YES" -eq 0 ]]; then
    read -r -p "Podar recursos Docker no usados con mas de $RETENTION? [y/N] " answer
    case "$answer" in
      y|Y|yes|YES|si|SI) ;;
      *) fail "Operacion cancelada." ;;
    esac
  fi

  before_runtime="$(active_container_images | sort)"
  docker image prune -af --filter "until=$RETENTION"
  docker builder prune -af --filter "until=$RETENTION"
  after_runtime="$(active_container_images | sort)"
  [[ "$after_runtime" == "$before_runtime" ]] \
    || fail "Cambio inesperado en contenedores o imagenes activas."
  bash "$SCRIPT_DIR/healthcheck_prod.sh"

  after_usage="$(used_percent)"
  log "Poda finalizada: before=${before_usage}% after=${after_usage}% health=ok"
  df -h /
  docker system df
}

main "$@"

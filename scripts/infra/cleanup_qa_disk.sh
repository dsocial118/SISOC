#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
EXPECTED_HOSTNAME="${QA_EXPECTED_HOSTNAME:-mdsldmz-ssies-test}"
APP_ROOT="${APP_ROOT:-/home/admin-ssies/sisoc-comedores-test/BACKOFFICE}"
ENV_FILE="${ENV_FILE:-$APP_ROOT/.env}"
THRESHOLD_PERCENT="${QA_DISK_THRESHOLD_PERCENT:-80}"
RETENTION="${QA_DOCKER_IMAGE_RETENTION:-336h}"
APPLY=0
ASSUME_YES=0

usage() {
  cat <<'USAGE'
Uso:
  cleanup_qa_disk.sh [--apply] [--yes]

Sin --apply muestra el estado y la accion prevista. Con --apply poda imagenes
y build cache Docker no usados mas antiguos que la retencion configurada.

Variables opcionales:
  QA_DISK_THRESHOLD_PERCENT  Umbral de uso de / (default: 80).
  QA_DOCKER_IMAGE_RETENTION  Retencion en horas (default: 336h / 14 dias).
USAGE
}

log() {
  local message="$*"
  printf '[%s] %s\n' "$SCRIPT_NAME" "$message"
  /usr/bin/logger -t sisoc-qa-disk-cleanup -- "$message" 2>/dev/null || true
}

fail() {
  log "ERROR: $*"
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

healthcheck() {
  local attempt
  for attempt in 1 2 3; do
    if curl --max-time 8 -fsS -o /dev/null http://127.0.0.1/health/; then
      return 0
    fi
    sleep 2
  done
  return 1
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
  local hostname environment before_usage after_usage before_containers after_containers

  parse_args "$@"
  [[ "$THRESHOLD_PERCENT" =~ ^[0-9]+$ ]] || fail "El umbral debe ser un entero."
  (( THRESHOLD_PERCENT >= 1 && THRESHOLD_PERCENT <= 100 )) || fail "El umbral debe estar entre 1 y 100."
  [[ "$RETENTION" =~ ^[1-9][0-9]*h$ ]] || fail "La retencion debe expresarse como horas positivas, por ejemplo 336h."
  [[ -r "$ENV_FILE" ]] || fail "No se puede leer $ENV_FILE"

  hostname="$(hostname -s)"
  [[ "$hostname" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado: $hostname"
  environment="$(read_env_value ENVIRONMENT || true)"
  environment="$(printf '%s' "$environment" | tr '[:upper:]' '[:lower:]')"
  [[ "$environment" == "qa" ]] || fail "ENVIRONMENT no es qa."

  command -v docker >/dev/null || fail "Docker no esta disponible."
  docker info >/dev/null || fail "El usuario no puede consultar Docker."

  before_usage="$(used_percent)"
  log "host=$hostname environment=qa root_usage=${before_usage}% threshold=${THRESHOLD_PERCENT}% retention=$RETENTION"
  docker system df
  docker ps --format 'container={{.Names}} status={{.Status}} image={{.Image}}'

  if [[ "$APPLY" -eq 0 ]]; then
    log "Modo informativo. Acciones previstas: docker image prune y docker builder prune, ambas con until=$RETENTION"
    exit 0
  fi

  exec 9>/tmp/sisoc-qa-disk-cleanup.lock
  flock -n 9 || fail "Ya hay otra limpieza en ejecucion."

  if (( before_usage < THRESHOLD_PERCENT )); then
    log "No se limpia: el uso esta por debajo del umbral."
    exit 0
  fi

  if [[ "$ASSUME_YES" -eq 0 ]]; then
    read -r -p "Podar imagenes Docker no usadas con mas de $RETENTION? [y/N] " answer
    case "$answer" in
      y|Y|yes|YES|si|SI) ;;
      *) fail "Operacion cancelada." ;;
    esac
  fi

  before_containers="$(docker ps --format '{{.Names}}|{{.Image}}' | sort)"
  log "Inicio de poda conservadora; no se tocaran volumenes ni contenedores."
  docker image prune -af --filter "until=$RETENTION"
  docker builder prune -af --filter "until=$RETENTION"
  after_containers="$(docker ps --format '{{.Names}}|{{.Image}}' | sort)"
  [[ "$after_containers" == "$before_containers" ]] || fail "Cambio inesperado en los contenedores activos."
  healthcheck || fail "El health check fallo despues de la poda."

  after_usage="$(used_percent)"
  log "Poda finalizada: root_usage_before=${before_usage}% root_usage_after=${after_usage}% health=ok"
  df -h /
  docker system df
}

main "$@"

#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
EXPECTED_HOSTNAME="${HML_EXPECTED_HOSTNAME:-ldmzssies-homolo}"
APP_ROOT="${APP_ROOT:-/sisoc/SISOC}"
ENV_FILE="${ENV_FILE:-$APP_ROOT/.env}"
DOMAIN="${HML_DOMAIN:-hml-sisoc.secretarianaf.gob.ar}"
THRESHOLD_PERCENT="${HML_DISK_THRESHOLD_PERCENT:-80}"
RETENTION="${HML_DOCKER_IMAGE_RETENTION:-336h}"
APPLY=0
ASSUME_YES=0

usage() {
  cat <<'USAGE'
Uso:
  cleanup_hml_disk.sh [--apply] [--yes]

Sin --apply muestra estado y plan. Con --apply poda solo imagenes y build cache
Docker no usados mas antiguos que la retencion. Nunca toca volumenes, media,
contenedores, logs ni MySQL.

Variables opcionales:
  HML_DISK_THRESHOLD_PERCENT  Umbral de uso de / (default: 80).
  HML_DOCKER_IMAGE_RETENTION  Retencion en horas (default: 336h / 14 dias).
USAGE
}

log() {
  local message="$*"
  printf '[%s] %s\n' "$SCRIPT_NAME" "$message"
  if [[ "$APPLY" -eq 1 ]]; then
    /usr/bin/logger -t sisoc-hml-disk-cleanup -- "$message" 2>/dev/null || true
  fi
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

active_container_images() {
  local container_id
  while IFS= read -r container_id; do
    [[ -n "$container_id" ]] || continue
    docker inspect --format '{{.Name}}|{{.Image}}' "$container_id"
  done < <(docker ps -q | sort)
}

functional_healthcheck() {
  docker ps --format '{{.Names}}|{{.Status}}' | grep -q '^sisoc-django-1|Up '
  docker ps --format '{{.Names}}|{{.Status}}' | grep -q '^sisoc-ocr_worker-1|Up '
  docker ps --format '{{.Names}}|{{.Status}}' | grep -q '^sisoc-mobile-frontend-1|Up '
  curl --max-time 8 -kfsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
    "https://$DOMAIN/health/"
  curl --max-time 8 -kfsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
    "https://$DOMAIN/mobile/"
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
  local hostname environment before_usage after_usage before_runtime after_runtime

  parse_args "$@"
  [[ "$THRESHOLD_PERCENT" =~ ^[0-9]+$ ]] || fail "El umbral debe ser entero."
  (( THRESHOLD_PERCENT >= 1 && THRESHOLD_PERCENT <= 100 )) \
    || fail "El umbral debe estar entre 1 y 100."
  [[ "$RETENTION" =~ ^[1-9][0-9]*h$ ]] \
    || fail "La retencion debe ser horas positivas, por ejemplo 336h."
  [[ -r "$ENV_FILE" ]] || fail "No se puede leer $ENV_FILE"

  hostname="$(hostname -s)"
  [[ "$hostname" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado: $hostname"
  environment="$(read_env_value ENVIRONMENT || true)"
  environment="$(printf '%s' "$environment" | tr '[:upper:]' '[:lower:]')"
  [[ "$environment" == "homologacion" ]] || fail "ENVIRONMENT no es homologacion."

  command -v docker >/dev/null || fail "Docker no esta disponible."
  docker info >/dev/null || fail "El usuario no puede consultar Docker."
  functional_healthcheck || fail "El health funcional previo fallo."

  before_usage="$(used_percent)"
  log "host=$hostname environment=homologacion root_usage=${before_usage}% threshold=${THRESHOLD_PERCENT}% retention=$RETENTION"
  docker system df
  docker ps --format 'container={{.Names}} status={{.Status}} image={{.Image}}'

  if [[ "$APPLY" -eq 0 ]]; then
    log "Modo informativo. Plan: image prune y builder prune con until=$RETENTION; sin volumenes."
    exit 0
  fi

  exec 9>/tmp/sisoc-hml-disk-cleanup.lock
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

  before_runtime="$(active_container_images | sort)"
  log "Inicio de poda conservadora; no se tocaran volumenes ni contenedores."
  docker image prune -af --filter "until=$RETENTION"
  docker builder prune -af --filter "until=$RETENTION"
  after_runtime="$(active_container_images | sort)"
  [[ "$after_runtime" == "$before_runtime" ]] \
    || fail "Cambio inesperado en contenedores o imagenes activas."
  functional_healthcheck || fail "El health funcional fallo despues de la poda."

  after_usage="$(used_percent)"
  log "Poda finalizada: root_usage_before=${before_usage}% root_usage_after=${after_usage}% health=ok"
  df -h /
  docker system df
}

main "$@"

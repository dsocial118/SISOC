#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
DRY_RUN=0
ASSUME_YES=0
INCLUDE_VOLUMES=0
ALLOW_DIRTY=0
ALLOW_BRANCH_MISMATCH=0
SKIP_PULL=0
WITH_MOBILE=0
MOBILE_DIR=""
MOBILE_SCRIPT=""
MOBILE_HTTPS_REMOTE="https://github.com/dsocial118/SISOC-Mobile.git"

usage() {
  cat <<'USAGE'
Uso:
  bash scripts/operacion/deploy_refresh.sh [opciones]

Objetivo:
  Baja Docker Compose, actualiza la branch actual con git pull --ff-only
  y vuelve a levantar el stack segun ENVIRONMENT en .env.

Opciones:
  --dry-run                 Muestra los comandos sin ejecutarlos.
  --yes                     No pide confirmacion interactiva.
  --volumes                 Agrega --volumes al docker compose down.
                            Cuidado: en dev puede borrar la DB local.
  --allow-dirty             Permite pull con cambios tracked locales.
  --allow-branch-mismatch   No bloquea si la branch actual no coincide
                            con la esperada para ENVIRONMENT.
  --skip-pull               No ejecuta git fetch/pull; solo reinicia Docker.
  --with-mobile             Tambien despliega SISOC-Mobile.
  --mobile-dir PATH         Ruta del checkout SISOC-Mobile.
                            Default: ../SISOC-Mobile desde la raiz de SISOC.
                            Ejecuta scripts/operacion/deploy_refresh.sh de ese repo.
                            SISOC-Mobile debe estar en branch main.
                            Su origin conocido se normaliza a HTTPS publica.
  -h, --help                Muestra esta ayuda.

Mapeo por entorno:
  ENVIRONMENT=dev|local|development -> docker-compose.yml
  ENVIRONMENT=qa                    -> docker-compose.deploy.yml
  ENVIRONMENT=homologacion|hml|staging
                                  -> docker-compose.deploy.yml + docker-compose.produccion.yml
                                     + SISOC-Mobile
  ENVIRONMENT=prd|prod|production   -> docker-compose.deploy.yml + docker-compose.produccion.yml
USAGE
}

log() {
  printf '[%s] %s\n' "$SCRIPT_NAME" "$*"
}

fail() {
  printf '[%s] ERROR: %s\n' "$SCRIPT_NAME" "$*" >&2
  exit 1
}

run() {
  printf '+'
  printf ' %q' "$@"
  printf '\n'

  if [[ "$DRY_RUN" -eq 1 ]]; then
    return 0
  fi

  "$@"
}

read_env_value() {
  local key="$1"
  local line value

  line="$(
    grep -E "^[[:space:]]*(export[[:space:]]+)?${key}[[:space:]]*=" "$ENV_FILE" \
      | tail -n 1 \
      || true
  )"

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

require_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "No existe $path"
}

confirm() {
  local prompt="$1"

  if [[ "$ASSUME_YES" -eq 1 || "$DRY_RUN" -eq 1 ]]; then
    return 0
  fi

  read -r -p "$prompt [y/N] " answer
  case "$answer" in
    y|Y|yes|YES|si|SI) return 0 ;;
    *) fail "Operacion cancelada por el usuario." ;;
  esac
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run) DRY_RUN=1 ;;
      --yes) ASSUME_YES=1 ;;
      --volumes) INCLUDE_VOLUMES=1 ;;
      --allow-dirty) ALLOW_DIRTY=1 ;;
      --allow-branch-mismatch) ALLOW_BRANCH_MISMATCH=1 ;;
      --skip-pull) SKIP_PULL=1 ;;
      --with-mobile) WITH_MOBILE=1 ;;
      --mobile-dir)
        shift
        [[ $# -gt 0 ]] || fail "--mobile-dir requiere una ruta."
        MOBILE_DIR="$1"
        WITH_MOBILE=1
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        fail "Opcion no reconocida: $1"
        ;;
    esac
    shift
  done
}

ensure_clean_branch() {
  local repo_dir="$1"
  local expected_branch="${2:-}"
  local branch_var_name="$3"
  local label="$4"
  local branch

  git -C "$repo_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || fail "$label no parece ser un repositorio git: $repo_dir"

  branch="$(git -C "$repo_dir" branch --show-current)"
  [[ -n "$branch" ]] || fail "$label esta en detached HEAD; no puedo hacer pull seguro."

  if [[ -n "$expected_branch" && "$ALLOW_BRANCH_MISMATCH" -eq 0 && "$branch" != "$expected_branch" ]]; then
    fail "$label espera branch '$expected_branch', pero la branch actual es '$branch'. Usa --allow-branch-mismatch si esto es intencional."
  fi

  if [[ "$ALLOW_DIRTY" -eq 0 ]]; then
    if ! git -C "$repo_dir" diff --quiet -- \
      || ! git -C "$repo_dir" diff --cached --quiet --; then
      fail "$label tiene cambios tracked locales. Commit/stash o usa --allow-dirty."
    fi
  fi

  printf -v "$branch_var_name" '%s' "$branch"
}

normalize_mobile_origin() {
  local current_remote

  [[ "$WITH_MOBILE" -eq 1 && "$SKIP_PULL" -eq 0 ]] || return 0

  current_remote="$(git -C "$MOBILE_DIR" remote get-url origin 2>/dev/null)" \
    || fail "SISOC-Mobile no tiene remote origin configurado."

  case "$current_remote" in
    "$MOBILE_HTTPS_REMOTE")
      return 0
      ;;
    https://github.com/dsocial118/SISOC-Mobile|git@github.com:dsocial118/SISOC-Mobile.git|ssh://git@github.com/dsocial118/SISOC-Mobile.git)
      log "Normalizando origin de SISOC-Mobile a HTTPS publica."
      run git -C "$MOBILE_DIR" remote set-url origin "$MOBILE_HTTPS_REMOTE"
      ;;
    *)
      fail "Origin inesperado para SISOC-Mobile; revisar origin sin copiar credenciales al log."
      ;;
  esac
}

compose_for_environment() {
  local environment="$1"

  COMPOSE_FILES=()
  EXPECTED_BRANCH=""

  case "$environment" in
    dev|local|development)
      COMPOSE_FILES=("docker-compose.yml")
      EXPECTED_BRANCH="${DEV_BRANCH:-development}"
      ;;
    qa)
      COMPOSE_FILES=("docker-compose.deploy.yml")
      EXPECTED_BRANCH="${QA_BRANCH:-development}"
      ;;
    homologacion|hml|staging)
      COMPOSE_FILES=("docker-compose.deploy.yml" "docker-compose.produccion.yml")
      EXPECTED_BRANCH="${HOMOLOGACION_BRANCH:-homologacion}"
      WITH_MOBILE=1
      ;;
    prd|prod|production|produccion)
      COMPOSE_FILES=("docker-compose.deploy.yml" "docker-compose.produccion.yml")
      EXPECTED_BRANCH="${PROD_BRANCH:-main}"
      ;;
    *)
      fail "ENVIRONMENT='$environment' no esta soportado."
      ;;
  esac

  COMPOSE_CMD=(docker compose)
  for file in "${COMPOSE_FILES[@]}"; do
    require_file "$ROOT_DIR/$file"
    COMPOSE_CMD+=(-f "$ROOT_DIR/$file")
  done
}

configure_mobile() {
  [[ "$WITH_MOBILE" -eq 1 ]] || return 0

  if [[ -z "$MOBILE_DIR" ]]; then
    MOBILE_DIR="$ROOT_DIR/../SISOC-Mobile"
  fi

  MOBILE_DIR="$(cd "$MOBILE_DIR" 2>/dev/null && pwd)" \
    || fail "No existe el directorio SISOC-Mobile esperado: $MOBILE_DIR"

  MOBILE_SCRIPT="$MOBILE_DIR/scripts/operacion/deploy_refresh.sh"
  require_file "$MOBILE_SCRIPT"

  MOBILE_ARGS=()
  [[ "$DRY_RUN" -eq 1 ]] && MOBILE_ARGS+=(--dry-run)
  [[ "$ASSUME_YES" -eq 1 ]] && MOBILE_ARGS+=(--yes)
  [[ "$INCLUDE_VOLUMES" -eq 1 ]] && MOBILE_ARGS+=(--volumes)
  [[ "$ALLOW_DIRTY" -eq 1 ]] && MOBILE_ARGS+=(--allow-dirty)
  [[ "$ALLOW_BRANCH_MISMATCH" -eq 1 ]] && MOBILE_ARGS+=(--allow-branch-mismatch)
  [[ "$SKIP_PULL" -eq 1 ]] && MOBILE_ARGS+=(--skip-pull)

  ensure_clean_branch "$MOBILE_DIR" "${MOBILE_BRANCH:-main}" MOBILE_BRANCH "SISOC-Mobile"
  normalize_mobile_origin
}

main() {
  parse_args "$@"

  require_file "$ENV_FILE"

  ENVIRONMENT="$(read_env_value ENVIRONMENT || true)"
  [[ -n "${ENVIRONMENT:-}" ]] || fail "No pude leer ENVIRONMENT desde $ENV_FILE"
  ENVIRONMENT="$(printf '%s' "$ENVIRONMENT" | tr '[:upper:]' '[:lower:]')"

  compose_for_environment "$ENVIRONMENT"
  ensure_clean_branch "$ROOT_DIR" "$EXPECTED_BRANCH" CURRENT_BRANCH "SISOC"
  configure_mobile

  log "root=$ROOT_DIR"
  log "environment=$ENVIRONMENT"
  log "branch=$CURRENT_BRANCH"
  log "compose_files=${COMPOSE_FILES[*]}"
  if [[ "$WITH_MOBILE" -eq 1 ]]; then
    log "mobile_root=$MOBILE_DIR"
    log "mobile_branch=$MOBILE_BRANCH"
    log "mobile_script=$MOBILE_SCRIPT"
  fi

  if [[ "$INCLUDE_VOLUMES" -eq 1 ]]; then
    confirm "Vas a ejecutar docker compose down --volumes. Esto puede borrar datos persistentes de los stacks. Continuar?"
    DOWN_ARGS=(down --remove-orphans --volumes)
  else
    DOWN_ARGS=(down --remove-orphans)
  fi

  if [[ "$SKIP_PULL" -eq 0 ]]; then
    run git -C "$ROOT_DIR" fetch origin --prune
  fi

  run "${COMPOSE_CMD[@]}" --project-directory "$ROOT_DIR" config -q

  run "${COMPOSE_CMD[@]}" --project-directory "$ROOT_DIR" "${DOWN_ARGS[@]}"

  if [[ "$SKIP_PULL" -eq 0 ]]; then
    run git -C "$ROOT_DIR" pull --ff-only origin "$CURRENT_BRANCH"
  fi

  run "${COMPOSE_CMD[@]}" --project-directory "$ROOT_DIR" up -d --build

  run "${COMPOSE_CMD[@]}" --project-directory "$ROOT_DIR" ps

  if [[ "$WITH_MOBILE" -eq 1 ]]; then
    run bash "$MOBILE_SCRIPT" "${MOBILE_ARGS[@]}"
  fi

  log "Deploy refresh finalizado."
}

main "$@"

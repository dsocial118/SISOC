#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="${SISOC_ROOT_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)}"
EXPECTED_REVISION=""
DEPLOY_ENVIRONMENT=""
ROLLBACK_REVISION=""
SKIP_PULL=0

fail() {
  printf '[deploy-verified] ERROR: %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --environment)
      DEPLOY_ENVIRONMENT="${2:-}"
      shift 2
      ;;
    --expected-revision)
      EXPECTED_REVISION="${2:-}"
      shift 2
      ;;
    --rollback-revision)
      ROLLBACK_REVISION="${2:-}"
      shift 2
      ;;
    --skip-pull)
      SKIP_PULL=1
      shift
      ;;
    *)
      fail "Argumento desconocido: $1"
      ;;
  esac
done

[[ "$EXPECTED_REVISION" =~ ^[0-9a-f]{40}$ ]] \
  || fail "--expected-revision debe ser un SHA completo."
if [[ -n "$ROLLBACK_REVISION" && ! "$ROLLBACK_REVISION" =~ ^[0-9a-f]{40}$ ]]; then
  fail "--rollback-revision debe ser un SHA completo."
fi

case "$DEPLOY_ENVIRONMENT" in
  qa)
    EXPECTED_BRANCH=development
    COMPOSE_FILES=(-f "$ROOT_DIR/docker-compose.deploy.yml")
    HEALTH_SCRIPT="$ROOT_DIR/scripts/infra/healthcheck_qa.sh"
    ;;
  homologacion)
    EXPECTED_BRANCH=homologacion
    COMPOSE_FILES=(-f "$ROOT_DIR/docker-compose.deploy.yml" -f "$ROOT_DIR/docker-compose.produccion.yml")
    HEALTH_SCRIPT="$ROOT_DIR/scripts/infra/healthcheck_hml.sh"
    ;;
  production)
    EXPECTED_BRANCH=main
    COMPOSE_FILES=(-f "$ROOT_DIR/docker-compose.deploy.yml" -f "$ROOT_DIR/docker-compose.produccion.yml")
    HEALTH_SCRIPT="$ROOT_DIR/scripts/infra/healthcheck_prod.sh"
    ;;
  *)
    fail "--environment debe ser qa, homologacion o production."
    ;;
esac

COMPOSE=(docker compose "${COMPOSE_FILES[@]}" --project-directory "$ROOT_DIR")
[[ -d "$ROOT_DIR/.git" ]] || fail "SISOC_ROOT_DIR no apunta a un checkout Git."
[[ "$(git -C "$ROOT_DIR" branch --show-current)" == "$EXPECTED_BRANCH" ]] \
  || fail "El checkout no esta en $EXPECTED_BRANCH."
git -C "$ROOT_DIR" diff --quiet || fail "El checkout tiene cambios tracked."
git -C "$ROOT_DIR" diff --cached --quiet || fail "El checkout tiene cambios staged."

git -C "$ROOT_DIR" fetch origin --no-tags "$EXPECTED_BRANCH:refs/remotes/origin/$EXPECTED_BRANCH"
remote_revision="$(git -C "$ROOT_DIR" rev-parse "origin/$EXPECTED_BRANCH")"
[[ "$remote_revision" == "$EXPECTED_REVISION" ]] \
  || fail "La branch avanzo a $remote_revision; no se despliega $EXPECTED_REVISION."

previous_revision="${ROLLBACK_REVISION:-$(git -C "$ROOT_DIR" rev-parse HEAD)}"
deployment_started=0

wait_for() {
  local description="$1"
  local attempts="$2"
  local output attempt
  shift 2
  output="$(mktemp)"
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    if "$@" >"$output" 2>&1; then
      cat "$output"
      rm -f "$output"
      return 0
    fi
    if ((attempt < attempts)); then
      echo "[deploy-verified] Esperando $description ($attempt/$attempts)..."
      sleep 2
    fi
  done
  cat "$output"
  rm -f "$output"
  return 1
}

show_diagnostics() {
  echo "::group::Diagnostico de $DEPLOY_ENVIRONMENT"
  "${COMPOSE[@]}" ps || true
  "${COMPOSE[@]}" logs --tail 200 django || true
  echo "::endgroup::"
}

verify_stack() {
  if ! wait_for "migraciones de $DEPLOY_ENVIRONMENT" 30 \
    "${COMPOSE[@]}" exec -T django python manage.py migrate --check; then
    return 1
  fi
  wait_for "healthcheck de $DEPLOY_ENVIRONMENT" 30 bash "$HEALTH_SCRIPT"
}

rollback_on_exit() {
  local failed_status=$?
  trap - EXIT
  if [[ "$failed_status" -eq 0 || "$deployment_started" -eq 0 ]]; then
    exit "$failed_status"
  fi

  show_diagnostics
  echo "::warning::El deploy fallo; restaurando automaticamente $previous_revision."
  if ! git -C "$ROOT_DIR" reset --hard "$previous_revision"; then
    echo "::error::No se pudo restaurar el checkout anterior."
    exit "$failed_status"
  fi
  if ! SISOC_ROOT_DIR="$ROOT_DIR" bash "$ROOT_DIR/scripts/operacion/deploy_refresh.sh" \
    --yes --skip-pull --expected-revision "$previous_revision" --without-mobile; then
    echo "::error::No se pudo reconstruir el stack de la revision anterior."
    exit "$failed_status"
  fi
  if ! verify_stack; then
    show_diagnostics
    echo "::error::La revision anterior fue recreada, pero no supero la verificacion."
    exit "$failed_status"
  fi
  echo "::warning::Rollback verificado en $previous_revision. Las migraciones de base de datos no se revierten automaticamente."
  exit "$failed_status"
}
trap rollback_on_exit EXIT

echo "Commit previo al deploy para rollback: $previous_revision"
deployment_started=1
deploy_args=(--yes --expected-revision "$EXPECTED_REVISION" --without-mobile)
[[ "$SKIP_PULL" -eq 0 ]] || deploy_args+=(--skip-pull)
SISOC_ROOT_DIR="$ROOT_DIR" bash "$ROOT_DIR/scripts/operacion/deploy_refresh.sh" "${deploy_args[@]}"
verify_stack
deployed_revision="$(git -C "$ROOT_DIR" rev-parse HEAD)"
[[ "$deployed_revision" == "$EXPECTED_REVISION" ]] \
  || fail "El checkout final no coincide con la revision esperada."
deployment_started=0

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  {
    echo "### Deploy $DEPLOY_ENVIRONMENT verificado"
    echo "- Revision desplegada: \`$deployed_revision\`"
    echo "- Migraciones: \`migrate --check\` OK"
    echo "- Health: \`$(basename "$HEALTH_SCRIPT")\` OK"
    echo "- Rollback automatico: revision previa \`$previous_revision\`"
  } >> "$GITHUB_STEP_SUMMARY"
fi

trap - EXIT

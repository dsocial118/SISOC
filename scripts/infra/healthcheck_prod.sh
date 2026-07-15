#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
EXPECTED_HOSTNAME="${PROD_EXPECTED_HOSTNAME:-mdsldmz-ssies}"
EXPECTED_DB_HOST="${PROD_EXPECTED_DB_HOST:-10.80.5.46}"
EXPECTED_DB_SERVER="${PROD_EXPECTED_DB_SERVER:-ldmzsql-sisoc}"
EXPECTED_DB_NAME="${PROD_EXPECTED_DB_NAME:-sisoc_local}"
DOMAIN="${PROD_DOMAIN:-sisoc.secretarianaf.gob.ar}"
RUNNER_UNIT="${PROD_RUNNER_UNIT:-actions.runner.dsocial118-SISOC.sisoc-produccion.service}"
CONTAINERS=(
  sisoc-django-1
  sisoc-ocr_worker-1
  sisoc-bulk_credentials_worker-1
  sisoc-ciudadanos_import_worker-1
  sisoc-mailing_worker-1
  sisoc-user_import_worker-1
  sisoc-mobile-frontend-1
)

fail() {
  printf '[%s] ERROR: %s\n' "$SCRIPT_NAME" "$*" >&2
  exit 1
}

container_up() {
  docker ps --format '{{.Names}}|{{.Status}}' | grep -q "^$1|Up "
}

main() {
  local container identity configured_host actual_server actual_db

  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  command -v docker >/dev/null || fail "Docker no esta disponible."
  command -v curl >/dev/null || fail "curl no esta disponible."

  systemctl is-active --quiet docker || fail "docker no esta activo."
  systemctl is-active --quiet nginx || fail "nginx no esta activo."
  systemctl is-active --quiet "$RUNNER_UNIT" || fail "El runner de produccion no esta activo."

  for container in "${CONTAINERS[@]}"; do
    container_up "$container" || fail "Contenedor ausente o no activo: $container"
  done

  [[ "$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' sisoc-mobile-frontend-1)" == "healthy" ]] \
    || fail "SISOC-Mobile no esta healthy."

  curl --max-time 8 -kfsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
    "https://$DOMAIN/"
  curl --max-time 8 -kfsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
    "https://$DOMAIN/health/"
  curl --max-time 8 -kfsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
    "https://$DOMAIN/mobile/"

  identity="$(
    docker exec sisoc-django-1 python manage.py shell -c \
      "from django.db import connection; connection.ensure_connection(); c=connection.cursor(); c.execute('SELECT @@hostname, DATABASE()'); row=c.fetchone(); c.close(); print(str(connection.settings_dict.get('HOST'))+'|'+str(row[0])+'|'+str(row[1]))" \
      | tail -n 1
  )"
  IFS='|' read -r configured_host actual_server actual_db <<< "$identity"
  [[ "$configured_host" == "$EXPECTED_DB_HOST" ]] || fail "Django configura una DB inesperada."
  [[ "$actual_server" == "$EXPECTED_DB_SERVER" ]] || fail "Servidor DB inesperado."
  [[ "$actual_db" == "$EXPECTED_DB_NAME" ]] || fail "Schema DB inesperado."

  printf 'PROD functional health check: OK\n'
  printf 'db_host=%s db_server=%s db_name=%s containers=%s\n' \
    "$configured_host" "$actual_server" "$actual_db" "${#CONTAINERS[@]}"
}

main "$@"

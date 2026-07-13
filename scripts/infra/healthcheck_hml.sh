#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_HOSTNAME="${HML_EXPECTED_HOSTNAME:-ldmzssies-homolo}"
EXPECTED_DB_HOST="${HML_EXPECTED_DB_HOST:-10.80.5.48}"
DOMAIN="${HML_DOMAIN:-hml-sisoc.secretarianaf.gob.ar}"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

container_up() {
  docker ps --format '{{.Names}}|{{.Status}}' | grep -q "^$1|Up "
}

main() {
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."

  container_up sisoc-django-1 || fail "Django no esta activo."
  container_up sisoc-ocr_worker-1 || fail "OCR worker no esta activo."
  container_up sisoc-mobile-frontend-1 || fail "Mobile no esta activo."

  curl --max-time 8 -kfsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
    "https://$DOMAIN/"
  curl --max-time 8 -kfsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
    "https://$DOMAIN/health/"
  curl --max-time 8 -kfsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
    "https://$DOMAIN/mobile/"

  docker exec sisoc-django-1 python manage.py shell -c \
    "from django.db import connection; connection.ensure_connection(); assert str(connection.settings_dict.get('HOST')) == '$EXPECTED_DB_HOST'; c=connection.cursor(); c.execute('SELECT 1'); assert c.fetchone()[0] == 1; c.close()" \
    >/dev/null

  if curl --max-time 8 -fsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
    "https://$DOMAIN/" 2>/dev/null; then
    printf 'tls_valid=yes\n'
  else
    printf 'WARNING: tls_valid=no; certificado HML requiere correccion separada.\n'
  fi

  printf 'HML functional health check: OK\n'
}

main "$@"

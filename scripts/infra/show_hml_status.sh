#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${APP_ROOT:-/sisoc/SISOC}"
MOBILE_ROOT="${MOBILE_ROOT:-/sisoc/SISOC-Mobile}"
EXPECTED_HOSTNAME="${HML_EXPECTED_HOSTNAME:-ldmzssies-homolo}"
DOMAIN="${HML_DOMAIN:-hml-sisoc.secretarianaf.gob.ar}"

[[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || {
  printf 'ERROR: host inesperado\n' >&2
  exit 1
}

printf 'host=%s\n' "$(hostname -s)"
printf 'timestamp=%s\n' "$(date --iso-8601=seconds)"
df -hT /
df -ih /
git -c safe.directory="$APP_ROOT" -C "$APP_ROOT" status --short --branch
git -c safe.directory="$APP_ROOT" -C "$APP_ROOT" rev-parse HEAD
git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" status --short --branch
git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" rev-parse HEAD
docker ps --format 'container={{.Names}} status={{.Status}} image={{.Image}}'
docker system df
systemctl is-active mysql || true
systemctl is-enabled mysql || true
ss -Hlnpt 'sport = :3306' || true
openssl x509 -in /etc/apache2/certs/fullchain.crt -noout -dates 2>/dev/null || true
curl --max-time 8 -kfsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
  -w 'root_http=%{http_code}\n' "https://$DOMAIN/"
curl --max-time 8 -kfsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
  -w 'health_http=%{http_code}\n' "https://$DOMAIN/health/"
curl --max-time 8 -kfsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
  -w 'mobile_http=%{http_code}\n' "https://$DOMAIN/mobile/"
if curl --max-time 8 -fsS -o /dev/null --resolve "$DOMAIN:443:127.0.0.1" \
  "https://$DOMAIN/" 2>/dev/null; then
  printf 'tls_valid=yes\n'
else
  printf 'tls_valid=no\n'
fi

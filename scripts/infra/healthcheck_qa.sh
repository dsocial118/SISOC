#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_HOSTNAME="${QA_EXPECTED_HOSTNAME:-mdsldmz-ssies-test}"

[[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || {
  printf 'ERROR: host inesperado\n' >&2
  exit 1
}

docker ps --format '{{.Names}}|{{.Status}}' | grep -q '^backoffice-django-1|Up '
docker ps --format '{{.Names}}|{{.Status}}' | grep -q '^backoffice-ocr_worker-1|Up '
curl --max-time 8 -fsS -o /dev/null http://127.0.0.1/
curl --max-time 8 -fsS -o /dev/null http://127.0.0.1/health/
printf 'QA health check: OK\n'

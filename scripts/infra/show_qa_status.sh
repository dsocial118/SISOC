#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${APP_ROOT:-/home/admin-ssies/sisoc-comedores-test/BACKOFFICE}"

printf 'host=%s\n' "$(hostname -s)"
printf 'timestamp=%s\n' "$(date --iso-8601=seconds)"
df -hT /
df -ih /
git -C "$APP_ROOT" status --short --branch
git -C "$APP_ROOT" rev-parse HEAD
docker ps --format 'container={{.Names}} status={{.Status}} image={{.Image}}'
docker system df
curl --max-time 8 -fsS -o /dev/null -w 'root_http=%{http_code}\n' http://127.0.0.1/
curl --max-time 8 -fsS -o /dev/null -w 'health_http=%{http_code}\n' http://127.0.0.1/health/

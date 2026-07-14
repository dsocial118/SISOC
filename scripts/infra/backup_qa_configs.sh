#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${APP_ROOT:-/home/admin-ssies/sisoc-comedores-test/BACKOFFICE}"
BACKUP_BASE="${BACKUP_BASE:-/home/sisoc-deploy/backups/infra/qa}"
EXPECTED_HOSTNAME="${QA_EXPECTED_HOSTNAME:-mdsldmz-ssies-test}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$BACKUP_BASE/$TIMESTAMP"

umask 077

log() {
  printf '[backup_qa_configs.sh] %s\n' "$*"
}

fail() {
  log "ERROR: $*" >&2
  exit 1
}

copy_readable() {
  local source="$1" destination="$2"
  if [[ -r "$source" ]]; then
    mkdir -p "$(dirname "$destination")"
    cp -L -- "$source" "$destination"
  else
    printf '%s\n' "$source" >> "$BACKUP_DIR/UNREADABLE_OR_MISSING.txt"
  fi
}

main() {
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  [[ -d "$APP_ROOT/.git" ]] || fail "No se encontro el checkout QA en $APP_ROOT"

  mkdir -p "$BACKUP_DIR"/{nginx,systemd,repo,docker,status,installed-scripts}

  copy_readable /etc/nginx/nginx.conf "$BACKUP_DIR/nginx/nginx.conf"
  copy_readable /etc/nginx/sites-available/staging.conf "$BACKUP_DIR/nginx/staging.conf"
  copy_readable /etc/systemd/system/actions.runner.dsocial118-SISOC.sisoc-qa.service \
    "$BACKUP_DIR/systemd/actions.runner.dsocial118-SISOC.sisoc-qa.service"

  local relative
  for relative in \
    .github/workflows/deploy.yml \
    docker-compose.deploy.yml \
    docker-compose.produccion.yml \
    docker/django/Dockerfile \
    docker/django/entrypoint.py \
    scripts/operacion/deploy_refresh.sh \
    scripts/crontab; do
    copy_readable "$APP_ROOT/$relative" "$BACKUP_DIR/repo/$relative"
  done

  local installed_script
  for installed_script in \
    backup_qa_configs.sh \
    cleanup_qa_disk.sh \
    healthcheck_qa.sh \
    show_qa_status.sh; do
    copy_readable "/home/sisoc-deploy/bin/$installed_script" \
      "$BACKUP_DIR/installed-scripts/$installed_script"
  done

  if [[ -r "$APP_ROOT/.env" ]]; then
    sed -nE 's/^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=.*$/\2=/p' \
      "$APP_ROOT/.env" > "$BACKUP_DIR/repo/env.keys"
  else
    printf '%s\n' "$APP_ROOT/.env" >> "$BACKUP_DIR/UNREADABLE_OR_MISSING.txt"
  fi

  crontab -l > "$BACKUP_DIR/status/crontab.sisoc-deploy.txt" 2>/dev/null || :
  git -C "$APP_ROOT" status --short --branch > "$BACKUP_DIR/status/git-status.txt"
  git -C "$APP_ROOT" rev-parse HEAD > "$BACKUP_DIR/status/git-head.txt"
  df -hT > "$BACKUP_DIR/status/df-hT.txt"
  systemctl is-active docker containerd nginx mysql cron \
    > "$BACKUP_DIR/status/systemd-active.txt" 2>&1 || true
  docker ps --no-trunc > "$BACKUP_DIR/docker/containers.txt"
  docker image ls --digests --no-trunc > "$BACKUP_DIR/docker/images.txt"
  docker system df -v > "$BACKUP_DIR/docker/system-df-v.txt"

  (
    cd "$BACKUP_DIR"
    find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum
  ) > "$BACKUP_DIR/SHA256SUMS"

  find "$BACKUP_DIR" -type d -exec chmod 700 {} +
  find "$BACKUP_DIR" -type f -exec chmod 600 {} +
  log "Backup creado fuera del repo."
  printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
}

main "$@"

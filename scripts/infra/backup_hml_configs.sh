#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${APP_ROOT:-/sisoc/SISOC}"
MOBILE_ROOT="${MOBILE_ROOT:-/sisoc/SISOC-Mobile}"
BACKUP_BASE="${BACKUP_BASE:-$HOME/backups/infra/hml}"
EXPECTED_HOSTNAME="${HML_EXPECTED_HOSTNAME:-ldmzssies-homolo}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$BACKUP_BASE/$TIMESTAMP"

umask 077

log() {
  printf '[backup_hml_configs.sh] %s\n' "$*"
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

export_env_keys() {
  local source="$1" destination="$2"
  if [[ -r "$source" ]]; then
    sed -nE 's/^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=.*$/\2=/p' \
      "$source" > "$destination"
  else
    printf '%s\n' "$source" >> "$BACKUP_DIR/UNREADABLE_OR_MISSING.txt"
  fi
}

main() {
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  [[ -d "$APP_ROOT/.git" ]] || fail "No se encontro el checkout HML."
  [[ -d "$MOBILE_ROOT/.git" ]] || fail "No se encontro el checkout mobile."

  mkdir -p "$BACKUP_DIR"/{nginx,systemd,repo,mobile,docker,status,tls}

  copy_readable /etc/nginx/nginx.conf "$BACKUP_DIR/nginx/nginx.conf"
  copy_readable /etc/nginx/sites-available/sisoc "$BACKUP_DIR/nginx/sisoc"
  copy_readable /etc/systemd/system/actions.runner.dsocial118-SISOC.sisoc-homologacion.service \
    "$BACKUP_DIR/systemd/actions.runner.dsocial118-SISOC.sisoc-homologacion.service"
  copy_readable /etc/systemd/system/sisoc.service \
    "$BACKUP_DIR/systemd/sisoc.service"

  local relative
  for relative in \
    .github/workflows/deploy.yml \
    docker-compose.deploy.yml \
    docker/django/Dockerfile \
    docker/django/entrypoint.py \
    scripts/operacion/deploy_refresh.sh \
    scripts/crontab; do
    copy_readable "$APP_ROOT/$relative" "$BACKUP_DIR/repo/$relative"
  done
  copy_readable "$MOBILE_ROOT/compose.prod.yaml" \
    "$BACKUP_DIR/mobile/compose.prod.yaml"

  export_env_keys "$APP_ROOT/.env" "$BACKUP_DIR/repo/env.keys"
  export_env_keys "$MOBILE_ROOT/.env" "$BACKUP_DIR/mobile/env.keys"

  crontab -l > "$BACKUP_DIR/status/crontab.current-user.txt" 2>/dev/null || :
  git -c safe.directory="$APP_ROOT" -C "$APP_ROOT" status --short --branch \
    > "$BACKUP_DIR/status/git-backend-status.txt"
  git -c safe.directory="$APP_ROOT" -C "$APP_ROOT" rev-parse HEAD \
    > "$BACKUP_DIR/status/git-backend-head.txt"
  git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" status --short --branch \
    > "$BACKUP_DIR/status/git-mobile-status.txt"
  git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" rev-parse HEAD \
    > "$BACKUP_DIR/status/git-mobile-head.txt"
  df -hT > "$BACKUP_DIR/status/df-hT.txt"
  df -ih > "$BACKUP_DIR/status/df-ih.txt"
  systemctl is-active docker containerd nginx mysql cron \
    actions.runner.dsocial118-SISOC.sisoc-homologacion \
    > "$BACKUP_DIR/status/systemd-active.txt" 2>&1 || true

  docker ps --no-trunc > "$BACKUP_DIR/docker/containers.txt"
  docker image ls --digests --no-trunc > "$BACKUP_DIR/docker/images.txt"
  docker system df -v > "$BACKUP_DIR/docker/system-df-v.txt"
  docker builder du > "$BACKUP_DIR/docker/builder-du.txt" 2>&1 || true

  if [[ -r /etc/apache2/certs/fullchain.crt ]]; then
    openssl x509 -in /etc/apache2/certs/fullchain.crt -noout \
      -subject -issuer -dates -fingerprint -sha256 \
      > "$BACKUP_DIR/tls/certificate-metadata.txt"
  else
    printf '%s\n' /etc/apache2/certs/fullchain.crt \
      >> "$BACKUP_DIR/UNREADABLE_OR_MISSING.txt"
  fi
  stat -c 'path=%n owner=%U:%G mode=%a' \
    /etc/apache2/certs/fullchain.crt \
    /etc/apache2/certs/secretarianaf.gob.ar.key \
    > "$BACKUP_DIR/tls/files-metadata.txt" 2>&1 || true

  (
    cd "$BACKUP_DIR"
    find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum
  ) > "$BACKUP_DIR/SHA256SUMS"

  find "$BACKUP_DIR" -type d -exec chmod 700 {} +
  find "$BACKUP_DIR" -type f -exec chmod 600 {} +
  log "Backup no secreto creado fuera del repo."
  printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
}

main "$@"

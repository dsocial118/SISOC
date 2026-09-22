#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EXPECTED_HOSTNAME="${QA_EXPECTED_HOSTNAME:-mdsldmz-ssies-test}"
SOURCE_SNIPPET="${QA_PWA_SOURCE_SNIPPET:-$REPO_ROOT/docs/operacion/nginx/sisoc-pwas.conf}"
TARGET_SNIPPET="${QA_PWA_TARGET_SNIPPET:-/etc/nginx/snippets/sisoc-pwas.conf}"
SITE_FILE="${QA_NGINX_SITE_FILE:-/etc/nginx/sites-available/staging.conf}"
BACKUP_BASE="${QA_PWA_BACKUP_BASE:-/var/backups/sisoc/pwa-nginx/qa}"
INCLUDE_LINE="    include /etc/nginx/snippets/sisoc-pwas.conf;"
APPLY=0
ASSUME_YES=0
BACKUP_DIR=""
MUTATION_STARTED=0
SNIPPET_EXISTED=0

usage() {
  cat <<'USAGE'
Uso:
  sudo bash scripts/infra/install_qa_pwa_nginx.sh [--apply] [--yes]

Sin --apply ejecuta un preflight de solo lectura. Con --apply:
  - respalda el vhost y el snippet anterior fuera del repositorio;
  - instala las rutas PWA versionadas;
  - agrega un unico include antes del catch-all de SISOC;
  - valida nginx -t y recarga Nginx;
  - restaura ambos archivos si la validacion o la recarga fallan.

No instala las PWA ni modifica DNS, TLS, firewall o el backend SISOC.
USAGE
}

log() {
  printf '[%s] %s\n' "$SCRIPT_NAME" "$*"
}

fail() {
  log "ERROR: $*" >&2
  exit 1
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

render_site_candidate() {
  local output="$1"
  local include_count catch_all_count

  include_count="$(grep -Ec '^[[:space:]]*include[[:space:]]+/etc/nginx/snippets/sisoc-pwas\.conf;[[:space:]]*$' "$SITE_FILE" || true)"
  [[ "$include_count" -le 1 ]] || fail "El vhost contiene mas de un include PWA."
  if [[ "$include_count" -eq 1 ]]; then
    cp -- "$SITE_FILE" "$output"
    return 0
  fi

  catch_all_count="$(grep -Ec '^[[:space:]]*location[[:space:]]+/[[:space:]]*\{' "$SITE_FILE" || true)"
  [[ "$catch_all_count" -eq 1 ]] \
    || fail "Se esperaba exactamente un location / en $SITE_FILE."

  awk -v include_line="$INCLUDE_LINE" '
    /^[[:space:]]*location[[:space:]]+\/[[:space:]]*\{/ && !inserted {
      print include_line
      print ""
      inserted = 1
    }
    { print }
    END { if (!inserted) exit 42 }
  ' "$SITE_FILE" > "$output"
}

preflight() {
  local candidate

  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  [[ -r "$SOURCE_SNIPPET" ]] || fail "No se puede leer $SOURCE_SNIPPET"
  [[ -r "$SITE_FILE" ]] || fail "No se puede leer $SITE_FILE"
  command -v nginx >/dev/null || fail "nginx no esta disponible."
  command -v systemctl >/dev/null || fail "systemctl no esta disponible."
  systemctl is-active --quiet nginx || fail "nginx no esta activo."

  candidate="$(mktemp)"
  render_site_candidate "$candidate"
  [[ "$(grep -Ec '^[[:space:]]*include[[:space:]]+/etc/nginx/snippets/sisoc-pwas\.conf;[[:space:]]*$' "$candidate" || true)" -eq 1 ]] \
    || fail "El candidato no contiene exactamente un include PWA."
  rm -f -- "$candidate"
  nginx -t
  log "Preflight OK: host, vhost, snippet y Nginx validados."
}

rollback_on_error() {
  local rc=$?
  trap - EXIT
  if [[ "$MUTATION_STARTED" -eq 1 && -n "$BACKUP_DIR" ]]; then
    log "Fallo durante la instalacion; restaurando Nginx."
    cp -a -- "$BACKUP_DIR/staging.conf.before" "$SITE_FILE" || true
    if [[ "$SNIPPET_EXISTED" -eq 1 ]]; then
      cp -a -- "$BACKUP_DIR/sisoc-pwas.conf.before" "$TARGET_SNIPPET" || true
    else
      rm -f -- "$TARGET_SNIPPET" || true
    fi
    nginx -t && systemctl reload nginx || true
  fi
  exit "$rc"
}

apply_changes() {
  local candidate timestamp

  timestamp="$(date +%Y%m%d_%H%M%S)"
  install -d -o root -g root -m 700 "$BACKUP_BASE"
  BACKUP_DIR="$(mktemp -d "$BACKUP_BASE/${timestamp}.XXXXXX")"
  chmod 700 "$BACKUP_DIR"
  cp -a -- "$SITE_FILE" "$BACKUP_DIR/staging.conf.before"
  if [[ -e "$TARGET_SNIPPET" ]]; then
    SNIPPET_EXISTED=1
    cp -a -- "$TARGET_SNIPPET" "$BACKUP_DIR/sisoc-pwas.conf.before"
  fi

  candidate="$(mktemp)"
  render_site_candidate "$candidate"
  MUTATION_STARTED=1
  trap rollback_on_error EXIT

  install -d -o root -g root -m 755 "$(dirname "$TARGET_SNIPPET")"
  install -o root -g root -m 644 "$SOURCE_SNIPPET" "$TARGET_SNIPPET"
  install -o root -g root -m 644 "$candidate" "$SITE_FILE"
  rm -f -- "$candidate"

  nginx -t
  systemctl reload nginx
  systemctl is-active --quiet nginx || fail "nginx no quedo activo."
  [[ "$(grep -Ec '^[[:space:]]*include[[:space:]]+/etc/nginx/snippets/sisoc-pwas\.conf;[[:space:]]*$' "$SITE_FILE" || true)" -eq 1 ]] \
    || fail "El vhost final no contiene exactamente un include PWA."
  cmp -s -- "$SOURCE_SNIPPET" "$TARGET_SNIPPET" \
    || fail "El snippet instalado no coincide con el versionado."

  MUTATION_STARTED=0
  trap - EXIT
  log "Rutas PWA instaladas y Nginx recargado."
  printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
}

main() {
  parse_args "$@"
  preflight
  if [[ "$APPLY" -eq 0 ]]; then
    log "Modo read-only. Use --apply cuando corresponda instalar."
    exit 0
  fi
  if [[ "$ASSUME_YES" -eq 0 ]]; then
    read -r -p "Instalar rutas PWA en QA y recargar Nginx? [y/N] " answer
    case "$answer" in
      y|Y|yes|YES|si|SI) ;;
      *) fail "Operacion cancelada." ;;
    esac
  fi
  apply_changes
}

main "$@"

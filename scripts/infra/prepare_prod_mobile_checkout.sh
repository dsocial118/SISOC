#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HOSTNAME="${PROD_EXPECTED_HOSTNAME:-mdsldmz-ssies}"
TARGET_USER="${PROD_MAINTENANCE_USER:-sisoc-deploy}"
TARGET_GROUP="${PROD_MAINTENANCE_GROUP:-sisoc-deploy}"
MOBILE_ROOT="${MOBILE_ROOT:-/sisoc/SISOC-Mobile}"
MOBILE_ENV="$MOBILE_ROOT/.env"
HTTPS_REMOTE="https://github.com/dsocial118/SISOC-Mobile.git"
BACKUP_BASE="${BACKUP_BASE:-/var/backups/sisoc/mobile-checkout-preparation}"
BACKUP_DIR=""
APPLY=0
ASSUME_YES=0
ROLLBACK_NEEDED=0

usage() {
  cat <<'USAGE'
Uso:
  prepare_prod_mobile_checkout.sh [--apply] [--yes]

Sin --apply audita checkout, ownership y remote sin cambiar nada. Con --apply:
  - guarda ACL/owners/modes completos y remote en backup root-only;
  - cambia recursivamente owner/grupo SOLO de /sisoc/SISOC-Mobile al usuario
    del runner;
  - restaura la metadata previa de .env;
  - cambia el origin SSH conocido a HTTPS publica;
  - valida fetch, branch, commit, working tree y health.

No mueve ni borra archivos. El cambio recursivo de owner requiere el GO
explicito de este gate.
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

remote_state() {
  local remote
  remote="$(git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" remote get-url origin 2>/dev/null)" \
    || fail "SISOC-Mobile no tiene origin."
  case "$remote" in
    "$HTTPS_REMOTE"|https://github.com/dsocial118/SISOC-Mobile)
      printf 'https'
      ;;
    git@github.com:dsocial118/SISOC-Mobile.git|ssh://git@github.com/dsocial118/SISOC-Mobile.git)
      printf 'ssh'
      ;;
    *)
      fail "Origin mobile inesperado; no se imprime para evitar exponer credenciales."
      ;;
  esac
}

preflight() {
  local branch tracked_changes non_target_entries state

  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  id "$TARGET_USER" >/dev/null 2>&1 || fail "No existe $TARGET_USER."
  command -v getfacl >/dev/null || fail "getfacl no esta disponible."
  command -v setfacl >/dev/null || fail "setfacl no esta disponible."
  git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || fail "No se encontro el checkout mobile."
  [[ -f "$MOBILE_ENV" ]] || fail "No existe .env mobile."
  branch="$(git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" branch --show-current)"
  [[ "$branch" == main ]] || fail "SISOC-Mobile no esta en main."
  if ! git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" diff-index --quiet HEAD --; then
    tracked_changes="$(git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" diff-index --name-only HEAD -- | wc -l)"
    fail "SISOC-Mobile tiene $tracked_changes archivos tracked modificados."
  fi

  state="$(remote_state)"
  non_target_entries="$(
    find "$MOBILE_ROOT" -xdev ! -path "$MOBILE_ENV" \
      \( ! -user "$TARGET_USER" -o ! -group "$TARGET_GROUP" \) -printf . | wc -c
  )"
  log "branch=main remote=$state entries_outside_target_owner=$non_target_entries"
  if [[ "$non_target_entries" -eq 0 && "$state" == https ]]; then
    runuser -u "$TARGET_USER" -- git -C "$MOBILE_ROOT" status --porcelain >/dev/null \
      || fail "El checkout parece preparado pero el runner no puede usarlo."
    log "Checkout mobile ya esta preparado."
  else
    [[ "$state" == ssh ]] || fail "Estado parcial inesperado del checkout mobile."
    log "Checkout mobile requiere alineacion de owner y remote antes del primer deploy."
  fi
}

rollback_on_error() {
  local rc=$? mobile_owner
  trap - EXIT
  if [[ "$ROLLBACK_NEEDED" -eq 1 && -n "$BACKUP_DIR" ]]; then
    log "Fallo durante preparacion mobile; restaurando ACL/owners y remote."
    if [[ -r "$BACKUP_DIR/mobile-origin.before" ]]; then
      git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" remote set-url origin \
        "$(cat "$BACKUP_DIR/mobile-origin.before")" || true
    fi
    setfacl --restore="$BACKUP_DIR/mobile.acl-ownership.before" || true
    mobile_owner="$(stat -c '%U' "$MOBILE_ROOT")"
    runuser -u "$mobile_owner" -- git -C "$MOBILE_ROOT" update-index --refresh -q \
      >/dev/null 2>&1 || true
    runuser -u "$mobile_owner" -- git -C "$MOBILE_ROOT" diff-index --quiet HEAD -- \
      || log "ERROR: El rollback mobile dejo cambios tracked."
    bash "$SCRIPT_DIR/healthcheck_prod.sh" || true
  fi
  exit "$rc"
}

apply_changes() {
  local timestamp before_head after_head

  timestamp="$(date +%Y%m%d_%H%M%S)"
  BACKUP_DIR="$BACKUP_BASE/$timestamp"
  umask 077
  install -d -o root -g root -m 700 "$BACKUP_DIR"
  getfacl -R -p "$MOBILE_ROOT" > "$BACKUP_DIR/mobile.acl-ownership.before"
  getfacl -p "$MOBILE_ENV" > "$BACKUP_DIR/mobile-env.acl-ownership.before"
  git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" remote get-url origin \
    > "$BACKUP_DIR/mobile-origin.before"
  before_head="$(git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" rev-parse HEAD)"
  printf '%s\n' "$before_head" > "$BACKUP_DIR/mobile-head.before"
  find "$BACKUP_DIR" -type f -exec chmod 600 {} +
  (
    cd "$BACKUP_DIR"
    find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum
  ) > "$BACKUP_DIR/SHA256SUMS"
  chmod 600 "$BACKUP_DIR/SHA256SUMS"

  trap rollback_on_error EXIT
  ROLLBACK_NEEDED=1
  chown -R "$TARGET_USER:$TARGET_GROUP" "$MOBILE_ROOT"
  setfacl --restore="$BACKUP_DIR/mobile-env.acl-ownership.before"
  runuser -u "$TARGET_USER" -- git -C "$MOBILE_ROOT" remote set-url origin "$HTTPS_REMOTE"
  runuser -u "$TARGET_USER" -- git -C "$MOBILE_ROOT" fetch origin --prune
  after_head="$(runuser -u "$TARGET_USER" -- git -C "$MOBILE_ROOT" rev-parse HEAD)"
  [[ "$after_head" == "$before_head" ]] || fail "El fetch cambio el HEAD local."
  [[ "$(runuser -u "$TARGET_USER" -- git -C "$MOBILE_ROOT" branch --show-current)" == main ]] \
    || fail "Mobile dejo de estar en main."
  runuser -u "$TARGET_USER" -- git -C "$MOBILE_ROOT" update-index --refresh -q \
    >/dev/null 2>&1 || true
  runuser -u "$TARGET_USER" -- git -C "$MOBILE_ROOT" diff-index --quiet HEAD -- \
    || fail "Aparecieron cambios tracked en mobile."
  [[ "$(remote_state)" == https ]] || fail "Origin mobile no quedo en HTTPS."
  bash "$SCRIPT_DIR/healthcheck_prod.sh"

  printf 'applied_at=%s\nhead=%s\n' "$(date --iso-8601=seconds)" "$after_head" \
    > "$BACKUP_DIR/PREPARATION_APPLIED"
  chmod 600 "$BACKUP_DIR/PREPARATION_APPLIED"
  (
    cd "$BACKUP_DIR"
    find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum
  ) > "$BACKUP_DIR/SHA256SUMS"
  chmod 600 "$BACKUP_DIR/SHA256SUMS"

  ROLLBACK_NEEDED=0
  trap - EXIT
  log "Checkout mobile preparado para deploy no interactivo."
  printf 'BACKUP_DIR=%s\n' "$BACKUP_DIR"
}

main() {
  parse_args "$@"
  preflight
  if [[ "$APPLY" -eq 0 ]]; then
    log "Modo read-only. Use --apply solo con aprobacion del owner recursivo."
    exit 0
  fi
  if [[ "$ASSUME_YES" -eq 0 ]]; then
    read -r -p "Alinear owner del checkout mobile y cambiar origin a HTTPS? [y/N] " answer
    case "$answer" in
      y|Y|yes|YES|si|SI) ;;
      *) fail "Operacion cancelada." ;;
    esac
  fi
  apply_changes
}

main "$@"

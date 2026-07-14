#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HOSTNAME="${PROD_EXPECTED_HOSTNAME:-mdsldmz-ssies}"
MOBILE_ROOT="${MOBILE_ROOT:-/sisoc/SISOC-Mobile}"
BACKUP_DIR=""
APPLY=0
ASSUME_YES=0

fail() {
  printf '[%s] ERROR: %s\n' "$SCRIPT_NAME" "$*" >&2
  exit 1
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --backup-dir)
        shift
        [[ $# -gt 0 ]] || fail "--backup-dir requiere valor."
        BACKUP_DIR="$1"
        ;;
      --apply) APPLY=1 ;;
      --yes) ASSUME_YES=1 ;;
      -h|--help)
        printf 'Uso: %s --backup-dir PATH [--apply] [--yes]\n' "$SCRIPT_NAME"
        exit 0
        ;;
      *) fail "Opcion no reconocida: $1" ;;
    esac
    shift
  done
}

main() {
  parse_args "$@"
  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  [[ "$BACKUP_DIR" == /var/backups/sisoc/mobile-checkout-preparation/* ]] \
    || fail "Backup fuera de la raiz mobile esperada."
  [[ -r "$BACKUP_DIR/mobile.acl-ownership.before" ]] || fail "Falta backup ACL/owners."
  [[ -r "$BACKUP_DIR/mobile-origin.before" ]] || fail "Falta backup del origin."
  (cd "$BACKUP_DIR" && sha256sum -c SHA256SUMS >/dev/null) \
    || fail "Checksum del backup invalido."

  printf '[%s] Plan: restaurar owners/ACL y origin desde %s\n' "$SCRIPT_NAME" "$BACKUP_DIR"
  if [[ "$APPLY" -eq 0 ]]; then
    printf '[%s] Modo informativo; no se modifico el checkout.\n' "$SCRIPT_NAME"
    exit 0
  fi
  if [[ "$ASSUME_YES" -eq 0 ]]; then
    read -r -p "Restaurar metadata y origin historicos del checkout mobile? [y/N] " answer
    case "$answer" in
      y|Y|yes|YES|si|SI) ;;
      *) fail "Operacion cancelada." ;;
    esac
  fi

  setfacl --restore="$BACKUP_DIR/mobile.acl-ownership.before"
  git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" remote set-url origin \
    "$(cat "$BACKUP_DIR/mobile-origin.before")"
  git -c safe.directory="$MOBILE_ROOT" -C "$MOBILE_ROOT" diff-index --quiet HEAD -- \
    || fail "El checkout mobile tiene cambios tracked despues del rollback."
  bash "$SCRIPT_DIR/healthcheck_prod.sh"
  printf '[%s] Rollback mobile aplicado; health OK.\n' "$SCRIPT_NAME"
}

main "$@"

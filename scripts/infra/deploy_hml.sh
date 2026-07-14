#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EXPECTED_HOSTNAME="${HML_EXPECTED_HOSTNAME:-ldmzssies-homolo}"
MOBILE_ROOT="${HML_MOBILE_ROOT:-/sisoc/SISOC-Mobile}"
APPLY=0
ACK_DB_WRITES=0

usage() {
  cat <<'USAGE'
Uso:
  deploy_hml.sh [--apply --acknowledge-db-writes]

Sin flags muestra el plan. El deploy real actualiza homologacion, reconstruye
backend/mobile y puede escribir DB; requiere aprobacion operativa explicita.
USAGE
}

for argument in "$@"; do
  case "$argument" in
    --apply) APPLY=1 ;;
    --acknowledge-db-writes) ACK_DB_WRITES=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'ERROR: opcion no reconocida: %s\n' "$argument" >&2; exit 1 ;;
  esac
done

if [[ "$APPLY" -eq 0 ]]; then
  printf 'Plan: backup, pull ff-only, rebuild backend/mobile y health check.\n'
  printf 'No se ejecuto ningun cambio.\n'
  exit 0
fi

[[ "$ACK_DB_WRITES" -eq 1 ]] || {
  printf 'ERROR: falta --acknowledge-db-writes\n' >&2
  exit 1
}
[[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || {
  printf 'ERROR: host inesperado\n' >&2
  exit 1
}

bash "$ROOT_DIR/scripts/infra/backup_hml_configs.sh"
bash "$ROOT_DIR/scripts/operacion/deploy_refresh.sh" --yes \
  --with-mobile --mobile-dir "$MOBILE_ROOT"
bash "$ROOT_DIR/scripts/infra/healthcheck_hml.sh"

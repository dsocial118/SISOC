#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APPLY=0
ACK_DB_WRITES=0

usage() {
  cat <<'USAGE'
Uso:
  deploy_qa.sh [--apply --acknowledge-db-writes]

Sin flags muestra el plan. El deploy real actualiza development y reconstruye
el stack. El entrypoint ejecuta migraciones y otros comandos con escritura en
DB; requiere aprobacion operativa explicita antes de usar ambos flags.
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
  printf 'Plan: backup de configuracion, pull ff-only, rebuild y health check.\n'
  printf 'No se ejecuto ningun cambio.\n'
  exit 0
fi

[[ "$ACK_DB_WRITES" -eq 1 ]] || {
  printf 'ERROR: falta --acknowledge-db-writes\n' >&2
  exit 1
}

bash "$ROOT_DIR/scripts/infra/backup_qa_configs.sh"
bash "$ROOT_DIR/scripts/operacion/deploy_refresh.sh" --yes
bash "$ROOT_DIR/scripts/infra/healthcheck_qa.sh"

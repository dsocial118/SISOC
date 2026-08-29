#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
    cat <<'EOF'
Uso: deploy_dispositivos.sh --action deploy|rollback --expected-revision SHA --branch BRANCH \
  --app-root PATH --env-file PATH --rollback-state PATH --compose-file PATH \
  --compose-project NAME --web-service NAME --migrate-service NAME
EOF
}

ACTION=""
EXPECTED_REVISION=""
BRANCH=""
APP_ROOT=""
ENV_FILE=""
ROLLBACK_STATE=""
COMPOSE_FILE=""
COMPOSE_PROJECT=""
WEB_SERVICE=""
MIGRATE_SERVICE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --action) ACTION="$2"; shift 2 ;;
        --expected-revision) EXPECTED_REVISION="$2"; shift 2 ;;
        --branch) BRANCH="$2"; shift 2 ;;
        --app-root) APP_ROOT="$2"; shift 2 ;;
        --env-file) ENV_FILE="$2"; shift 2 ;;
        --rollback-state) ROLLBACK_STATE="$2"; shift 2 ;;
        --compose-file) COMPOSE_FILE="$2"; shift 2 ;;
        --compose-project) COMPOSE_PROJECT="$2"; shift 2 ;;
        --web-service) WEB_SERVICE="$2"; shift 2 ;;
        --migrate-service) MIGRATE_SERVICE="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Argumento no reconocido: $1" >&2; usage >&2; exit 2 ;;
    esac
done

[[ "$ACTION" == "deploy" || "$ACTION" == "rollback" ]] || {
    echo "--action debe ser deploy o rollback." >&2
    exit 2
}
for variable in EXPECTED_REVISION BRANCH APP_ROOT ENV_FILE ROLLBACK_STATE COMPOSE_FILE COMPOSE_PROJECT WEB_SERVICE MIGRATE_SERVICE; do
    [[ -n "${!variable}" ]] || {
        echo "Falta --${variable,,}." >&2
        exit 2
    }
done

[[ "$EXPECTED_REVISION" =~ ^[0-9a-f]{40}$ ]] || {
    echo "--expected-revision debe ser un SHA completo." >&2
    exit 2
}
git -C "$APP_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    echo "El checkout aislado no es un repositorio Git." >&2
    exit 1
}
[[ -r "$ENV_FILE" && -r "$COMPOSE_FILE" ]] || {
    echo "Checkout, entorno o Compose no están disponibles." >&2
    exit 1
}
[[ -f "$ROLLBACK_STATE" || -d "$(dirname "$ROLLBACK_STATE")" ]] || {
    echo "El directorio de rollback no existe." >&2
    exit 1
}

compose=(docker compose --project-name "$COMPOSE_PROJECT" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" --project-directory "$APP_ROOT")

ensure_clean_checkout() {
    [[ -z "$(git -C "$APP_ROOT" status --porcelain)" ]] || {
        echo "El checkout aislado no está limpio." >&2
        exit 1
    }
}

prepare_deploy_source() {
    ensure_clean_checkout
    git -C "$APP_ROOT" fetch origin --prune
    remote_sha="$(git -C "$APP_ROOT" rev-parse "origin/$BRANCH")"
    [[ "$remote_sha" == "$EXPECTED_REVISION" ]] || {
        echo "El SHA solicitado no coincide con origin/$BRANCH." >&2
        exit 1
    }
    git -C "$APP_ROOT" checkout "$BRANCH"
    git -C "$APP_ROOT" merge --ff-only "origin/$BRANCH"
    source_sha="$(git -C "$APP_ROOT" rev-parse HEAD)"
    [[ "$source_sha" == "$EXPECTED_REVISION" ]] || {
        echo "El checkout no coincide con el SHA autorizado." >&2
        exit 1
    }
}

start_source() {
    local source_sha="$1"
    export DISPOSITIVOS_ENV_FILE="$ENV_FILE"
    export DISPOSITIVOS_SOURCE_SHA="$source_sha"
    "${compose[@]}" config -q
    "${compose[@]}" build "$WEB_SERVICE"
    "${compose[@]}" --profile migrate run --rm --no-build --no-deps "$MIGRATE_SERVICE"
    "${compose[@]}" up -d --no-build "$WEB_SERVICE"
    running_services="$("${compose[@]}" ps --services --status running)"
    [[ "$running_services" == "$WEB_SERVICE" ]] || {
        echo "El proceso web aislado no quedó en ejecución." >&2
        "${compose[@]}" ps >&2 || true
        exit 1
    }
}

if [[ "$ACTION" == "deploy" ]]; then
    previous_sha="$(git -C "$APP_ROOT" rev-parse HEAD)"
    prepare_deploy_source
    start_source "$EXPECTED_REVISION"
    umask 077
    printf '%s\n' "$previous_sha" > "$ROLLBACK_STATE"
    chmod 600 "$ROLLBACK_STATE"
    echo "Deploy aislado de Dispositivos verificado en $EXPECTED_REVISION."
    exit 0
fi

[[ -s "$ROLLBACK_STATE" ]] || {
    echo "No existe un SHA previo para rollback." >&2
    exit 1
}
rollback_sha="$(tr -d '\r\n' < "$ROLLBACK_STATE")"
[[ "$rollback_sha" =~ ^[0-9a-f]{40}$ ]] || {
    echo "El estado de rollback no contiene un SHA válido." >&2
    exit 1
}
ensure_clean_checkout
git -C "$APP_ROOT" fetch origin --prune
git -C "$APP_ROOT" cat-file -e "$rollback_sha^{commit}"
current_sha="$(git -C "$APP_ROOT" rev-parse HEAD)"
git -C "$APP_ROOT" checkout --detach "$rollback_sha"
start_source "$rollback_sha"
umask 077
printf '%s\n' "$current_sha" > "$ROLLBACK_STATE"
chmod 600 "$ROLLBACK_STATE"
echo "Rollback aislado de Dispositivos verificado en $rollback_sha."

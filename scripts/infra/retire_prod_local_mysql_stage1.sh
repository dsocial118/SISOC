#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HOSTNAME="${PROD_EXPECTED_HOSTNAME:-mdsldmz-ssies}"
EXPECTED_DB_HOST="${PROD_EXPECTED_DB_HOST:-10.80.5.46}"
EXPECTED_DB_SERVER="${PROD_EXPECTED_DB_SERVER:-ldmzsql-sisoc}"
EXPECTED_DB_NAME="${PROD_EXPECTED_DB_NAME:-sisoc_local}"
EXPECTED_LOCAL_UUID="${PROD_EXPECTED_LOCAL_MYSQL_UUID:-39c3f26e-78f1-11f0-8e8b-005056a21960}"
CONTAINER_NAME="${PROD_DJANGO_CONTAINER:-sisoc-django-1}"
BACKUP_BASE="${BACKUP_BASE:-/var/backups/sisoc/mysql-local-retirement/prod}"
APPLY=0
ASSUME_YES=0
ROLLBACK_NEEDED=0
BACKUP_DIR=""
MYSQL=(mysql --protocol=socket --batch --skip-column-names --raw)

usage() {
  cat <<'USAGE'
Uso:
  retire_prod_local_mysql_stage1.sh [--apply] [--yes]

Sin --apply ejecuta solo el preflight. Stage 1 crea backup root-only y
detiene/deshabilita el MySQL local. Conserva paquetes, configuracion y datadir
por al menos 14 dias; nunca ejecuta DROP, purge ni borrado.
USAGE
}

log() {
  printf '[%s] %s\n' "$SCRIPT_NAME" "$*"
}

fail() {
  log "ERROR: $*" >&2
  exit 1
}

rollback_on_error() {
  local rc=$?
  if [[ "$ROLLBACK_NEEDED" -eq 1 ]]; then
    log "Fallo posterior al stop; restaurando mysql.service."
    systemctl enable mysql >/dev/null 2>&1 || true
    systemctl start mysql || true
  fi
  exit "$rc"
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

django_db_identity() {
  docker exec "$CONTAINER_NAME" python manage.py shell -c \
    "from django.db import connection; connection.ensure_connection(); c=connection.cursor(); c.execute('SELECT @@hostname, @@server_uuid, DATABASE()'); row=c.fetchone(); c.close(); print(str(connection.settings_dict.get('HOST'))+'|'+str(connection.connection.get_host_info())+'|'+str(row[0])+'|'+str(row[1])+'|'+str(row[2]))" \
    | tail -n 1
}

validate_django_remote_db() {
  local identity configured_host connection_info actual_server actual_uuid actual_db
  identity="$(django_db_identity)"
  IFS='|' read -r configured_host connection_info actual_server actual_uuid actual_db <<< "$identity"
  [[ "$configured_host" == "$EXPECTED_DB_HOST" ]] \
    || fail "Django configura un host inesperado."
  [[ "$connection_info" == *"$EXPECTED_DB_HOST"* ]] \
    || fail "Django no conecta por TCP al host esperado."
  [[ "$actual_server" == "$EXPECTED_DB_SERVER" ]] \
    || fail "Servidor DB inesperado."
  [[ "$actual_db" == "$EXPECTED_DB_NAME" ]] \
    || fail "Schema DB inesperado."
  log "Django DB: configured=$configured_host actual=$actual_server uuid=$actual_uuid database=$actual_db"
}

preflight_local_mysql() {
  local local_identity local_uuid application_schemas unexpected_connections
  local enabled_events replica_channels group_members

  systemctl is-active --quiet mysql || fail "mysql.service no esta activo."
  systemctl is-enabled --quiet mysql || fail "mysql.service no esta habilitado."
  [[ -d /var/lib/mysql ]] || fail "No existe /var/lib/mysql"

  local_identity="$("${MYSQL[@]}" -e "SELECT CONCAT(@@hostname, '|', @@server_uuid, '|', @@server_id, '|', @@event_scheduler);")"
  local_uuid="$("${MYSQL[@]}" -e "SELECT @@server_uuid;")"
  [[ "$local_uuid" == "$EXPECTED_LOCAL_UUID" ]] \
    || fail "UUID del MySQL local inesperado."
  log "MySQL local: $local_identity"

  application_schemas="$("${MYSQL[@]}" -e "
    SELECT COUNT(*) FROM information_schema.schemata
    WHERE schema_name NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys');
  ")"
  unexpected_connections="$("${MYSQL[@]}" -e "
    SELECT COUNT(*) FROM information_schema.processlist
    WHERE ID <> CONNECTION_ID()
      AND NOT (USER = 'event_scheduler' AND COMMAND = 'Daemon');
  ")"
  enabled_events="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM information_schema.EVENTS WHERE STATUS = 'ENABLED';")"
  replica_channels="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM performance_schema.replication_connection_status WHERE SERVICE_STATE = 'ON';")"
  group_members="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM performance_schema.replication_group_members WHERE MEMBER_STATE = 'ONLINE';")"

  log "preflight application_schemas=$application_schemas unexpected_connections=$unexpected_connections enabled_events=$enabled_events replica_channels=$replica_channels group_members=$group_members"
  (( application_schemas == 0 )) || fail "Hay schemas locales no clasificados."
  (( unexpected_connections == 0 )) || fail "Hay conexiones locales no clasificadas."
  (( enabled_events == 0 )) || fail "Hay eventos MySQL habilitados."
  (( replica_channels == 0 )) || fail "Hay canales de replicacion activos."
  (( group_members == 0 )) || fail "Hay miembros Group Replication online."
}

create_backup() {
  local timestamp
  timestamp="$(date +%Y%m%d_%H%M%S)"
  BACKUP_DIR="$BACKUP_BASE/$timestamp"
  umask 077
  install -d -o root -g root -m 700 "$BACKUP_DIR" "$BACKUP_DIR/metadata"

  cp -a /etc/mysql "$BACKUP_DIR/etc-mysql"
  cp -a /var/lib/mysql/auto.cnf "$BACKUP_DIR/metadata/auto.cnf"
  systemctl cat mysql > "$BACKUP_DIR/metadata/mysql.service.txt"
  systemctl status mysql --no-pager > "$BACKUP_DIR/metadata/mysql.status.before.txt"
  systemctl is-enabled mysql > "$BACKUP_DIR/metadata/mysql.enabled.before.txt"
  du -sh /var/lib/mysql > "$BACKUP_DIR/metadata/datadir-size.txt"
  ss -Hlnpt 'sport = :3306' > "$BACKUP_DIR/metadata/listener-3306.before.txt" || true
  ss -Hlnpt 'sport = :33060' > "$BACKUP_DIR/metadata/listener-33060.before.txt" || true
  dpkg-query -W -f='${binary:Package}\t${Version}\t${db:Status-Status}\n' 'mysql-server*' \
    > "$BACKUP_DIR/metadata/packages.txt" 2>/dev/null || true
  "${MYSQL[@]}" -e "SELECT @@hostname, @@port, @@server_uuid, @@server_id, @@datadir, @@event_scheduler, @@read_only, @@super_read_only;" \
    > "$BACKUP_DIR/metadata/server-identity.tsv"
  "${MYSQL[@]}" -e "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;" \
    > "$BACKUP_DIR/metadata/schemas.tsv"
  "${MYSQL[@]}" -e "
    SELECT ID, USER, HOST, COALESCE(DB, '-'), COMMAND, TIME, COALESCE(STATE, '-')
    FROM information_schema.processlist WHERE ID <> CONNECTION_ID();
  " > "$BACKUP_DIR/metadata/processlist.tsv"
  "${MYSQL[@]}" -e "
    SELECT CHANNEL_NAME, HOST, PORT FROM performance_schema.replication_connection_configuration;
  " > "$BACKUP_DIR/metadata/replication.tsv"
  "${MYSQL[@]}" -e "
    SELECT EVENT_SCHEMA, EVENT_NAME, STATUS, INTERVAL_VALUE, INTERVAL_FIELD, LAST_EXECUTED
    FROM information_schema.EVENTS ORDER BY EVENT_SCHEMA, EVENT_NAME;
  " > "$BACKUP_DIR/metadata/events.tsv"
  django_db_identity > "$BACKUP_DIR/metadata/django-db-identity.txt"

  (
    cd "$BACKUP_DIR"
    find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum
  ) > "$BACKUP_DIR/SHA256SUMS"
  find "$BACKUP_DIR" -type d -exec chmod 700 {} +
  find "$BACKUP_DIR" -type f -exec chmod 600 {} +
  log "Backup root-only creado en $BACKUP_DIR"
}

verify_after_stop() {
  systemctl is-active --quiet mysql && fail "mysql.service sigue activo."
  systemctl is-enabled --quiet mysql && fail "mysql.service sigue habilitado."
  if ss -Hlnpt 'sport = :3306' | grep -q .; then
    fail "El puerto local 3306 sigue escuchando."
  fi
  if ss -Hlnpt 'sport = :33060' | grep -q .; then
    fail "El puerto local 33060 sigue escuchando."
  fi
  validate_django_remote_db
  bash "$SCRIPT_DIR/healthcheck_prod.sh"
}

main() {
  parse_args "$@"
  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  command -v mysql >/dev/null || fail "mysql client no esta disponible."
  command -v docker >/dev/null || fail "Docker no esta disponible."
  [[ -r "$SCRIPT_DIR/healthcheck_prod.sh" ]] || fail "Falta healthcheck_prod.sh."

  bash "$SCRIPT_DIR/healthcheck_prod.sh"
  validate_django_remote_db
  preflight_local_mysql

  if [[ "$APPLY" -eq 0 ]]; then
    log "Preflight OK. Plan: backup, stop+disable y verificacion; sin purge."
    exit 0
  fi
  if [[ "$ASSUME_YES" -eq 0 ]]; then
    read -r -p "Detener y deshabilitar solo el MySQL local de PRD? [y/N] " answer
    case "$answer" in
      y|Y|yes|YES|si|SI) ;;
      *) fail "Operacion cancelada." ;;
    esac
  fi

  create_backup
  trap rollback_on_error EXIT
  ROLLBACK_NEEDED=1
  timeout 60 systemctl stop mysql
  systemctl disable mysql
  verify_after_stop

  printf 'applied_at=%s\nobserve_until=%s\n' \
    "$(date --iso-8601=seconds)" "$(date -d '+14 days' --iso-8601=seconds)" \
    > "$BACKUP_DIR/STAGE1_APPLIED"
  chmod 600 "$BACKUP_DIR/STAGE1_APPLIED"
  (
    cd "$BACKUP_DIR"
    find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum
  ) > "$BACKUP_DIR/SHA256SUMS"

  ROLLBACK_NEEDED=0
  trap - EXIT
  log "Stage 1 finalizado. MySQL local inactivo/deshabilitado; datadir y paquetes intactos."
  log "Observar 14 dias antes de cualquier purge. Backup: $BACKUP_DIR"
  df -h /
}

main "$@"

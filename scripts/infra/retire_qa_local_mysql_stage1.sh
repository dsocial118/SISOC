#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
EXPECTED_HOSTNAME="${QA_EXPECTED_HOSTNAME:-mdsldmz-ssies-test}"
EXPECTED_DB_HOST="${QA_EXPECTED_DB_HOST:-10.80.9.18}"
EXPECTED_DB_SERVER="${QA_EXPECTED_DB_SERVER:-ltestsql-ssies}"
CONTAINER_NAME="${QA_DJANGO_CONTAINER:-backoffice-django-1}"
BACKUP_BASE="${BACKUP_BASE:-/var/backups/sisoc/mysql-local-retirement}"
APPLY=0
ASSUME_YES=0
ROLLBACK_NEEDED=0
BACKUP_DIR=""
MYSQL=(mysql --protocol=socket --batch --skip-column-names)

usage() {
  cat <<'USAGE'
Uso:
  retire_qa_local_mysql_stage1.sh [--apply] [--yes]

Sin --apply ejecuta preflight y muestra el plan. Stage 1 detiene y deshabilita
solo el MySQL local; no borra paquetes, schemas ni /var/lib/mysql.
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
    || fail "Django configura un host inesperado: $configured_host"
  [[ "$connection_info" == *"$EXPECTED_DB_HOST"* ]] \
    || fail "Django no conecta por TCP al host esperado."
  [[ "$actual_server" == "$EXPECTED_DB_SERVER" ]] \
    || fail "Servidor DB inesperado: $actual_server"
  log "Django DB: configured=$configured_host actual=$actual_server uuid=$actual_uuid database=$actual_db"
}

preflight_local_mysql() {
  local unexpected_connections enabled_events replica_channels group_members local_identity

  systemctl is-active --quiet mysql || fail "mysql.service no esta activo."
  systemctl is-enabled --quiet mysql || fail "mysql.service no esta habilitado."
  [[ -d /var/lib/mysql ]] || fail "No existe /var/lib/mysql"

  local_identity="$("${MYSQL[@]}" -e "SELECT CONCAT(@@hostname, '|', @@server_uuid, '|', @@server_id, '|', @@event_scheduler);")"
  log "MySQL local: $local_identity"

  unexpected_connections="$("${MYSQL[@]}" -e "
    SELECT COUNT(*)
    FROM information_schema.processlist
    WHERE ID <> CONNECTION_ID()
      AND NOT (USER = 'event_scheduler' AND COMMAND = 'Daemon');
  ")"
  enabled_events="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM information_schema.EVENTS WHERE STATUS = 'ENABLED';")"
  replica_channels="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM performance_schema.replication_connection_status WHERE SERVICE_STATE = 'ON';")"
  group_members="$("${MYSQL[@]}" -e "SELECT COUNT(*) FROM performance_schema.replication_group_members WHERE MEMBER_STATE = 'ONLINE';")"

  log "preflight unexpected_connections=$unexpected_connections enabled_events=$enabled_events replica_channels=$replica_channels group_members=$group_members"

  if (( unexpected_connections > 0 )); then
    "${MYSQL[@]}" -e "
      SELECT ID, USER, HOST, COALESCE(DB, '-'), COMMAND, TIME, COALESCE(STATE, '-')
      FROM information_schema.processlist
      WHERE ID <> CONNECTION_ID()
        AND NOT (USER = 'event_scheduler' AND COMMAND = 'Daemon');
    "
    fail "Hay conexiones locales no clasificadas; no se detiene MySQL."
  fi
  (( enabled_events == 0 )) || {
    "${MYSQL[@]}" -e "SELECT EVENT_SCHEMA, EVENT_NAME, STATUS, INTERVAL_VALUE, INTERVAL_FIELD FROM information_schema.EVENTS WHERE STATUS = 'ENABLED';"
    fail "Hay eventos MySQL habilitados; no se detiene MySQL."
  }
  (( replica_channels == 0 )) || fail "Hay canales de replicacion activos."
  (( group_members == 0 )) || fail "Hay miembros de Group Replication online."
}

create_backup() {
  local timestamp
  timestamp="$(date +%Y%m%d_%H%M%S)"
  BACKUP_DIR="$BACKUP_BASE/$timestamp"
  umask 077
  mkdir -p "$BACKUP_DIR/metadata"
  chmod 700 "$BACKUP_DIR"

  cp -a /etc/mysql "$BACKUP_DIR/etc-mysql"
  cp -a /var/lib/mysql/auto.cnf "$BACKUP_DIR/metadata/auto.cnf"
  systemctl cat mysql > "$BACKUP_DIR/metadata/mysql.service.txt"
  systemctl status mysql --no-pager > "$BACKUP_DIR/metadata/mysql.status.before.txt"
  systemctl is-enabled mysql > "$BACKUP_DIR/metadata/mysql.enabled.before.txt"
  du -sh /var/lib/mysql > "$BACKUP_DIR/metadata/datadir-size.txt"
  dpkg-query -W -f='${binary:Package}\t${Version}\t${db:Status-Status}\n' 'mysql-server*' \
    > "$BACKUP_DIR/metadata/packages.txt" 2>/dev/null || true

  "${MYSQL[@]}" -e "SELECT @@hostname, @@port, @@server_uuid, @@server_id, @@datadir, @@event_scheduler, @@read_only, @@super_read_only;" \
    > "$BACKUP_DIR/metadata/server-identity.tsv"
  "${MYSQL[@]}" -e "
    SELECT table_schema, ROUND(SUM(data_length + index_length) / 1024 / 1024, 1)
    FROM information_schema.tables
    WHERE table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
    GROUP BY table_schema ORDER BY SUM(data_length + index_length) DESC;
  " > "$BACKUP_DIR/metadata/schema-sizes-mib.tsv"
  "${MYSQL[@]}" -e "
    SELECT ID, USER, HOST, COALESCE(DB, '-'), COMMAND, TIME, COALESCE(STATE, '-')
    FROM information_schema.processlist WHERE ID <> CONNECTION_ID();
  " > "$BACKUP_DIR/metadata/processlist.tsv"
  "${MYSQL[@]}" -e "
    SELECT COALESCE(USER, '<internal>'), COALESCE(HOST, '<internal>'), CURRENT_CONNECTIONS, TOTAL_CONNECTIONS
    FROM performance_schema.accounts WHERE TOTAL_CONNECTIONS > 0 ORDER BY TOTAL_CONNECTIONS DESC;
  " > "$BACKUP_DIR/metadata/accounts.tsv"
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
  chmod -R go-rwx "$BACKUP_DIR"
  log "Backup root-only creado en $BACKUP_DIR"
}

verify_after_stop() {
  systemctl is-active --quiet mysql && fail "mysql.service sigue activo."
  systemctl is-enabled --quiet mysql && fail "mysql.service sigue habilitado."
  if ss -Hlnpt 'sport = :3306' | grep -q .; then
    ss -Hlnpt 'sport = :3306'
    fail "El puerto local 3306 sigue escuchando."
  fi

  [[ "$(docker inspect --format '{{.State.Running}}' backoffice-django-1)" == "true" ]] \
    || fail "El contenedor Django no esta activo."
  [[ "$(docker inspect --format '{{.State.Running}}' backoffice-ocr_worker-1)" == "true" ]] \
    || fail "El contenedor OCR no esta activo."
  validate_django_remote_db
  curl --max-time 8 -fsS -o /dev/null http://127.0.0.1/
  curl --max-time 8 -fsS -o /dev/null http://127.0.0.1/health/
}

main() {
  parse_args "$@"
  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."
  command -v mysql >/dev/null || fail "No esta disponible mysql client."
  command -v docker >/dev/null || fail "No esta disponible Docker."

  validate_django_remote_db
  preflight_local_mysql

  if [[ "$APPLY" -eq 0 ]]; then
    log "Preflight OK. Plan: backup, stop+disable, verificacion; datadir y paquetes quedan intactos."
    exit 0
  fi

  if [[ "$ASSUME_YES" -eq 0 ]]; then
    read -r -p "Detener y deshabilitar solo el MySQL local, conservando 43 GB? [y/N] " answer
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
    "$(date --iso-8601=seconds)" "$(date -d '+7 days' --iso-8601=seconds)" \
    > "$BACKUP_DIR/STAGE1_APPLIED"
  chmod 600 "$BACKUP_DIR/STAGE1_APPLIED"
  (
    cd "$BACKUP_DIR"
    find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum
  ) > "$BACKUP_DIR/SHA256SUMS"

  ROLLBACK_NEEDED=0
  trap - EXIT
  log "Stage 1 finalizado. MySQL local inactivo/deshabilitado; datadir y paquetes intactos."
  log "Observar siete dias antes de cualquier borrado o purge. Backup: $BACKUP_DIR"
  df -h /
}

main "$@"

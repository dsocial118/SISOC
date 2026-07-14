#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_HOSTNAME="${HML_EXPECTED_HOSTNAME:-ldmzssies-homolo}"
EXPECTED_DB_HOST="${HML_EXPECTED_DB_HOST:-10.80.5.48}"
MYSQL=(mysql --protocol=socket --batch --skip-column-names --raw)

log() {
  printf '[audit_hml_root_readonly.sh] %s\n' "$*"
}

fail() {
  log "ERROR: $*" >&2
  exit 1
}

main() {
  [[ "$EUID" -eq 0 ]] || fail "Ejecutar como root mediante sudo."
  [[ "$(hostname -s)" == "$EXPECTED_HOSTNAME" ]] || fail "Host inesperado."

  log "Auditoria read-only; no detiene servicios ni modifica archivos."

  printf 'FILESYSTEM\n'
  df -hT /
  df -ih /
  du -xsh /var/lib/mysql /var/lib/docker /var/log /sisoc 2>/dev/null || true

  printf 'MYSQL_SERVICE\n'
  systemctl show mysql -p ActiveState -p UnitFileState -p FragmentPath \
    -p ActiveEnterTimestamp --no-pager
  ss -Hlnpt 'sport = :3306' || true
  ss -Htn state established '( sport = :3306 )' || true

  command -v mysql >/dev/null || fail "No esta disponible mysql client."
  systemctl is-active --quiet mysql || fail "mysql.service no esta activo."

  printf 'MYSQL_IDENTITY\n'
  "${MYSQL[@]}" -e "
    SELECT @@hostname, @@port, @@server_uuid, @@server_id, @@datadir,
           @@event_scheduler, @@read_only, @@super_read_only;
  "

  printf 'APPLICATION_SCHEMAS_MIB\n'
  "${MYSQL[@]}" -e "
    SELECT table_schema,
           ROUND(SUM(data_length + index_length) / 1024 / 1024, 1)
    FROM information_schema.tables
    WHERE table_schema NOT IN
      ('information_schema', 'performance_schema', 'mysql', 'sys')
    GROUP BY table_schema
    ORDER BY SUM(data_length + index_length) DESC;
  "

  printf 'CONNECTIONS_NO_QUERY_TEXT\n'
  "${MYSQL[@]}" -e "
    SELECT ID, USER, HOST, COALESCE(DB, '-'), COMMAND, TIME,
           COALESCE(STATE, '-')
    FROM information_schema.processlist
    WHERE ID <> CONNECTION_ID()
    ORDER BY TIME DESC;
  "

  printf 'MYSQL_SCHEDULERS_AND_REPLICATION\n'
  "${MYSQL[@]}" -e "
    SELECT 'enabled_events', COUNT(*)
    FROM information_schema.EVENTS WHERE STATUS = 'ENABLED'
    UNION ALL
    SELECT 'active_replica_channels', COUNT(*)
    FROM performance_schema.replication_connection_status
    WHERE SERVICE_STATE = 'ON'
    UNION ALL
    SELECT 'online_group_members', COUNT(*)
    FROM performance_schema.replication_group_members
    WHERE MEMBER_STATE = 'ONLINE';
  "

  printf 'ENABLED_EVENTS_METADATA\n'
  "${MYSQL[@]}" -e "
    SELECT EVENT_SCHEMA, EVENT_NAME, STATUS, INTERVAL_VALUE, INTERVAL_FIELD,
           LAST_EXECUTED
    FROM information_schema.EVENTS
    WHERE STATUS = 'ENABLED'
    ORDER BY EVENT_SCHEMA, EVENT_NAME;
  "

  printf 'REPLICATION_METADATA\n'
  "${MYSQL[@]}" -e "
    SELECT CHANNEL_NAME, HOST, PORT
    FROM performance_schema.replication_connection_configuration;
  "

  printf 'SYSTEM_REFERENCES\n'
  grep -RIlE '(localhost|127\.0\.0\.1).*(3306|mysql)|mysql.*(localhost|127\.0\.0\.1)' \
    /etc/systemd/system /etc/cron.d /etc/crontab 2>/dev/null || true

  printf 'PACKAGES\n'
  dpkg-query -W -f='${binary:Package}\t${Version}\t${db:Status-Status}\n' \
    'mysql-server*' 2>/dev/null || true

  if timeout 3 bash -c "</dev/tcp/$EXPECTED_DB_HOST/3306" 2>/dev/null; then
    printf 'REMOTE_DB_REACHABLE host=%s port=3306\n' "$EXPECTED_DB_HOST"
  else
    printf 'REMOTE_DB_UNREACHABLE host=%s port=3306\n' "$EXPECTED_DB_HOST"
  fi

  log "Auditoria read-only finalizada."
}

main "$@"

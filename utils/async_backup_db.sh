#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Uso: $0 <DB_USER> <DB_PASS> <DB_NAME> <DB_HOST>"
  exit 1
fi

DB_USER="$1"
DB_PASS="$2"
DB_NAME="$3"
DB_HOST="$4"

TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
BACKUP_FILE="backup_${DB_NAME}_${TIMESTAMP}.sql"
LOG_FILE="backup_${DB_NAME}_${TIMESTAMP}.log"

nohup mysqldump \
  --single-transaction \
  --skip-lock-tables \
  --routines \
  --triggers \
  --default-character-set=utf8mb4 \
  -h"$DB_HOST" \
  -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" \
  > "$BACKUP_FILE" 2> "$LOG_FILE" &

echo "Backup iniciado en segundo plano (PID $!)."
echo "– Archivo: $BACKUP_FILE"
echo "– Log:     $LOG_FILE"

#!/usr/bin/env bash
# Резервная копия PostgreSQL production-стека с ротацией.
#
# Использование:
#   bash deploy/backup.sh
#   BACKUP_RETENTION_DAYS=30 bash deploy/backup.sh
#
# Cron (setup-vps.sh добавляет автоматически):
#   15 3 * * * cd /opt/medical_booking && bash deploy/backup.sh >> logs/backup.log 2>&1

set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BACKUP_DIR="${BACKUP_DIR:-${APP_DIR}/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

cd "$APP_DIR"
COMPOSE=(docker compose -f docker-compose.prod.yml --env-file .env.production)

mkdir -p "$BACKUP_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
FILE="${BACKUP_DIR}/backup_${TS}.sql.gz"

echo "[$(date '+%F %T')] Создание бэкапа: $FILE"
"${COMPOSE[@]}" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "$FILE"

# Проверяем, что дамп не пустой.
if [ ! -s "$FILE" ]; then
    echo "Ошибка: бэкап пустой" >&2
    rm -f "$FILE"
    exit 1
fi

echo "[$(date '+%F %T')] Готово: $(du -h "$FILE" | cut -f1)"

if [ "$RETENTION_DAYS" -gt 0 ]; then
    find "$BACKUP_DIR" -name 'backup_*.sql.gz' -type f -mtime +"$RETENTION_DAYS" -print -delete
fi

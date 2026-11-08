@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Восстановление из резервной копии
echo Укажите файл backup в команде ниже:
REM docker compose -f docker-compose.prod.yml --env-file .env.production exec -T db sh -c "psql -U $POSTGRES_USER -d $POSTGRES_DB" < backups\backup_YYYYMMDD_HHMM.sql
echo После восстановления откройте приложение и проверьте данные.

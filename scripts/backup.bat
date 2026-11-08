@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Создание резервной копии
if not exist backups mkdir backups
for /f "tokens=1-4 delims=/.: " %%a in ("%date% %time%") do set TS=%%c%%b%%a_%%d
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T db sh -c "pg_dump -U $POSTGRES_USER $POSTGRES_DB" > backups\backup_%TS%.sql
echo Backup создан: backups\backup_%TS%.sql

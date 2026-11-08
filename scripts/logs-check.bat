@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Логи приложения
if not exist reports mkdir reports
docker compose -f docker-compose.prod.yml --env-file .env.production logs --no-color --tail=100 web celery celery-beat nginx > reports\logs_tail.txt
type reports\logs_tail.txt

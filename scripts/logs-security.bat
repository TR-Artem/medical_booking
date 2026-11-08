@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Логи безопасности
if not exist reports mkdir reports
docker compose -f docker-compose.prod.yml --env-file .env.production logs --no-color --tail=100 web celery nginx > reports\security_logs.txt
findstr /I /C:"Traceback" /C:"ERROR" /C:"CRITICAL" reports\security_logs.txt

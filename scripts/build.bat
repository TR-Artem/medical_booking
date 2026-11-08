@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Сборка проекта
docker compose -f docker-compose.prod.yml --env-file .env.production build

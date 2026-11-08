@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Контейнеры и порты
docker compose -f docker-compose.prod.yml --env-file .env.production ps
echo Порты хоста
netstat -ano | findstr LISTENING

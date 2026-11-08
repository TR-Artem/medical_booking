@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ========================================
echo  Перезапуск production/demo-стенда
echo ========================================

docker compose -f docker-compose.prod.yml --env-file .env.production down
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
docker compose -f docker-compose.prod.yml --env-file .env.production ps

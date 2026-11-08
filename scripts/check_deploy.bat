@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ========================================
echo  Проверка после развертывания
echo ========================================

docker compose -f docker-compose.prod.yml --env-file .env.production ps
docker compose -f docker-compose.prod.yml --env-file .env.production logs --tail=80
curl -s -o NUL -w "HTTP %%{http_code}\n" http://localhost/

@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ========================================
echo  Развертывание production/demo-стенда
echo ========================================

if not exist .env.production (
  echo Создайте .env.production из .env.production.example
  exit /b 1
)

docker compose -f docker-compose.prod.yml --env-file .env.production up --build -d
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T web python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T web python manage.py collectstatic --noinput --clear
docker compose -f docker-compose.prod.yml --env-file .env.production restart web
docker compose -f docker-compose.prod.yml --env-file .env.production restart nginx
docker compose -f docker-compose.prod.yml --env-file .env.production ps

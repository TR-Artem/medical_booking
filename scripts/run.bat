@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ========================================
echo  Запуск проекта
echo ========================================

docker compose up --build -d
docker compose exec -T web python manage.py migrate --noinput
docker compose exec -T web python manage.py collectstatic --noinput --clear
docker compose restart nginx
echo Открыть: http://localhost:8080

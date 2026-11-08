@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Запуск тестов
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T web python manage.py test

@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Финальная проверка перед релизом
docker compose -f docker-compose.prod.yml --env-file .env.production --profile tools run --rm tools sh -c "ruff check . && black --check . && python manage.py test"

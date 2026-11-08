@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ========================================
echo  Проверка качества: линтер, форматтер, тесты
echo ========================================

docker compose up -d --build
docker compose exec -T web sh -c "ruff check . && black --check . && python manage.py test"

@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ========================================
echo  Форматирование кода
echo ========================================

docker compose exec -T web sh -c "ruff check --fix . && black ."

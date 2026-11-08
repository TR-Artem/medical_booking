@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ========================================
echo  Запуск проекта
echo ========================================

docker compose up --build -d
echo Открыть: http://localhost:8000

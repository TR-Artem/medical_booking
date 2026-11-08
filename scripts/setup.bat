@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ========================================
echo  Установка и сборка проекта
echo ========================================

if not exist .env copy .env.example .env > nul
docker compose build

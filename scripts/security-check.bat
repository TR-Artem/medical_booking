@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Проверка секретов и .env
git ls-files | findstr /I ".env"
git grep -n -i -E "password|secret|token|api_key|jwt" -- . ":!docs" ":!*.md"

@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Общая проверка качества
call scripts\test.bat
call scripts\api-test.bat
call scripts\logs-check.bat
echo Готово. Сохраните скриншот результата.

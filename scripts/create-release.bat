@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Создание релизного архива
if not exist release mkdir release
for /f "tokens=1-4 delims=/.: " %%a in ("%date%") do set TS=%%c%%b%%a
git archive --format=zip --prefix=medical_booking/ -o release\medical_booking_%TS%.zip HEAD
echo Архив создан: release\medical_booking_%TS%.zip

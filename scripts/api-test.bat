@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Проверка HTTP-маршрутов
for %%u in (/) do curl -s -o NUL -w "%%u -> %%{http_code}\n" http://localhost%%u
curl -s -o NUL -w "/accounts/login/ -> %%{http_code}\n" http://localhost/accounts/login/
curl -s -o NUL -w "/appointments/doctors/ -> %%{http_code}\n" http://localhost/appointments/doctors/
curl -s -o NUL -w "/no-such-page/ -> %%{http_code}\n" http://localhost/no-such-page/

@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Замер производительности
for /L %%%%i in (1,1,10) do curl -s -o NUL -w "%%{time_total}\n" http://localhost/
npx --yes lighthouse@12 http://localhost/ --only-categories=accessibility,best-practices,seo --output=html --output-path=reports/lighthouse_report.html --chrome-flags="--headless --no-sandbox" --quiet

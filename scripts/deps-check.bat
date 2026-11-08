@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo Проверка зависимостей (pip-audit)
docker run --rm -v "%cd%\requirements.txt:/req.txt:ro" python:3.12-slim sh -c "pip install -q pip-audit && pip-audit -r /req.txt"

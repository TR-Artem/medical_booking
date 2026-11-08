# RELEASE_NOTES.md

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

## Версия 0.2.0 — production/demo-стенд (этап 3 УП.03)

Дата: 08.11.2026
Ветка: `feature/up03-stage3-deploy`

### Что добавлено

- `docker-compose.prod.yml` — production-конфигурация: без `--reload`, без монтирования кода, открыт только порт 80 (Nginx), `restart: unless-stopped`, healthcheck для PostgreSQL.
- `.env.production.example` — шаблон production-настроек без секретов.
- `scripts/deploy.bat`, `restart.bat`, `check_deploy.bat` и цели Makefile `deploy`, `restart`, `check-deploy`.
- `docs/DEPLOYMENT.md`, `docs/DEMO_GUIDE.md`, `docs/RELEASE_NOTES.md`.

### Что исправлено

- `DEBUG` по умолчанию `False` (был `True`) — P-09.
- Настройка Celery `broker_connection_retry` заменена на `CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP` — P-08.
- Порты PostgreSQL и Redis больше не публикуются наружу в production — P-10.
- `.env.*` добавлены в `.gitignore`, кроме шаблонов `.env.example` и `.env.production.example`.

### Как запустить

```bash
cp .env.production.example .env.production   # заполнить секреты
make deploy
```

Открыть: http://localhost

### Как проверить

- `make check` — ruff, black и 37 тестов проходят.
- `make check-deploy` — все сервисы `running`, HTTP 200.
- Вход администратором работает.

### Известные ограничения

- Нет HTTPS.
- Учётные записи не создаются автоматически (P-15 открыт).
- Celery работает от root в контейнере (P-07, исправляется в этапе 5).
- Dockerfile не имеет healthcheck для web.

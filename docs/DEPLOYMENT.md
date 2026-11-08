# DEPLOYMENT.md

## 1. Где развернут проект

Вариант C: локальный demo-стенд через Docker (production-конфигурация).
Адрес: http://localhost (порт 80, через Nginx).

Причина выбора варианта: внешнего сервера и доменного имени у студента нет. Стенд поднимается тем же production-compose, что и на сервере, поэтому его можно перенести на VPS без изменений.

## 2. Требования

- ОС: macOS, Windows 10/11 или Linux.
- Docker Engine / Docker Desktop / OrbStack с Docker Compose v2.
- Свободный порт 80 на хосте.
- Порты БД и Redis наружу не публикуются.
- Переменные окружения: см. `.env.production.example` и `docs/CONFIGURATION.md`.

## 3. Команды развертывания

```bash
git clone https://github.com/TR-Artem/medical_booking.git
cd medical_booking
git checkout feature/up03-stage3-deploy
cp .env.production.example .env.production
# заполнить SECRET_KEY и DB_PASSWORD в .env.production
make deploy            # macOS / Linux
scripts\deploy.bat     # Windows
```

`make deploy` (`scripts/deploy.bat`) выполняет:

1. `docker compose -f docker-compose.prod.yml --env-file .env.production up --build -d`
2. `migrate` — применение миграций;
3. `collectstatic` — сборка статики в volume;
4. `ps` — вывод статуса сервисов.

Первичные данные и администратор (один раз):

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec web python manage.py loaddata fixtures/initial_data.json
docker compose -f docker-compose.prod.yml --env-file .env.production exec web python manage.py createsuperuser
```

## 4. Проверка

- Адрес приложения: http://localhost
- Проверка статуса и логов: `make check-deploy` / `scripts\check_deploy.bat`
- Ожидаемый результат: все сервисы `running`, `db` в статусе `healthy`, `HTTP 200`.
- Основной сценарий: открыть главную, перейти на вход, войти под администратором, увидеть приветствие.
- Логи: `docker compose -f docker-compose.prod.yml --env-file .env.production logs --tail=80` — без ошибок и traceback (см. `logs/deploy_log.txt`).

## 5. Остановка и перезапуск

```bash
make restart           # scripts\restart.bat
docker compose -f docker-compose.prod.yml --env-file .env.production down   # остановка без удаления данных
```

Данные PostgreSQL хранятся в volume `postgres_data`. `down` их не удаляет; `down -v` удалит.

Проверено: после `make restart` сайт отвечает HTTP 200, статика отдаётся, данные (1 пользователь, 6 специальностей) сохранились.

## 6. Что изменено относительно разработки

| Параметр | Разработка (`docker-compose.yml`) | Production (`docker-compose.prod.yml`) |
|---|---|---|
| Сервер приложения | `gunicorn --reload` | `gunicorn` без `--reload` |
| Код | монтируется `.:/app` | только из образа |
| Порты наружу | 80, 8000, 5432, 6379 | только 80 |
| Пароли | в файле (`postgres`) | из `.env.production` |
| `DEBUG` | `True` по умолчанию | `False` |
| Перезапуск | `restart: always` | `restart: unless-stopped` |
| Ожидание БД | нет | `healthcheck` и `condition: service_healthy` |

# Установка и запуск

Требования: Docker Desktop (или OrbStack) с Docker Compose v2.

## Быстрый старт (macOS / Linux)

```bash
make setup      # создать .env из .env.example и собрать образы
make run        # поднять контейнеры в фоне
make migrate    # применить миграции
docker compose exec web python manage.py loaddata fixtures/initial_data.json
```

Открыть: http://localhost:8000

## Быстрый старт (Windows)

Запускать из папки проекта:

```bat
scripts\setup.bat
scripts\run.bat
```

## Все команды

| Действие | Windows | Makefile | Docker |
|---|---|---|---|
| Установка | `scripts\setup.bat` | `make setup` | `docker compose build` |
| Запуск | `scripts\run.bat` | `make run` | `docker compose up --build -d` |
| Проверка (ruff, black, тесты) | `scripts\check.bat` | `make check` | `docker compose exec web sh -c "ruff check . && black --check . && python manage.py test"` |
| Форматирование | `scripts\format.bat` | `make format` | `docker compose exec web sh -c "ruff check --fix . && black ."` |
| Остановка | `scripts\docker-down.bat` | `make docker-down` | `docker compose down` |
| Логи | `scripts\logs.bat` | `make logs` | `docker compose logs -f` |

## Переменные окружения

Все настройки берутся из `.env`. Описание переменных — в `.env.example`.
Файл `.env` не попадает в git.

## Проверка

После запуска должны работать все сервисы:

```bash
docker compose ps
```

Сервисы `web`, `nginx`, `db`, `redis`, `celery`, `celery-beat` — в статусе `running`.

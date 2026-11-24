# Установка и запуск

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

Требования: Docker Desktop (или OrbStack) с Docker Compose v2.

## Быстрый старт (macOS / Linux)

```bash
make setup      # создать .env из .env.example и собрать образы
make run        # поднять контейнеры, применить миграции, собрать статику
make seed-dev   # пользователи, 5 врачей, пациент, расписание на 7 дней
```

Открыть: http://localhost:8080

Демо-доступы: `admin@test.ru`, `doctor@test.ru`, `patient@test.ru`, пароль `Test1234!`.

## Быстрый старт (Windows)

Запускать из папки проекта:

```bat
scripts\setup.bat
scripts\run.bat
docker compose exec web python manage.py seed_demo
```

## Production-стенд

```bash
cp .env.production.example .env.production
make deploy
make seed
```

Открыть: http://localhost. Подробности и VPS с HTTPS — в [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Все команды

| Действие | Windows | Makefile | Docker |
|---|---|---|---|
| Установка | `scripts\setup.bat` | `make setup` | `docker compose build` |
| Запуск | `scripts\run.bat` | `make run` | `docker compose up --build -d` |
| Демо-данные (dev) | — | `make seed-dev` | `docker compose exec web python manage.py seed_demo` |
| Проверка (ruff, black, тесты) | `scripts\check.bat` | `make check` | `docker compose exec web sh -c "ruff check . && black --check . && python manage.py test"` |
| Форматирование | `scripts\format.bat` | `make format` | `docker compose exec web sh -c "ruff check --fix . && black ."` |
| Остановка | `scripts\docker-down.bat` | `make docker-down` | `docker compose down` |
| Логи | `scripts\logs.bat` | `make logs` | `docker compose logs -f` |

## Переменные окружения

Все настройки берутся из `.env`. Описание переменных — в `.env.example` и [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
Файл `.env` не попадает в git.

## Проверка

После запуска должны работать все сервисы:

```bash
docker compose ps
```

Сервисы `web`, `nginx`, `db`, `redis`, `celery`, `celery-beat` — в статусе `running`.

Приложение: http://localhost:8080, вход: http://localhost:8080/accounts/login/.

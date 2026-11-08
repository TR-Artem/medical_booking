# Входной аудит проекта (УП.03, этап 1)

Проект: «Онлайн-запись пациентов в медицинский центр»
Репозиторий: https://github.com/TR-Artem/medical_booking
Ветка: `feature/up03-stage2-install`
Дата аудита: 08.11.2026

## 1. Паспорт проекта

| Поле | Значение |
|---|---|
| Что делает программа | Позволяет пациенту записаться на приём к врачу через интернет, врачу — видеть своё расписание и отмечать явку, администратору — управлять расписанием и пользователями |
| Для кого | Пациент, врач, администратор, системный администратор (4 роли) |
| Что было сделано в УП.02 | ТЗ, UML-диаграмма классов, модули Accounts / Appointments / Notifications / Core, 37 модульных тестов |
| Стек | Python 3.12, Django 5.0.4, Django REST Framework 3.15.1, PostgreSQL 16, Redis 6.1 + Celery 5.3.6, Gunicorn, Nginx, Docker Compose, Bootstrap 5 |
| Текущее состояние | **Запускается полностью** через Docker Compose после исправлений этапа 2 |
| Главная проблема на входе | Не было инструкции запуска, `static/` не попадал в репозиторий, Celery-воркер падал из-за версии Redis, в образ попадал бы `.env` |

## 2. Что было сделано в этапе 2 (до аудита)

- добавлены `.dockerignore`, `static/css/main.css`, `static/js/main.js`;
- исправлен `requirements.txt`: `redis==5.0.4` → `redis==6.1.0`;
- код приведён к стандарту: `ruff` (27 исправлений), `black` (26 файлов);
- добавлены `Makefile`, `scripts/*.bat`, `INSTALL.md`, `pyproject.toml`, `.editorconfig`.

## 3. Проверка состава проекта

| Файл / папка | Что должно быть | Что есть сейчас | Что сделать |
|---|---|---|---|
| `README.md` | Описание и запуск | Есть, но структура проекта не совпадает с репозиторием (указаны несуществующие `appointments/forms.py`, `templates/doctor/schedule.html`), не описаны `celery.py`, `notifications/tasks.py` | Исправить структуру, добавить ссылки на `INSTALL.md` и `docs/` |
| `requirements.txt` | Список зависимостей | Есть, версии закреплены. `sendgrid` указан, но в коде не используется (отправка через SMTP) | Удалить `sendgrid` или описать использование |
| `.env.example` | Пример настроек без секретов | Есть, значения-заглушки. `DEBUG=True` и `SECRET_KEY=your-secret-key-here...` по умолчанию | Оставить как dev-пример, для prod добавить `.env.production.example` (этап 3) |
| `Dockerfile` | Сборка образа | Есть. `.dockerignore` добавлен | Оставлено |
| `docker-compose.yml` | Запуск сервисов | Есть: db, redis, web, celery, celery-beat, nginx | В dev-режиме: `--reload`, монтирование кода, пароль `postgres`, порты БД и Redis открыты наружу — переделать в этапе 3 |
| `nginx.conf` | Прокси | Есть, проксирует на `web:8000`, отдаёт `/static/` | Оставлено |
| `manage.py`, `medical_booking/` | Настройки Django | Есть. `DEBUG` по умолчанию `True`, `SECRET_KEY` по умолчанию небезопасный | Переделать в этапе 5 |
| `apps/` | Модули | Есть 4 приложения: accounts, appointments, notifications, core | Оставлено |
| `apps/*/tests/` | Тесты | 37 тестов в `tests/__init__.py`, Django их находит, все проходят | Вынести в `test_*.py` для стандартной структуры (по желанию) |
| `migrations/` | Миграции | Есть для accounts и appointments, для notifications нет (не нужны — нет своих моделей) | Оставлено |
| `templates/` | Шаблоны | Есть, используют `static/css/main.css` и `static/js/main.js` | Оставлено |
| `static/` | Статика | Была отсутствующей и игнорировалась `.gitignore`. Исправлено | Оставлено |
| `fixtures/initial_data.json` | Тестовые данные | Есть, 10 объектов, загружается командой `loaddata` | Оставлено |
| `docs/` | Документация | Отсутствовала | Создана в этапе 1 |
| `Makefile`, `scripts/` | Команды запуска | Добавлены в этапе 2 | Оставлено |
| `.github/workflows/` | CI | Отсутствует | Этап 6 |

## 4. Зависимости и версии

| Зависимость | Версия | Команда проверки | Для чего |
|---|---|---|---|
| Python | 3.12.16 (в образе) | `python --version` | Backend |
| Django | 5.0.4 | `python -c "import django;print(django.__version__)"` | Фреймворк |
| Django REST Framework | 3.15.1 | — | API |
| PostgreSQL | 16.15 (образ `postgres:16-alpine`) | `docker compose exec db postgres --version` | Основная БД |
| Redis | 7 (образ), клиент 6.1.0 | `docker compose exec redis redis-server --version` | Очередь Celery |
| Celery | 5.3.6 | — | Отправка писем и напоминаний |
| Gunicorn | 22.0.0 | — | WSGI-сервер |
| Nginx | alpine (образ) | — | Прокси и статика |
| Docker | 29.8.2 (OrbStack) | `docker --version` | Контейнеры |
| Docker Compose | v5.5.0 | `docker compose version` | Оркестрация |

Установка: `make setup` (или `scripts\setup.bat` на Windows). Проверено: установка из чистого клона проходит без ошибок.

## 5. Результат запуска

Проверено из чистого клона в новой папке (см. `logs/app_start_log.txt`):

- `make setup` — образы собраны;
- `make run` — все 6 сервисов в статусе `running`;
- миграции применены, фикстура загружена;
- `make check` — ruff, black и 37 тестов пройдены;
- `http://localhost:8000` → HTTP 200.

## 6. Предупреждения из логов

- `SecurityWarning: You're running the worker with superuser privileges` — Celery запущен от root в контейнере. Исправить: отдельный пользователь в Dockerfile (этап 5).
- `CPendingDeprecationWarning: broker_connection_retry` — настройка Celery устарела. Исправить в `settings.py` (этап 3).

## 7. Журнал проблем

| ID | Проблема | Как проявляется | Причина | Что сделать | Статус |
|---|---|---|---|---|---|
| P-01 | Celery-воркер не запускается | `kombu.exceptions.VersionMismatch: Redis transport requires redis-py 6.1.0 or later` | `redis==5.0.4` несовместим с kombu | Обновлено до `redis==6.1.0` | Исправлено |
| P-02 | Страница без стилей и скриптов при `DEBUG=False` | `{% static 'css/main.css' %}` не находит файл | Папка `static/` не закоммичена, `.gitignore` её игнорировал | Созданы файлы, убрано из `.gitignore` | Исправлено |
| P-03 | В Docker-образ попал бы `.env` с секретами | `COPY . .` без `.dockerignore` | Нет `.dockerignore` | Добавлен `.dockerignore` | Исправлено |
| P-04 | Ошибка сборки статики скрыта | `collectstatic ... \|\| true` | Ошибка не видна | Убрано `\|\| true` | Исправлено |
| P-05 | Нет инструкции запуска | Другой человек не знает команды | README не описывал запуск | Добавлен `INSTALL.md`, `Makefile`, `scripts/` | Исправлено |
| P-06 | Нет линтера и форматтера | Код не единообразен | Не настроены инструменты | Добавлены ruff и black, код отформатирован | Исправлено |
| P-07 | Celery запущен от root | `SecurityWarning` в логах | Образ не создаёт отдельного пользователя | Создать пользователя в Dockerfile | Открыто, этап 5 |
| P-08 | Устаревшая настройка Celery | `CPendingDeprecationWarning` | `broker_connection_retry` | Заменить настройку | Открыто, этап 3 |
| P-09 | `DEBUG=True` и небезопасный `SECRET_KEY` по умолчанию | Значения в `settings.py` | Настройки для разработки | Перевести на production-значения в `.env.production.example` | Открыто, этап 3 |
| P-10 | Dev-режим в `docker-compose.yml` | `--reload`, `.:/app`, пароль `postgres`, открыты порты 5432 и 6379 | Compose сделан для разработки | Создать `docker-compose.prod.yml` | Открыто, этап 3 |
| P-11 | README не совпадает с проектом | Упомянуты несуществующие файлы | README писался до изменений | Исправить структуру | Открыто |
| P-12 | В README тестовые пароли | `Test1234!` для трёх ролей | Для демо нормально, для эксплуатации — риск | Пометить как «только для демо», сменить в prod | Открыто, этап 5 |
| P-15 | Тестовые учётки из README не существуют | В чистой базе 0 пользователей; фикстура содержит только специальности и кабинеты | Пользователи не добавлены в фикстуру | Добавить пользователей в фикстуру или команду создания демо-данных; до этого — `createsuperuser` (см. CONFIGURATION.md) | Открыто |
| P-13 | Лишняя зависимость | `sendgrid` в requirements, не используется | Осталось после выбора SMTP | Удалить | Открыто |
| P-14 | Неясная история коммитов | Сообщения «mail», «ридми», «dictorFix», «proj» | Не было соглашения | Использовать осмысленные сообщения и PR | Открыто, этап 6 |

## 8. Задачи на следующие этапы

1. Этап 3: `docker-compose.prod.yml`, `.env.production.example`, `DEPLOYMENT.md`, исправить P-08, P-09, P-10.
2. Этап 4: тест-план, проверка API (Swagger, curl), Lighthouse, дефекты (P-01 уже есть как образец).
3. Этап 5: пользователь без root для Celery, проверка доступа к чужим записям, backup/restore PostgreSQL, `SECURITY_CHECKLIST.md`.
4. Этап 6: issue, PR, `ci.yml`, `CHANGELOG.md`, `RELEASE_NOTES.md`.

## 9. Вывод о готовности

Проект **запускается полностью** через Docker Compose и проходит тесты и проверки качества кода. Для эксплуатации он **не готов**: есть dev-настройки в compose и settings (P-08, P-09, P-10), не описано развёртывание, не проверены безопасность и восстановление данных. Эти пункты закрываются в этапах 3–5.

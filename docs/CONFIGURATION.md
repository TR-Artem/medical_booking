# Конфигурация проекта

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

Все переменные читаются из `.env` (шаблон — `.env.example`). Файл `.env` в git не попадает.

## 1. Переменные окружения

| Переменная | Пример | Назначение | Обязательна | Комментарий |
|---|---|---|---|---|
| `SECRET_KEY` | `change_me_in_real_project` | Секретный ключ Django | Да | Для эксплуатации — длинная случайная строка, не из git |
| `DEBUG` | `True` | Режим отладки | Нет | Для эксплуатации `False` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Разрешённые имена хоста | Нет | Для эксплуатации добавить домен |
| `CSRF_TRUSTED_ORIGINS` | `https://clinic.example.ru` | Доверенные origin для CSRF | Нет | Обязательно для HTTPS-домена, со схемой |
| `DB_NAME` | `medical_db` | Имя базы PostgreSQL | Да | |
| `DB_USER` | `postgres` | Пользователь БД | Да | |
| `DB_PASSWORD` | `postgres` | Пароль БД | Да | Для эксплуатации — свой пароль |
| `DB_HOST` | `db` | Хост БД | Да | В Docker — имя сервиса `db` |
| `DB_PORT` | `5432` | Порт БД | Нет | |
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP-сервер | Нет | Для тестов можно Mailpit |
| `EMAIL_PORT` | `587` | Порт SMTP | Нет | |
| `EMAIL_USE_TLS` | `True` | Шифрование SMTP | Нет | |
| `EMAIL_HOST_USER` | `your-email@gmail.com` | Логин SMTP | Нет | |
| `EMAIL_HOST_PASSWORD` | `your-app-password` | Пароль SMTP | Нет | Секрет, только в `.env` |
| `DEFAULT_FROM_EMAIL` | `МедЦентр <noreply@medcenter.ru>` | Адрес отправителя | Нет | |
| `REDIS_URL` | `redis://redis:6379/0` | Брокер Celery | Да | В Docker — сервис `redis` |
| `SITE_URL` | `http://localhost:8000` | Адрес сайта для ссылок в письмах | Нет | |
| `SESSION_COOKIE_SECURE` | `False` | Cookie сессии только по HTTPS | Нет | `True` на HTTPS-стенде |
| `CSRF_COOKIE_SECURE` | `False` | CSRF-cookie только по HTTPS | Нет | `True` на HTTPS-стенде |
| `SECURE_SSL_REDIRECT` | `False` | Редирект HTTP→HTTPS | Нет | `True` за Nginx с TLS |
| `SECURE_HSTS_SECONDS` | `0` | HSTS, секунды | Нет | `31536000` на HTTPS-стенде |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `False` | HSTS для поддоменов | Нет | |
| `SECURE_HSTS_PRELOAD` | `False` | HSTS preload | Нет | |

Примечание: `DEBUG` по умолчанию `False`, `ALLOWED_HOSTS` — только `localhost,127.0.0.1`.
Для HTTPS Django доверяет заголовку `X-Forwarded-Proto` от Nginx (`SECURE_PROXY_SSL_HEADER`), поэтому редиректа-петли нет.

## 2. Порты

| Сервис | Порт на хосте | Порт в контейнере | Назначение | Открыт наружу |
|---|---|---|---|---|
| nginx | 80 | 80 | Вход на сайт | Да (для демо) |
| nginx (HTTPS) | 443 | 443 | Вход на сайт по HTTPS | Да (VPS) |
| web (gunicorn) | 8000 | 8000 | Django напрямую | Да (dev) |
| db (PostgreSQL) | 5432 | 5432 | База данных | Да (dev, в prod закрыть) |
| redis | 6379 | 6379 | Очередь Celery | Да (dev, в prod закрыть) |

## 3. Зависимости и команды

| Зависимость | Версия | Команда |
|---|---|---|
| Python | 3.12 | `python --version` |
| Docker + Compose | 24+ / v2 | `docker compose version` |
| Все Python-пакеты | см. `requirements.txt` | `make setup` |

| Действие | Команда |
|---|---|
| Установка | `make setup` / `scripts\setup.bat` |
| Запуск | `make run` / `scripts\run.bat` |
| Миграции | `make migrate` |
| Тестовые данные | `make seed-dev` / `python manage.py seed_demo` |
| HTTPS на VPS | `DOMAIN=... EMAIL=... bash deploy/setup-vps.sh` |
| Проверка качества | `make check` / `scripts\check.bat` |
| Остановка | `make docker-down` / `scripts\docker-down.bat` |

## 4. Учётные записи

Фикстура `initial_data.json` содержит только специальности и кабинеты, пользователей в ней нет.
Демо-учётные записи и данные создаются командой `seed_demo`:

```bash
make seed      # production
make seed-dev  # разработка
```

Создаются администратор (`admin@test.ru`), 5 врачей (`doctor@test.ru` … `doctor5@test.ru`), пациент (`patient@test.ru`), расписание на 7 дней и 3 записи. Пароль по умолчанию `Test1234!`, меняется через `--password`. Команда идемпотентна и сбрасывает пароли демо-учёток при каждом запуске.

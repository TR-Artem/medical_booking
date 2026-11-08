# Конфигурация проекта

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

Все переменные читаются из `.env` (шаблон — `.env.example`). Файл `.env` в git не попадает.

## 1. Переменные окружения

| Переменная | Пример | Назначение | Обязательна | Комментарий |
|---|---|---|---|---|
| `SECRET_KEY` | `change_me_in_real_project` | Секретный ключ Django | Да | Для эксплуатации — длинная случайная строка, не из git |
| `DEBUG` | `True` | Режим отладки | Нет | Для эксплуатации `False` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Разрешённые имена хоста | Нет | Для эксплуатации добавить домен |
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

Примечание: в `settings.py` `DEBUG` по умолчанию `True`, `SECRET_KEY` — небезопасная заглушка. Это исправляется в этапе 3.

## 2. Порты

| Сервис | Порт на хосте | Порт в контейнере | Назначение | Открыт наружу |
|---|---|---|---|---|
| nginx | 80 | 80 | Вход на сайт | Да (для демо) |
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
| Тестовые данные | `docker compose exec web python manage.py loaddata fixtures/initial_data.json` |
| Проверка качества | `make check` / `scripts\check.bat` |
| Остановка | `make docker-down` / `scripts\docker-down.bat` |

## 4. Учётные записи

Фикстура `initial_data.json` содержит только специальности и кабинеты, пользователей в ней нет.
Демо-учётные записи и данные создаются командой:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec web python manage.py create_demo_data
```

Команда создаёт 7 пользователей (admin, sysadmin, 3 врача, 2 пациента), профили врачей, расписание на 5 рабочих дней и одну запись. Пароль по умолчанию `Demo1234!` — только для локального демо-стенда, менять через `--password`.

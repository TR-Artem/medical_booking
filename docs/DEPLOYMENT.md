# DEPLOYMENT.md

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

## 1. Варианты развёртывания

| Вариант | Адрес | Назначение |
|---|---|---|
| Разработка | http://localhost:8080 | код монтируется, `gunicorn --reload` |
| Production локально | http://localhost | образ без монтирования, Nginx, только 80-й порт |
| VPS + HTTPS | https://домен | `deploy/setup-vps.sh`, Let's Encrypt, 80/443 |

## 2. Production локально

Требования: Docker Desktop / OrbStack, Docker Compose v2, свободный порт 80.

```bash
cp .env.production.example .env.production
# заполнить SECRET_KEY и DB_PASSWORD (остальное можно оставить для демо)

make deploy
make seed
```

`make deploy`:

1. собирает образы и поднимает `db`, `redis`, `mailpit`, `web`, `celery`, `celery-beat`, `nginx`;
2. применяет миграции;
3. выставляет владельца volume статики и выполняет `collectstatic`;
4. перезапускает `web` и `nginx`;
5. печатает статус сервисов.

Проверка:

```bash
make check-deploy
make health
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost/
```

Ожидается: все сервисы `running`, `db` — `healthy`, HTTP 200, `/healthz/` — `status: ok`.
Письма демо-стенда: http://127.0.0.1:8025 (Mailpit).

## 3. VPS с HTTPS

Требования:

- Ubuntu/Debian, root или пользователь с sudo;
- A-запись домена указывает на IP сервера;
- порты 80 и 443 свободны;
- установленный `git` и `curl`.

Запуск одной командой:

```bash
DOMAIN=clinic.example.ru EMAIL=admin@example.ru bash deploy/setup-vps.sh
```

Скрипт:

1. устанавливает Docker, если его нет;
2. включает UFW (22/80/443), fail2ban и unattended-upgrades (`HARDEN=0` отключает);
3. клонирует `main` в `/opt/medical_booking` (или обновляет существующий клон);
4. создаёт `.env.production` со случайными `SECRET_KEY` и `DB_PASSWORD`, доменом, HTTPS-флагами;
5. выпускает сертификат Let's Encrypt (standalone, 80-й порт);
6. рендерит `deploy/nginx-https.conf` из шаблона;
7. поднимает production-стек с HTTPS-оверрайдом;
8. применяет миграции, собирает статику, запускает `seed_demo` (`SEED_DEMO=0` отключает);
9. добавляет cron: перезагрузка Nginx после продления сертификата и ежедневный бэкап БД.

Проверка:

```bash
curl -I https://clinic.example.ru/
docker compose -f docker-compose.prod.yml -f deploy/docker-compose.https.yml \
  --env-file .env.production ps
```

Открыть `https://clinic.example.ru/`, войти под `admin@test.ru / Test1234!`.

### HTTPS вручную

Если сертификат уже выпущен:

```bash
make deploy-https
```

`deploy/docker-compose.https.yml` публикует 80/443, монтирует сертификаты и запускает контейнер `certbot` для продления (`webroot`, каждые 12 часов). Nginx перезагружается по cron раз в неделю.

### Обязательные переменные для HTTPS

```dotenv
ALLOWED_HOSTS=clinic.example.ru
CSRF_TRUSTED_ORIGINS=https://clinic.example.ru
SITE_URL=https://clinic.example.ru
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
```

`SECURE_PROXY_SSL_HEADER` уже настроен в `settings.py`: Django доверяет `X-Forwarded-Proto` от Nginx и не уходит в редирект-петлю.

## 4. Демо-данные

```bash
make seed     # production-стек
make seed-dev # dev-стек
```

Создаются администратор клиники, системный администратор, 5 врачей, пациент,
расписание на 7 дней и 3 записи. Пароль — `Test1234!`. Команда идемпотентна,
пароли демо-учёток сбрасываются.

## 5. Остановка и данные

```bash
make docker-down                     # остановить без удаления данных
make restart                         # перезапустить production
```

PostgreSQL хранится в volume `postgres_data`. `down` данные не удаляет, `down -v` — удаляет.

## 6. Бэкап и восстановление

```bash
make backup                                   # deploy/backup.sh, gzip + ротация 14 дней
make restore BACKUP=backups/backup_20261125_031500.sql.gz
```

`backup.sh` можно запускать вручную и из cron; переменные `BACKUP_DIR`,
`BACKUP_RETENTION_DAYS`. Восстановление идёт в отдельную БД `medical_restore_test`,
production-база не затрагивается.

## 7. Мониторинг и логи

- `GET /healthz/` — 200 и JSON `{"status":"ok","db":true,"version":"..."}`;
  при недоступной БД — 503.
- Внешний uptime-чек настраивается на `/healthz/` (UptimeRobot и аналоги).
- Docker-логи ограничены: 10 МБ × 3 файла на сервис.
- Приложение пишет события входа, бронирования, отмены и ошибки SMTP в stdout;
  смотрите `docker compose logs web celery celery-beat`.

## 7. Отличия dev и prod

| Параметр | Разработка | Production |
|---|---|---|
| Сервер | `gunicorn --reload` | `gunicorn` без reload |
| Код | монтируется `.:/app` | только из образа |
| Порты | 80 (nginx), 8000, 5432, 6379 | 80 (и 443 при HTTPS) |
| Пароли | в compose | из `.env.production` |
| `DEBUG` | `True` | `False` |
| Перезапуск | `always` | `unless-stopped` |
| Ожидание БД | нет | healthcheck |
| HTTPS | нет | Let's Encrypt + Nginx |

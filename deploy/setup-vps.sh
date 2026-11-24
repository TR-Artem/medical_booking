#!/usr/bin/env bash
# Развёртывание демо-стенда «МедЦентр» на чистом Ubuntu/Debian VPS с HTTPS.
#
# Требования:
#   * A-запись домена уже указывает на IP сервера;
#   * порты 80 и 443 свободны;
#   * запуск от root (или пользователя с sudo).
#
# Пример:
#   DOMAIN=clinic.example.ru EMAIL=admin@example.ru bash deploy/setup-vps.sh
#
# Скрипт идемпотентен: повторный запуск обновляет код и перезапускает стек,
# существующие .env.production и сертификат не перезаписываются.

set -euo pipefail

: "${DOMAIN:?Укажите домен: DOMAIN=clinic.example.ru}"
: "${EMAIL:?Укажите e-mail для Let's Encrypt: EMAIL=admin@example.ru}"

APP_DIR="${APP_DIR:-/opt/medical_booking}"
REPO="${REPO:-https://github.com/TR-Artem/medical_booking.git}"
BRANCH="${BRANCH:-main}"
CERT_VOLUME="medical_booking_certbot_conf"
WEBROOT_VOLUME="medical_booking_certbot_www"

COMPOSE=(docker compose -f docker-compose.prod.yml -f deploy/docker-compose.https.yml --env-file .env.production)
CRON_MARKER="medical_booking-cert-reload"

log() { printf '\n==> %s\n' "$*"; }

log "Проверка Docker"
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker >/dev/null 2>&1 || true

log "Код проекта: $APP_DIR ($BRANCH)"
if [ ! -d "$APP_DIR/.git" ]; then
    mkdir -p "$(dirname "$APP_DIR")"
    git clone --branch "$BRANCH" "$REPO" "$APP_DIR"
else
    git -C "$APP_DIR" fetch origin "$BRANCH"
    git -C "$APP_DIR" checkout "$BRANCH"
    git -C "$APP_DIR" pull --ff-only
fi
cd "$APP_DIR"

if [ ! -f .env.production ]; then
    log "Создание .env.production"
    SECRET_KEY="$(openssl rand -hex 32)"
    DB_PASSWORD="$(openssl rand -hex 16)"
    cat > .env.production <<EOF
# Сгенерировано deploy/setup-vps.sh. Не коммитить.
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${DOMAIN}
CSRF_TRUSTED_ORIGINS=https://${DOMAIN}

DB_NAME=medical_db
DB_USER=medical_user
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=db
DB_PORT=5432

EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=МедЦентр <noreply@${DOMAIN}>

REDIS_URL=redis://redis:6379/0

SITE_URL=https://${DOMAIN}
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
EOF
    chmod 600 .env.production
else
    log ".env.production уже существует — оставляю без изменений"
fi

log "Сертификат Let's Encrypt"
docker volume create "$CERT_VOLUME" >/dev/null
docker volume create "$WEBROOT_VOLUME" >/dev/null
if docker run --rm -v "${CERT_VOLUME}:/etc/letsencrypt" alpine:3 \
    test -d "/etc/letsencrypt/live/${DOMAIN}"; then
    echo "Сертификат для ${DOMAIN} уже выпущен"
else
    # Certbot standalone требует свободный 80-й порт: сначала останавливаем стек.
    "${COMPOSE[@]}" down >/dev/null 2>&1 || true
    docker run --rm \
        -p 80:80 \
        -v "${CERT_VOLUME}:/etc/letsencrypt" \
        -v "${WEBROOT_VOLUME}:/var/www/certbot" \
        certbot/certbot:latest \
        certonly --standalone --non-interactive --agree-tos \
        --email "$EMAIL" -d "$DOMAIN"
fi

log "Рендер конфигурации Nginx"
sed "s/__DOMAIN__/${DOMAIN}/g" deploy/nginx-https.conf.template > deploy/nginx-https.conf

log "Сборка и запуск"
"${COMPOSE[@]}" up --build -d
"${COMPOSE[@]}" exec -T web python manage.py migrate --noinput
"${COMPOSE[@]}" exec -T -u root web chown -R app:app /app/staticfiles
"${COMPOSE[@]}" exec -T web python manage.py collectstatic --noinput --clear
"${COMPOSE[@]}" exec -T web python manage.py seed_demo
"${COMPOSE[@]}" exec -T web python manage.py check --deploy
"${COMPOSE[@]}" restart nginx

log "Проверка"
curl -fsS -o /dev/null -w "https://${DOMAIN} -> HTTP %{http_code}\n" "https://${DOMAIN}/"

log "Cron: перезагрузка Nginx после продления сертификата"
CRON_LINE="0 4 * * 1 cd ${APP_DIR} && ${COMPOSE[*]} exec -T nginx nginx -s reload >/dev/null 2>&1 # ${CRON_MARKER}"
{ crontab -l 2>/dev/null | grep -v "$CRON_MARKER" || true; echo "$CRON_LINE"; } | crontab -

log "Готово. Демо-стенд: https://${DOMAIN}"
echo "Логины: admin@test.ru / doctor@test.ru / patient@test.ru, пароль Test1234!"
echo "Файл настроек: ${APP_DIR}/.env.production"

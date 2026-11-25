# CHANGELOG.md

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

Все заметные изменения проекта. Формат основан на Keep a Changelog, версии — SemVer.

## [0.4.0] — 2026-11-25

### Added

- Вход по логину или e-mail без учёта регистра (`EmailOrUsernameBackend`).
- Сброс пароля по e-mail и смена пароля в профиле.
- Rate limit входа: 5 попыток на логин+IP и 20 на IP за 15 минут (Redis).
- Асинхронная отправка писем через Celery с повторами и `EMAIL_TIMEOUT`.
- Mailpit в dev/prod-стеке: демо-письма видны на `http://localhost:8025`.
- Периодическая задача напоминаний за 24 часа создаётся миграцией.
- Демо-учётка системного администратора `sysadmin@test.ru`; Django admin
  больше не доступен администратору клиники.
- `/healthz/` — health-check приложения и БД для мониторинга.
- `deploy/backup.sh` — бэкап с gzip и ротацией, cron на VPS; hardening
  `setup-vps.sh`: UFW, fail2ban, unattended-upgrades.
- Проверка конфликта кабинета и времени при создании расписания.
- Поиск и пагинация врачей, пагинация пользователей.
- Статус «Подтверждено»: подтверждение записи врачом и отображение во всех кабинетах.
- Страница политики ПДн `/privacy/` и ссылки в регистрации/подвале.
- Свои страницы 404 и 500.
- Playwright E2E-тест сценария «запись → отмена → повторная запись» и ролей.
- CI: Redis, E2E-задача, smoke-сборка production-стека в Docker.
- Ограничение размера Docker-логов (10 МБ × 3).

### Changed

- Генерация слотов вынесена из модели `Schedule` в `apps/appointments/services.py`.
- `seed_demo` не создаёт записи в прошлом и печатает сисадмина.
- README, INSTALL, DEMO_GUIDE, DEPLOYMENT, CONFIGURATION, SECURITY обновлены.

### Removed

- Неиспользуемые зависимости `djangorestframework`, `djangorestframework-simplejwt`,
  `django-cors-headers`, `sendgrid` и настройки DRF/JWT/CORS.

### Fixed

- Напоминания учитывают часовой пояс клиники и статус `confirmed`.
- Письма не отправляются при откате транзакции бронирования.

## [0.3.1] — 2026-11-25

### Fixed

- После отмены записи слот снова доступен для бронирования. `Appointment.slot`
  стал `ForeignKey`, добавлен частичный уникальный индекс
  `unique_active_appointment_per_slot` (миграция `appointments.0002`):
  на слот может быть только одна активная запись, отменённые остаются в истории.
- Нельзя записаться на слот, который уже начался: `TimeSlot.is_available`
  сравнивает время приёма с текущим в часовом поясе клиники, а список слотов
  скрывает прошедшие сегодняшние слоты.
- `TimeSlot` больше не использует `date.today()` (UTC контейнера): дата и время
  считаются через `timezone.localdate()` / `timezone.now()` в `Europe/Moscow`.
- `seed_demo` создаёт демо-записи только на будущие слоты: поздно вечером
  запись переносится на ближайший свободный день, а не остаётся в прошлом.
- Добавлены регрессионные тесты бронирования, отмены и повторной записи
  (58 тестов всего).

## [0.3.0] — 2026-11-24

### Added

- Команда `seed_demo`: администратор, 5 врачей, пациент, 6 специальностей, 6 кабинетов,
  расписание на 7 дней и 3 демо-записи. Идемпотентна, поддерживает `--days`,
  `--password`, `--without-appointments`, `--keep-legacy`.
- Скриншоты интерфейса в `docs/screenshots/` и галерея в README.
- Деплой на VPS с HTTPS: `deploy/setup-vps.sh`, `deploy/docker-compose.https.yml`,
  `deploy/nginx-https.conf.template`, продление Let's Encrypt, cron-перезагрузка Nginx.
- Makefile: `seed`, `seed-dev`, `deploy-https`.
- Тесты `seed_demo` (51 тест всего).
- Переменные HTTPS: `CSRF_TRUSTED_ORIGINS`, `SECURE_PROXY_SSL_HEADER`, HSTS, secure cookies.

### Changed

- README переписан под фактическое состояние: запуск, демо-доступы, seed_demo,
  production, VPS/HTTPS, структура, ограничения.
- INSTALL.md, docs/DEPLOYMENT.md, docs/DEMO_GUIDE.md, docs/CONFIGURATION.md обновлены.
- `seed_demo` удаляет старые демо-учётки `@medcenter.local` от `create_demo_data`,
  чтобы в списке врачей не было дублей.
- Команда `create_demo_data` удалена: её заменяет `seed_demo`.

### Fixed

- `collectstatic --clear` больше не падает с PermissionError на volume статики,
  созданном старым образом: Makefile выставляет владельца перед сборкой статики.
- «Сегодня» в кабинетах врача и администратора считается по часовому поясу
  `Europe/Moscow` (`timezone.localdate()`), а не по UTC: после 21:00 МСК
  расписание больше не сдвигается на предыдущий день.

## [0.2.0] — 2026-11-08

### Added

- GitHub Actions CI: линтер, форматтер, `manage.py check --deploy`, миграции, 44 теста, pip-audit.
- Шаблон страницы 403 и функция `access_denied`.
- Скрипты релиза: `scripts/build.bat`, `release-check.bat`, `create-release.bat`, цели `make build`, `make release`.
- Документы поддержки: `INCIDENT_REPORT.md`, `RELEASE_CHECKLIST.md`, `SUPPORT_REPORT.md`.

### Changed

- Закрытые разделы (панель администратора, кабинет врача, управление пользователями) отдают **403** с понятной страницей вместо редиректа на главную.
- Тесты дополнены проверками прав доступа (44 теста вместо 37).

### Fixed

- BUG-12: редирект 302 на главную скрывал причину отказа доступа.

### Security

- Django 5.2.19, Pillow 13.0.0, DRF 3.18.3, simplejwt 5.5.1.
- Контейнеры работают от пользователя `app` (uid 100).

### Verified

- Локально: `make check` — ruff, black, 44 теста.
- CI: workflow `CI` (`.github/workflows/ci.yml`).
- Релизный архив: `release/medical_booking_20261108.zip`.

## [0.1.0] — 2026-04-22

### Added

- Первая версия системы онлайн-записи: роли, расписание, слоты, бронирование, уведомления, Docker Compose.

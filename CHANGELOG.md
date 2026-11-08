# CHANGELOG.md

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

Все заметные изменения проекта. Формат основан на Keep a Changelog, версии — SemVer.

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

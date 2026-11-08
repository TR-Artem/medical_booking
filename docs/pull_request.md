# Что изменено

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

- Добавлена функция `access_denied()`: закрытые разделы отдают HTTP 403 и страницу `templates/403.html` вместо редиректа на главную.
- Проверки прав применены в `admin_required`, `doctor_required`, `sysadmin_required` и `doctor_dashboard`.
- Добавлены тесты `apps/appointments/tests/test_access.py` (7 проверок: роли и доступ к чужой записи).
- Настроен GitHub Actions: ruff, black, `manage.py check --deploy`, миграции, тесты, pip-audit.
- Добавлены CHANGELOG, RELEASE_NOTES, INCIDENT_REPORT, RELEASE_CHECKLIST, SUPPORT_REPORT, скрипты релиза.

# Связанный issue

Closes #<номер issue>

# Как проверено

- `ruff check .` — без замечаний.
- `black --check .` — без изменений.
- `python manage.py test` — 44 теста проходят.
- Ручная проверка: пациент → 403, сисадмин → 200.
- CI: workflow `CI` завершился успешно.

# Скриншоты

`screenshots/05_fix_commit.png`, `screenshots/06_tests_passed_locally.png`, `screenshots/07_github_actions_success.png`.

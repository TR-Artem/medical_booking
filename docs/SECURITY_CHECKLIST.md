# SECURITY_CHECKLIST.md

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

| Проверка | Статус | Доказательство | Что исправлено |
|---|---|---|---|
| `.env` не загружен в Git | выполнено | `screenshots/01_gitignore_no_env.png` | в индексе только `.env.example` и `.env.production.example` |
| `.env.example` без реальных секретов | выполнено | `screenshots/02_env_example_without_secrets.png` | значения заменены на `change_me` |
| Ручной поиск секретов выполнен | выполнено | `screenshots/03_secret_scan_result.png` | найдены только заглушки и тестовые пароли |
| Зависимости проверены | выполнено | `screenshots/04_dependency_check_result.png` | обновлены Django, Pillow, DRF, simplejwt, celery-beat; pip-audit: 0 уязвимостей |
| Проверены роли | выполнено | `screenshots/05_roles_access_check.png` | пациент → админ-раздел 302 |
| Проверен доступ к чужим данным | выполнено | `screenshots/06_foreign_data_access_denied.png` | отмена чужой записи → 404 |
| CORS/hosts/debug проверены | выполнено | `screenshots/07_cors_or_security_config.png` | `DEBUG=False`, CORS по списку, security-заголовки |
| Контейнеры не от root | выполнено | `screenshots/07_cors_or_security_config.png` | пользователь `app` (uid 100) в web и celery |
| Backup создан | выполнено | `screenshots/08_backup_created.png` | `pg_dump` → `backups/backup_20261108_2241.sql`, 64 КБ |
| Restore проверен | выполнено | `screenshots/09_restore_success.png` | восстановление в `medical_restore_test`, данные совпали |
| Открытые порты проверены | выполнено | `screenshots/10_open_ports_check.png` | наружу только 80; 5432, 6379, 8000 закрыты |
| Логи без критических ошибок | выполнено | `screenshots/11_logs_no_critical_errors.png` | 0 traceback в web, celery, nginx |
| Коммит этапа | выполнено | `screenshots/12_security_commit.png` | ветка `feature/up03-stage5-security` |

## Не применимо / ограничения

- HTTPS: на демо-стенде не настроен, параметры подготовлены (`SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`).
- WAF, IDS, мониторинг: вне рамок учебного стенда.

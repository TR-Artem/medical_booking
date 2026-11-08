# RELEASE_CHECKLIST.md

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

Финальная проверка перед релизом 0.2.0.

| Проверка | Команда | Статус |
|---|---|---|
| Линтер | `ruff check .` | пройдено |
| Форматтер | `black --check .` | пройдено |
| Проверка Django | `python manage.py check --deploy` | пройдено |
| Миграции | `python manage.py migrate --noinput` | пройдено |
| Тесты | `python manage.py test` | 44/44 |
| Безопасность зависимостей | `make deps-check` | уязвимостей нет |
| Доступ по ролям | тесты `test_access.py` | 7/7 |
| CI | GitHub Actions `CI` | настроен |
| Changelog | `CHANGELOG.md` | обновлён |
| Release notes | `RELEASE_NOTES.md` | обновлены |
| Релизный архив | `make release` | `release/medical_booking_20261108.zip` |
| Тег версии | `git tag v0.2.0` | создан |

## Что проверить вручную после деплоя

1. http://localhost открывается.
2. Вход пациентом, попытка открыть админ-раздел → страница 403.
3. Вход сисадмином → панель и управление пользователями открываются.
4. В логах нет traceback: `make logs-security`.

## Откат

```bash
git checkout v0.1.0
make deploy
```

Данные БД при откате сохраняются; схема совместима.

# BACKUP_RESTORE_REPORT.md

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

## Условия

- СУБД: PostgreSQL 16 в контейнере `db` (production-compose).
- База: `medical_db`, пользователь `medical_user`.
- Дата проверки: 08.11.2026.

## Создание резервной копии

```bash
make backup
# внутри: docker compose -f docker-compose.prod.yml --env-file .env.production \
#   exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backups/backup_YYYYMMDD_HHMM.sql
```

Результат:

| Параметр | Значение |
|---|---|
| Файл | `backups/backup_20261108_2241.sql` |
| Размер | 64 КБ |
| Строк в дампе | 1913 |
| Формат | plain SQL, восстановление через `psql` |

До создания копии в базе: 7 пользователей, 1 запись, 96 временных слотов.

## Восстановление

```bash
# создать отдельную БД и восстановить дамп
docker compose ... exec -T db sh -c 'createdb -U "$POSTGRES_USER" medical_restore_test'
docker compose ... exec -T db sh -c 'psql -U "$POSTGRES_USER" -d medical_restore_test -q' < backups/backup_20261108_2241.sql
```

Результат восстановления:

| Показатель | Исходная БД | После восстановления |
|---|---|---|
| Пользователи | 7 | 7 |
| Записи на приём | 1 | 1 |
| Временные слоты | 96 | 96 |

Проверка связей после восстановления:

```
patient|doctor|booked
```

То есть запись пациента корректно связана со слотом, врачом и специальностью.

## Очистка

После проверки тестовая БД удалена:

```bash
docker compose ... exec -T db sh -c 'dropdb -U "$POSTGRES_USER" medical_restore_test'
```

## Выводы

- Резервная копия создаётся одной командой и восстанавливается без ошибок.
- Данные и связи после восстановления совпадают с исходными.
- Каталог `backups/` и файлы `*.sql` исключены из git.
- Для эксплуатации нужно добавить регулярный запуск (cron или шаг CI) и хранение копий вне сервера — внесено в реестр рисков (R-06).

# INCIDENT_REPORT.md

> Репозиторий проекта: https://github.com/TR-Artem/medical_booking

## 1. Инцидент

Закрытые разделы при недостатке прав возвращают редирект на главную (302) вместо ошибки 403. Пользователь не понимает, почему раздел не открылся.

Идентификатор в журнале дефектов: BUG-12.
Issue: см. `docs/github_issue.md` (шаблон для GitHub Issues).

## 2. Где обнаружено

Локальный demo-стенд (production-compose), проверка прав на этапе 4 через Django test client:
пациент → `/appointments/admin/dashboard/` → 302 `/`.

## 3. Как воспроизвести

1. Войти пациентом (`patient` / `Demo1234!`).
2. Открыть http://localhost/appointments/admin/dashboard/.
3. Фактически: редирект на главную с сообщением.
4. Ожидается: HTTP 403 и страница с объяснением.

## 4. Диагностика

- Логи приложения: ошибок нет, редирект штатный.
- Код: декораторы `admin_required`, `doctor_required`, `sysadmin_required` и проверка в `doctor_dashboard` вызывали `messages.error` + `redirect("core:home")`.
- Проверка через `manage.py shell` и Django test client:
  `patient → /appointments/admin/dashboard/ = 302 /`, `patient2 → cancel чужой записи = 404` (эта часть уже работала корректно).

## 5. Причина

Отказ в доступе реализован как редирект, а не как HTTP-ошибка. Из-за этого:
- клиент и мониторинг не видят отказ (нет 403 в логах);
- пользователь теряет контекст;
- автотесты не могут отличить «нет прав» от «страница переехала».

## 6. Исправление

- Добавлена функция `access_denied()` в `apps/appointments/views.py`, которая рендерит `templates/403.html` со статусом 403.
- Заменены все четыре места с редиректом: `admin_required`, `doctor_required`, `sysadmin_required`, `doctor_dashboard`.
- Добавлен шаблон `templates/403.html` в стиле проекта.
- Добавлены тесты `apps/appointments/tests/test_access.py` (7 проверок, включая доступ к чужой записи).

## 7. Проверка

```bash
make check          # ruff, black, 44 теста
make release-check  # финальная проверка
```

Результат: все тесты проходят, пациент получает 403, администратор и сисадмин — 200.

## 8. Итог

Инцидент исправлен. Изменения вошли в релиз 0.2.0, архив `release/medical_booking_20261108.zip`.

# DEFECT_LOG.md

Дефекты найдены при аудите, установке, развёртывании и тестировании. Часть исправлена, часть принята как риск.

| ID | Где найдено | Описание | Как воспроизвести | Критичность | Статус | Исправление |
|---|---|---|---|---|---|---|
| BUG-01 | Docker / Celery | Воркер падает: `kombu.exceptions.VersionMismatch` | `docker compose up`, смотреть логи celery | Высокая | fixed | `redis==6.1.0` в `requirements.txt` |
| BUG-02 | UI / статика | Страницы без оформления: классы шаблонов не описаны | Открыть главную | Высокая | fixed | Полный `static/css/main.css` |
| BUG-03 | UI / вход | Иконки отдельно от полей, input-group развалился | Открыть `/accounts/login/` | Средняя | fixed | Селектор полей сужен до `input:not([class])` |
| BUG-04 | Демо-данные | `create_demo_data` падает на чистой базе | Удалить том БД, выполнить команду | Средняя | fixed | Команда сама вызывает `loaddata` |
| BUG-05 | UI / контраст | Контраст 3,42:1 у бейджа и 1,11:1 у номеров шагов | Lighthouse: color-contrast | Средняя | fixed | Цвета приведены к WCAG AA, повторный аудит 100 |
| BUG-06 | UI / семантика | Нарушен порядок заголовков (h2 → h5, h6 в подвале) | Lighthouse: heading-order | Низкая | fixed | `h5` заменены на `h3`, подвал на `h4.h6` |
| BUG-07 | SEO | Нет meta description | Lighthouse: meta-description | Низкая | fixed | Добавлен `<meta name="description">` |
| BUG-08 | Развёртывание | После деплоя отдавался старый CSS | Пересобрать с изменённым CSS | Средняя | fixed | `collectstatic --clear` + `restart web` в `make deploy` |
| BUG-09 | Развёртывание | 502 после пересоздания `web` | Пересоздать контейнер web | Высокая | fixed | `restart nginx` в `make deploy` |
| BUG-10 | Инфраструктура | Dev и prod делили том PostgreSQL, `down -v` мог удалить данные | Запустить `make check` при поднятом prod | Высокая | fixed | Разные имена проектов и томов |
| BUG-11 | Демо | Учётки из README не существовали | Открыть страницу входа | Средняя | fixed | Команда `create_demo_data` |
| BUG-12 | Доступ | Закрытые разделы отдают 302 на главную, а не 403 | Пациентом открыть `/appointments/admin/dashboard/` | Низкая | open | Запланировать 403 с отдельной страницей (этап 6) |
| BUG-13 | Безопасность | Демо-стенд работает по HTTP без TLS | Открыть `http://localhost` | Средняя | open | HTTPS/reverse-proxy с сертификатом — этап 5 |

## Как проверялись исправления

- BUG-05..07: Lighthouse до и после. До: accessibility 88, best-practices 100, SEO 75. После: 100/100/100 (`reports/lighthouse_report.html`).
- BUG-01: `docker compose ps` — celery и celery-beat в статусе `running`.
- BUG-08..09: повторный `make deploy`, страница отдаёт новый хеш CSS, ответ 200.
- BUG-10: `docker compose -f docker-compose.prod.yml ps` и `docker compose -f docker-compose.yml ps` — независимые проекты.
- BUG-03: скриншот страницы входа после исправления.

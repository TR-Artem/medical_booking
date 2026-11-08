.PHONY: setup run check format docker-up docker-down logs migrate deploy restart check-deploy test api-test quality-check performance logs-check security-check deps-check backup restore ports-check logs-security build release-check release clean

setup:
	@test -f .env || cp .env.example .env
	$(DEV) build

run:
	$(DEV) up --build -d
	$(DEV) exec -T web python manage.py migrate --noinput
	$(DEV) exec -T web python manage.py collectstatic --noinput --clear
	$(DEV) restart nginx
	@echo "Открыть: http://localhost:8080"

check:
	$(PROD) --profile tools run --rm tools sh -c "ruff check . && black --check . && python manage.py test"

check-dev:
	$(DEV) up -d --build
	$(DEV) exec -T web sh -c "ruff check . && black --check . && python manage.py test"

format:
	$(PROD) --profile tools run --rm tools sh -c "ruff check --fix . && black ."

docker-up:
	$(DEV) up --build -d

docker-down:
	$(DEV) down

logs:
	$(DEV) logs -f --tail=100

migrate:
	$(PROD) exec -T web python manage.py migrate

DEV = docker compose -f docker-compose.yml
PROD = docker compose -f docker-compose.prod.yml --env-file .env.production

deploy:
	@test -f .env.production || (echo "Создайте .env.production из .env.production.example" && exit 1)
	$(PROD) up --build -d
	$(PROD) exec -T web python manage.py migrate --noinput
	$(PROD) exec -T web python manage.py collectstatic --noinput --clear
	$(PROD) restart web
	$(PROD) restart nginx
	$(PROD) ps

restart:
	$(PROD) down
	$(PROD) up -d
	$(PROD) ps

check-deploy:
	$(PROD) ps
	$(PROD) logs --tail=80
	curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost/

test:
	$(PROD) exec -T web python manage.py test

api-test:
	@echo "Проверка HTTP-маршрутов"
	@for u in / /accounts/login/ /accounts/register/ /appointments/doctors/ /appointments/my/ /appointments/admin/dashboard/ /no-such-page/; do \
		curl -s -o /dev/null -w "$$u -> %{http_code} (%{time_total}s)\n" "http://localhost$$u"; \
	done

quality-check: test api-test logs-check
	@echo "Проверка качества завершена"

performance:
	@echo "Среднее время ответа / (10 запросов):"
	@for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null -w "%{time_total}\n" http://localhost/; done | awk '{s+=$$1} END {printf "avg %.3f s\n", s/NR}'
	@npx --yes lighthouse@12 http://localhost/ --only-categories=accessibility,best-practices,seo --output=html --output-path=reports/lighthouse_report.html --chrome-flags="--headless --no-sandbox" --quiet

logs-check:
	@mkdir -p reports
	$(PROD) logs --no-color --tail=100 web celery celery-beat nginx > reports/logs_tail.txt
	@grep -Eci "traceback|error|critical|fatal" reports/logs_tail.txt || echo "критических ошибок не найдено"

security-check:
	@echo "=== Файлы .env в индексе git ==="
	@git ls-files | grep -E "(^|/)\.env" || echo "Файлов .env в индексе нет (только примеры)"
	@echo
	@echo "=== Поиск секретов ==="
	@git grep -nE "password|secret|token|api_key|apikey|jwt" -- ':!docs' ':!screenshots' ':!*.md' ':!*.html' | head -20 || true
	@echo
	@echo "Если найдены реальные значения — удалить и заменить на .env.example"

deps-check:
	@docker run --rm -v "$$(pwd)/requirements.txt:/req.txt:ro" python:3.12-slim \
		sh -c "pip install -q pip-audit 2>/dev/null && pip-audit -r /req.txt"

backup:
	@mkdir -p backups
	@TS=$$(date +%Y%m%d_%H%M); \
	$(PROD) exec -T db sh -c 'pg_dump -U "$$POSTGRES_USER" "$$POSTGRES_DB"' > backups/backup_$$TS.sql; \
	echo "Backup создан: backups/backup_$$TS.sql"

restore:
	@test -n "$(BACKUP)" || (echo "Укажите файл: make restore BACKUP=backups/backup_YYYYMMDD_HHMM.sql" && exit 1)
	$(PROD) exec -T db sh -c 'dropdb -U "$$POSTGRES_USER" --if-exists medical_restore_test && createdb -U "$$POSTGRES_USER" medical_restore_test'
	$(PROD) exec -T db sh -c 'psql -U "$$POSTGRES_USER" -d medical_restore_test -q' < $(BACKUP)
	@echo "Восстановлено в medical_restore_test. Проверьте данные и удалите БД."

ports-check:
	@echo "=== Контейнеры и порты ==="
	$(PROD) ps --format "{{.Service}}: {{.Ports}}"
	@echo
	@echo "=== Проверка хоста ==="
	@for p in 80 5432 6379 8000; do (nc -z -w 1 localhost $$p && echo "$$p открыт") || echo "$$p закрыт"; done

logs-security:
	@mkdir -p reports
	$(PROD) logs --no-color --tail=100 web celery nginx > reports/security_logs.txt
	@grep -Eci "traceback|error|critical|fatal" reports/security_logs.txt || echo "критических ошибок не найдено"

build:
	@echo "Сборка release-образа"
	$(PROD) build

release-check: check test
	@echo "Финальная проверка перед релизом пройдена"

release: release-check
	@mkdir -p release
	@TS=$$(date +%Y%m%d); \
	git archive --format=zip --prefix=medical_booking/ -o release/medical_booking_$$TS.zip HEAD; \
	echo "Релизный архив: release/medical_booking_$$TS.zip"

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +

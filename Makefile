.PHONY: setup run check format docker-up docker-down logs migrate deploy restart check-deploy test api-test quality-check performance logs-check clean

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
	$(PROD) exec -T web sh -c "ruff check . && black --check . && python manage.py test"

check-dev:
	$(DEV) up -d --build
	$(DEV) exec -T web sh -c "ruff check . && black --check . && python manage.py test"

format:
	$(PROD) exec -T web sh -c "ruff check --fix . && black ."

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
	$(PROD) logs --no-color --tail=100 > reports/logs_tail.txt
	@grep -Eci "traceback|error|critical|fatal" reports/logs_tail.txt || echo "критических ошибок не найдено"

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +

.PHONY: setup run check format docker-up docker-down logs migrate deploy restart check-deploy clean

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

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +

.PHONY: setup run check format docker-up docker-down logs migrate deploy restart check-deploy clean

setup:
	@test -f .env || cp .env.example .env
	docker compose build

run:
	docker compose up --build -d
	@echo "Открыть: http://localhost:8000"

check:
	docker compose up -d --build
	docker compose exec -T web sh -c "ruff check . && black --check . && python manage.py test"

format:
	docker compose exec -T web sh -c "ruff check --fix . && black ."

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

logs:
	docker compose logs -f --tail=100

migrate:
	docker compose exec -T web python manage.py migrate

PROD = docker compose -f docker-compose.prod.yml --env-file .env.production

deploy:
	@test -f .env.production || (echo "Создайте .env.production из .env.production.example" && exit 1)
	$(PROD) up --build -d
	$(PROD) exec -T web python manage.py migrate --noinput
	$(PROD) exec -T web python manage.py collectstatic --noinput
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

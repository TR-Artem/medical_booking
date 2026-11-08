.PHONY: setup run check format docker-up docker-down logs migrate clean

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

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +

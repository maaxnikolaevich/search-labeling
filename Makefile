.PHONY: run

build:
	docker compose -f docker-compose.yml build

run:
	docker compose -f docker-compose.yml up --force-recreate --remove-orphans

migrate:
	docker compose exec app /bin/bash -c "uv run alembic upgrade head"
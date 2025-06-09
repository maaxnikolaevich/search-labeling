.PHONY: run

build:
	docker compose -f docker-compose.yml build

run:
	docker compose -f docker-compose.yml up --force-recreate --remove-orphans

migrate:
	docker compose exec app /bin/bash -c "uv run alembic upgrade head"

downgrade-before:
	docker compose exec app /bin/bash -c "uv run alembic downgrade head-1"

create-migration:
	@read -p "Title: " title; \
	docker compose exec app /bin/bash -c \
	 "uv run alembic revision --autogenerate -m '$$title'"
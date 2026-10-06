.PHONY: help infra up worker beat migrate fmt lint test fe-dev

help:
	@echo "infra    - start postgres+pgvector and redis"
	@echo "up       - run FastAPI dev server"
	@echo "worker   - run Celery worker"
	@echo "beat     - run Celery beat (observer cron)"
	@echo "migrate  - alembic upgrade head"
	@echo "test     - run backend tests"
	@echo "fmt/lint - ruff format / check"
	@echo "fe-dev   - run Next.js dev server"

infra:
	docker compose up -d db redis

up:
	cd backend && uv run uvicorn app.main:app --reload

worker:
	cd backend && uv run celery -A app.workers.celery_app.celery worker --loglevel=info

beat:
	cd backend && uv run celery -A app.workers.celery_app.celery beat --loglevel=info

migrate:
	cd backend && uv run alembic upgrade head

fmt:
	cd backend && uv run ruff format .

lint:
	cd backend && uv run ruff check .

test:
	cd backend && uv run pytest

fe-dev:
	cd frontend && npm run dev

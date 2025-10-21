.PHONY: help dev dev-build dev-down dev-clean dev-logs dev-restart
.PHONY: backend-shell backend-logs backend-lint backend-format backend-format-check backend-typecheck backend-test backend-coverage backend-migrate
.PHONY: frontend-shell frontend-logs frontend-lint frontend-test frontend-test-watch frontend-build
.PHONY: db-shell db-migrate db-revision db-reset db-init
.PHONY: test test-backend test-frontend test-unit test-integration coverage
.PHONY: ci lint format format-check typecheck lint-all
.PHONY: clean clean-pyc clean-cache clean-test clean-db clean-docker clean-all
.PHONY: status health

# === Development ===
dev:
	docker compose up -d

dev-build:
	docker compose up -d --build

dev-down:
	docker compose down

dev-clean:
	docker compose down -v

dev-logs:
	docker compose logs -f

dev-restart:
	docker compose restart

# === Backend ===
backend-shell:
	docker compose exec backend bash

backend-logs:
	docker compose logs -f backend

backend-lint:
	docker compose run --rm backend ruff check app

backend-format:
	docker compose run --rm backend black app

backend-format-check:
	docker compose run --rm backend black --check app

backend-typecheck:
	docker compose run --rm backend mypy app

backend-test:
	docker compose run --rm -e PYTHONPATH=/app -e ENVIRONMENT=testing backend pytest -v app/tests

backend-coverage:
	docker compose run --rm -e PYTHONPATH=/app -e ENVIRONMENT=testing backend pytest -v --cov=app --cov-report=term-missing --cov-report=html app/tests

backend-migrate:
	docker compose run --rm backend alembic upgrade head

# === Frontend ===
frontend-shell:
	docker compose exec frontend sh

frontend-logs:
	docker compose logs -f frontend

frontend-lint:
	docker compose exec frontend npm run lint

frontend-test:
	docker compose exec frontend npm test -- --run

frontend-test-watch:
	docker compose exec frontend npm test

frontend-build:
	docker compose exec frontend npm run build

# === Database ===
db-shell:
	docker compose exec postgres psql -U insightboard -d insightboard

db-migrate:
	docker compose run --rm backend alembic upgrade head

db-revision:
	docker compose run --rm backend alembic revision --autogenerate -m "$(msg)"

db-reset:
	docker compose down -v
	docker compose up -d
	sleep 5
	docker compose run --rm backend alembic upgrade head

db-init:
	docker compose run --rm backend python scripts/init_db.py

# === Testing ===
test: test-backend test-frontend

test-backend:
	docker compose run --rm -e PYTHONPATH=/app -e ENVIRONMENT=testing backend pytest -v app/tests

test-frontend:
	docker compose exec frontend npm test -- --run

test-unit:
	docker compose run --rm -e PYTHONPATH=/app -e ENVIRONMENT=testing backend pytest -v app/tests/unit

test-integration:
	docker compose run --rm -e PYTHONPATH=/app -e ENVIRONMENT=testing backend pytest -v app/tests/integration

coverage:
	docker compose run --rm -e PYTHONPATH=/app -e ENVIRONMENT=testing backend pytest -v --cov=app --cov-report=term-missing --cov-report=html app/tests

coverage-report:
	open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "Coverage report at htmlcov/index.html"

# === CI ===
ci: lint typecheck test

lint: backend-lint frontend-lint

format: backend-format

format-check: backend-format-check

typecheck: backend-typecheck

lint-all: lint format-check typecheck

# === Cleaning ===
clean-pyc:
	docker compose run --rm backend sh -c "find . -type f -name '*.py[co]' -delete && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true"

clean-cache:
	docker compose run --rm backend sh -c "rm -rf .pytest_cache .mypy_cache .ruff_cache"
	docker compose exec frontend sh -c "rm -rf node_modules/.cache" 2>/dev/null || true

clean-test:
	docker compose run --rm backend sh -c "rm -rf .coverage htmlcov/ .tox/"

clean-db:
	docker compose down -v

clean-docker:
	docker compose down --rmi local --volumes --remove-orphans

clean: clean-pyc clean-cache clean-test

clean-all: clean clean-db clean-docker

# === Utilities ===
status:
	docker compose ps

health:
	@curl -sf http://localhost:8000/health | python -m json.tool || echo "Backend not responding"
	@curl -sf http://localhost:3000 >/dev/null && echo "Frontend: OK" || echo "Frontend not responding"

shell:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U insightboard -d insightboard

# === Help ===
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Start all services"
	@echo "  make dev-build        Rebuild and start"
	@echo "  make dev-down         Stop services"
	@echo "  make dev-clean        Stop and remove volumes"
	@echo "  make dev-logs         Follow logs"
	@echo "  make dev-restart      Restart services"
	@echo ""
	@echo "Backend:"
	@echo "  make backend-shell    Enter backend container"
	@echo "  make backend-logs     Show backend logs"
	@echo "  make backend-lint     Run ruff linter"
	@echo "  make backend-format   Format code with black"
	@echo "  make backend-typecheck Run mypy type checker"
	@echo "  make backend-test     Run tests"
	@echo "  make backend-coverage Run tests with coverage"
	@echo "  make backend-migrate  Run database migrations"
	@echo ""
	@echo "Frontend:"
	@echo "  make frontend-shell   Enter frontend container"
	@echo "  make frontend-logs    Show frontend logs"
	@echo "  make frontend-lint    Run ESLint"
	@echo "  make frontend-test    Run tests (once)"
	@echo "  make frontend-test-watch Run tests (watch mode)"
	@echo "  make frontend-build   Build production bundle"
	@echo ""
	@echo "Database:"
	@echo "  make db-shell         PostgreSQL shell"
	@echo "  make db-migrate       Run migrations"
	@echo "  make db-revision msg='...' Create migration"
	@echo "  make db-reset         Reset database"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-backend     Backend tests only"
	@echo "  make test-frontend    Frontend tests only"
	@echo "  make test-unit        Backend unit tests"
	@echo "  make test-integration Backend integration tests"
	@echo "  make coverage         Coverage report"
	@echo ""
	@echo "CI:"
	@echo "  make ci               Run CI checks"
	@echo "  make lint             Lint all code"
	@echo "  make format           Format code"
	@echo "  make format-check     Check formatting"
	@echo "  make typecheck        Type check"
	@echo ""
	@echo "Cleaning:"
	@echo "  make clean            Clean cache and artifacts"
	@echo "  make clean-all        Full cleanup"
	@echo "  make clean-db         Remove database volumes"
	@echo ""
	@echo "Utilities:"
	@echo "  make status           Container status"
	@echo "  make health           Health check"
	@echo "  make help             Show this help"

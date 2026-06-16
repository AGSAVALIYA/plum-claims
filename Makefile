.PHONY: help install dev-install test lint format run seed eval frontend-install frontend-dev clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	uv sync

dev-install: ## Install all dev dependencies
	uv sync --group dev

test: ## Run tests
	uv run pytest backend/tests/ -v

test-cov: ## Run tests with coverage
	uv run pytest backend/tests/ -v --cov=backend --cov-report=term --cov-report=html

lint: ## Run linting
	uv run ruff check backend/ scripts/

format: ## Format code
	uv run ruff check --fix backend/ scripts/
	uv run ruff format backend/ scripts/

run: ## Start the FastAPI backend
	uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

seed: ## Seed the database
	uv run python scripts/seed_data.py

eval: ## Run evaluation
	uv run python scripts/run_eval.py

frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Start the frontend dev server
	cd frontend && npm run dev

clean: ## Clean up build artifacts
	rm -rf .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

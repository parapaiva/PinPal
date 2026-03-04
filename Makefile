.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: help install lint format typecheck test test-unit test-integration up down logs migrate dev

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies (dev included)
	uv sync --all-extras

lint: ## Run ruff linter + mypy type checker
	uv run ruff check src tests
	uv run mypy src

format: ## Auto-format code with ruff
	uv run ruff format src tests
	uv run ruff check --fix src tests

typecheck: ## Run mypy
	uv run mypy src

test: ## Run all tests (requires Docker services)
	uv run pytest

test-unit: ## Run unit tests only (no Docker needed)
	uv run pytest -m "not integration"

test-integration: ## Run integration tests only (requires Docker services)
	uv run pytest -m integration

up: ## Start Postgres + MongoDB containers
	docker compose up -d

down: ## Stop containers
	docker compose down

logs: ## Tail container logs
	docker compose logs -f

migrate: ## Run Alembic migrations
	uv run alembic upgrade head

dev: ## Start FastAPI dev server
	uv run uvicorn pinpal.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000

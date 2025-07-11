.PHONY: help install lint format format-check typecheck test test-cov docs clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with uv
	uv sync

lint:  ## Run ruff linter
	uv run ruff check .

format:  ## Format code with ruff
	uv run ruff format .

format-check:  ## Check code formatting without modifying files
	uv run ruff format --check .

fix:  ## Fix linting issues and format code
	uv run ruff check . --fix
	uv run ruff format .

typecheck:  ## Run type checking with mypy
	uv run mypy .

test:  ## Run tests
	uv run pytest

test-cov:  ## Run tests with coverage report
	uv run pytest --cov=src --cov-report term --cov-report html --cov-report xml -vv

docs:  ## Generate documentation
	mkdir -p ./docs/build
	uv run ./docs/generate.sh --out=./docs/build/ --pypath=src/

clean:  ## Clean build artifacts
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov .coverage coverage.xml .pytest_cache
	rm -rf docs/build
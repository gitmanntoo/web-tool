.PHONY: help install dev lint format check test clean

.DEFAULT_GOAL := help

# Default target: show help
help:
	@echo "Available targets:"
	@echo ""
	@echo "Development:"
	@echo "  make install    - Install project with all dependencies"
	@echo "  make dev        - Install development dependencies"
	@echo ""
	@echo "Linting & Formatting:"
	@echo "  make lint       - Run ruff linting checks"
	@echo "  make format     - Format Python code with ruff"
	@echo "  make check      - Run all quality checks (lint + format)"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run pytest tests"
	@echo "  make testcov    - Run tests with coverage report"
	@echo "  make testv      - Run tests with verbose output"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs       - Generate HTML documentation"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean      - Remove temporary files and cache"
	@echo "  make run        - Run the application"
	@echo "  make docker     - Build Docker image"

# Install with all dependencies
install:
	@echo "Installing project with all dependencies..."
	uv pip install -e ".[dev]"

# Install development dependencies
dev:
	@echo "Installing development dependencies..."
	uv pip install -e ".[dev]"

# Run all linting checks
lint:
	@echo "Running ruff check..."
	ruff check library/ tests/

# Format Python code
format:
	@echo "Running ruff format..."
	ruff format library/ tests/

# Run import sorting
check-imports:
	@echo "Running ruff check --select I..."
	ruff check --select I --fix library/ tests/

# Run all quality checks
check: lint format check-imports
	@echo "All quality checks passed!"

# Run pytest tests
test:
	@echo "Running pytest..."
	uv run pytest

# Run tests with coverage report
testcov:
	@echo "Running tests with coverage..."
	uv run pytest tests/ --cov=library --cov-report=html --cov-report=term

# Run tests with verbose output
testv:
	@echo "Running tests with verbose output..."
	uv run pytest tests/ -vv

# Generate HTML documentation
docs:
	@echo "Generating documentation..."
	@echo "Documentation generation not configured. Add documentation tools if needed."

# Clean temporary files and cache
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -name "*.py[cod]" -delete
	find . -name "*.so" -delete
	find . -name ".coverage" -delete
	find . -name "*.egg-info" -type d -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	@echo "Clean complete!"

# Run the application
run:
	@echo "Running the application..."
	./run-it.sh

# Build Docker image
docker:
	@echo "Building Docker image..."
	docker build -t web-tool .

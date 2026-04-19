DOCKER_REPO = dockmann/web-tool
DOCKER_IMAGE = $(DOCKER_REPO):latest

# Docker Hub credentials (required for push operations)
DOCKERHUB_USERNAME ?= $(shell echo $$DOCKERHUB_USERNAME)
DOCKERHUB_TOKEN ?= $(shell echo $$DOCKERHUB_TOKEN)

# Version resolution: git tag if at tagged commit, else dev-<sha>, else dev
VERSION = $(shell tag=$$(git describe --tags --exact-match 2>/dev/null || true); \
	if [ -n "$$tag" ]; then \
		echo "$$tag" | sed 's/^v//'; \
	else \
		sha=$$(git rev-parse --short HEAD 2>/dev/null || true); \
		if [ -n "$$sha" ]; then \
			echo "dev-$$sha"; \
		else \
			echo "dev"; \
		fi; \
	fi)

# Verify Docker Hub credentials are set
define check-docker-credentials
	@if [ -z "$(DOCKERHUB_USERNAME)" ]; then \
		echo "Error: DOCKERHUB_USERNAME environment variable not set"; \
		echo "Set it with: export DOCKERHUB_USERNAME=your-username"; \
		exit 1; \
	fi
	@if [ -z "$(DOCKERHUB_TOKEN)" ]; then \
		echo "Error: DOCKERHUB_TOKEN environment variable not set"; \
		echo "Create a token at: https://hub.docker.com/settings/security"; \
		exit 1; \
	fi
endef

.PHONY: help install dev run lint format check test testcov testv docs check-imports clean docker-run docker-build docker-buildx docker-push docker-release docker-describe docker-stop docker-clean

.DEFAULT_GOAL := help

# Default target: show help
help:
	@echo "Available targets:"
	@echo ""
	@echo "Development:"
	@echo "  make install    - Install project with all dependencies"
	@echo "  make dev        - Install development dependencies"
	@echo "  make run        - Run the application locally"
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
	@echo ""
	@echo "Docker:"
	@echo "  make docker-run       - Run the published Docker image"
	@echo "  make docker-build     - Build Docker image for current platform"
	@echo "  make docker-buildx    - Build multi-platform image (amd64/arm64)"
	@echo "  make docker-push      - Build and push multi-platform image"
	@echo "  make docker-release   - Build, push, and update Docker Hub description"
	@echo "  make docker-describe  - Update Docker Hub description from README"
	@echo "  make docker-stop      - Stop running container"
	@echo "  make docker-clean     - Stop container and prune build cache"

# Install with runtime dependencies only
install:
	@echo "Installing project with runtime dependencies..."
	uv pip install -e .

# Install with all dependencies (including dev)
dev:
	@echo "Installing project with development dependencies..."
	uv pip install -e ".[dev]"

# Run the application locally
run:
	@echo "Running web-tool..."
	uv run python web-tool.py

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

# Run the published Docker image
docker-run:
	@echo "Running Docker container from $(DOCKER_IMAGE)..."
	docker run -it --rm -p 8532:8532 --name web-tool $(DOCKER_IMAGE)

# Build Docker image for current platform
docker-build:
	@echo "Building Docker image $(DOCKER_IMAGE)..."
	docker build -t $(DOCKER_IMAGE) .

# Build multi-platform image (amd64/arm64)
docker-buildx:
	@echo "Building multi-platform Docker image $(DOCKER_IMAGE)..."
	docker buildx build --platform linux/amd64,linux/arm64 --tag $(DOCKER_IMAGE) .

# Build and push multi-platform image with version tag
docker-push:
	$(call check-docker-credentials)
	@echo "Building and pushing multi-platform image..."
	@echo "  Image: $(DOCKER_IMAGE)"
	@echo "  Version: $(VERSION)"
	@echo "  Platforms: linux/amd64, linux/arm64"
	@echo ""
	@echo "Logging in to Docker Hub..."
	@echo "$(DOCKERHUB_TOKEN)" | docker login -u "$(DOCKERHUB_USERNAME)" --password-stdin
	@echo ""
	@echo "Building and pushing..."
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--tag $(DOCKER_IMAGE) \
		--tag $(DOCKER_REPO):$(VERSION) \
		--push .
	@echo ""
	@echo "Pushed: $(DOCKER_IMAGE)"
	@echo "Pushed: $(DOCKER_REPO):$(VERSION)"

# Full release: build, push, and update Docker Hub description
docker-release: docker-push docker-describe
	@echo ""
	@echo "=== Release Complete ==="
	@echo "Image: $(DOCKER_REPO):$(VERSION)"
	@echo "Latest: $(DOCKER_IMAGE)"

# Update Docker Hub description from README.md
docker-describe:
	$(call check-docker-credentials)
	@echo "Updating Docker Hub description..."
	@echo "  Repository: $(DOCKER_REPO)"
	@echo "  Source: README.md"
	@echo ""
	@PAYLOAD=$$(python3 -c 'import json, pathlib; print(json.dumps({"full_description": pathlib.Path("README.md").read_text()}))'); \
	NETRC_FILE=$$(mktemp); \
	trap 'rm -f "$$NETRC_FILE"' EXIT; \
	umask 077; \
	printf 'machine hub.docker.com login %s password %s\n' "$(DOCKERHUB_USERNAME)" "$(DOCKERHUB_TOKEN)" > "$$NETRC_FILE"; \
	if curl -fsS -X PATCH \
		-H "Content-Type: application/json" \
		--netrc-file "$$NETRC_FILE" \
		-d "$$PAYLOAD" \
		https://hub.docker.com/v2/repositories/$(DOCKER_REPO)/ \
		> /dev/null; then \
		echo "Description updated successfully"; \
	else \
		echo "Failed to update description (check credentials)"; \
		exit 1; \
	fi

# Stop running container
docker-stop:
	@echo "Stopping web-tool container..."
	-docker stop web-tool 2>/dev/null || true
	-docker rm web-tool 2>/dev/null || true

# Stop container and prune build cache
docker-clean: docker-stop
	@echo "Pruning Docker build cache..."
	docker buildx prune -f

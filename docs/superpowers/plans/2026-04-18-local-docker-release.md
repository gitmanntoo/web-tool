# Local Docker Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace GitHub Actions Docker workflow with local Makefile targets that build, push, and update Docker Hub description using git tags for versioning.

**Architecture:** Environment-variable based Docker Hub authentication; git tag-based version resolution (or dev- prefix for untagged commits); Makefile targets orchestrate buildx multi-platform builds and Docker Hub API calls for description updates.

**Tech Stack:** Make, Docker (buildx), Docker Hub REST API, shell scripting

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `.github/workflows/docker.yml` | Delete | Remove broken GitHub Actions workflow |
| `Makefile` | Modify | Add `docker-release`, `docker-describe` targets; update `docker-push` with versioning |
| `VERSION` | Delete | No longer needed (git tags replace auto-increment) |

---

### Task 1: Delete GitHub Actions Workflow

**Files:**
- Delete: `.github/workflows/docker.yml`

- [ ] **Step 1: Remove the GitHub Actions workflow file**

```bash
rm .github/workflows/docker.yml
```

- [ ] **Step 2: Verify deletion and commit**

```bash
git add .github/workflows/docker.yml
git commit -m "ci: remove GitHub Actions Docker workflow"
```

---

### Task 2: Update Makefile with New Targets

**Files:**
- Modify: `Makefile` (add new variables and targets)

- [ ] **Step 1: Add Docker Hub credentials check script at top of Makefile**

Add after line 1 (`DOCKER_IMAGE = dockmann/web-tool:latest`):

```makefile
# Docker Hub credentials (required for push operations)
DOCKERHUB_USERNAME ?= $(shell echo $$DOCKERHUB_USERNAME)
DOCKERHUB_TOKEN ?= $(shell echo $$DOCKERHUB_TOKEN)

# Version resolution: git tag if at tagged commit, else dev-<sha>
VERSION := $(shell git describe --tags --exact-match 2>/dev/null | sed 's/^v//' || echo "dev-$$(git rev-parse --short HEAD)")

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
```

- [ ] **Step 2: Update help target to include new targets**

Replace lines 32-38 (the Docker section in help) with:

```makefile
@echo "Docker:"
@echo "  make docker-run       - Run the published Docker image"
@echo "  make docker-build     - Build Docker image for current platform"
@echo "  make docker-buildx    - Build multi-platform image (amd64/arm64)"
@echo "  make docker-push      - Build and push multi-platform image"
@echo "  make docker-release   - Build, push, and update Docker Hub description"
@echo "  make docker-describe  - Update Docker Hub description from README"
@echo "  make docker-stop      - Stop running container"
@echo "  make docker-clean     - Stop container and prune build cache"
```

- [ ] **Step 3: Update docker-push target with versioning**

Replace lines 124-127 (the docker-push target) with:

```makefile
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
		--tag dockmann/web-tool:$(VERSION) \
		--push .
	@echo ""
	@echo "Pushed: $(DOCKER_IMAGE)"
	@echo "Pushed: dockmann/web-tool:$(VERSION)"
```

- [ ] **Step 4: Add docker-release target**

Add after the docker-push target (after line 127 in the original):

```makefile
# Full release: build, push, and update Docker Hub description
docker-release: docker-push docker-describe
	@echo ""
	@echo "=== Release Complete ==="
	@echo "Image: dockmann/web-tool:$(VERSION)"
	@echo "Latest: $(DOCKER_IMAGE)"
```

- [ ] **Step 5: Add docker-describe target**

Add after docker-release target:

```makefile
# Update Docker Hub description from README.md
docker-describe:
	$(call check-docker-credentials)
	@echo "Updating Docker Hub description..."
	@echo "  Repository: $(DOCKERHUB_USERNAME)/web-tool"
	@echo "  Source: README.md"
	@echo ""
	@DESCRIPTION=$$(cat README.md | sed 's/"/\\"/g' | sed ':a;N;$$!ba;s/\n/\\n/g'); \
	curl -s -X PATCH \
		-H "Content-Type: application/json" \
		-u "$(DOCKERHUB_USERNAME):$(DOCKERHUB_TOKEN)" \
		-d "{\"full_description\": \"$$DESCRIPTION\"}" \
		https://hub.docker.com/v2/repositories/$(DOCKERHUB_USERNAME)/web-tool/ \
		| grep -q "full_description" && echo "Description updated successfully" || echo "Failed to update description (check credentials)"
```

- [ ] **Step 6: Verify Makefile syntax and commit**

```bash
make -n docker-push 2>&1 | head -5
# Expected: Should show the command structure without errors
git add Makefile
git commit -m "build: add docker-release and docker-describe Makefile targets"
```

---

### Task 3: Delete VERSION File

**Files:**
- Delete: `VERSION`

- [ ] **Step 1: Remove VERSION file**

```bash
rm VERSION
```

- [ ] **Step 2: Commit the deletion**

```bash
git add VERSION
git commit -m "chore: remove VERSION file (replaced by git tags)"
```

---

### Task 4: Test Version Resolution

**Files:**
- Test: `Makefile` version logic

- [ ] **Step 1: Test version resolution without credentials**

```bash
unset DOCKERHUB_USERNAME DOCKERHUB_TOKEN
make docker-push 2>&1 | head -5
# Expected: "Error: DOCKERHUB_USERNAME environment variable not set"
```

- [ ] **Step 2: Test version resolution with credentials (mocked)**

```bash
export DOCKERHUB_USERNAME=testuser
export DOCKERHUB_TOKEN=testtoken
make -n docker-push 2>&1 | grep -E "(VERSION|version:|Pushed:)"
# Expected: Shows version (dev-XXX if untagged, or version number if at tag)
```

---

## Self-Review

**Spec Coverage Check:**
- ✅ Delete `.github/workflows/docker.yml` → Task 1
- ✅ Add `make docker-release` target → Task 2 Step 4
- ✅ Add `make docker-describe` target → Task 2 Step 5
- ✅ Update `make docker-push` with versioning → Task 2 Step 3
- ✅ Delete `VERSION` file → Task 3
- ✅ Git tag-based version resolution → Task 2 Step 1 (VERSION variable)
- ✅ Environment variable credentials → Task 2 Step 1 (check-docker-credentials)
- ✅ Docker Hub API description update → Task 2 Step 5

**Placeholder Scan:** ✅ No TBD, TODO, or vague instructions found

**Type Consistency:** ✅ N/A for Makefile (all shell commands)

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-18-local-docker-release.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**

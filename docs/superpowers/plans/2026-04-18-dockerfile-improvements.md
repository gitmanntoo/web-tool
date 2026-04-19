# Dockerfile Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the Dockerfile from a single-stage build to a multi-stage build, reducing image size from ~1.53GB to ~800-850MB while improving security and build cache efficiency.

**Architecture:** Two-stage Dockerfile — a `builder` stage compiles dependencies with build tools, then a `runtime` stage copies only the installed artifacts (no compiler, dev headers, or uv binary). Also updates .dockerignore and the healthcheck.

**Tech Stack:** Docker multi-stage builds, python:3.14-slim, uv, NLTK, CairoSVG

---

### Task 1: Update .dockerignore

**Files:**
- Modify: `.dockerignore`

- [ ] **Step 1: Add `specs/` and `.claude/` to .dockerignore**

Open `.dockerignore` and add two new entries after the existing "Build cache" section:

```
# Design and spec files
specs/

# Claude Code session files
.claude/
```

These directories are not needed at runtime and should not be included in the build context.

- [ ] **Step 2: Verify the build context is smaller (optional)**

Run: `docker build --check . 2>/dev/null || echo "Build syntax check not supported, visual inspection sufficient"`

You can also inspect the context size with: `docker build --progress=plain . 2>&1 | head -5` to confirm the excluded dirs aren't sent.

- [ ] **Step 3: Commit**

```bash
git add .dockerignore
git commit -m "chore: add specs/ and .claude/ to .dockerignore - completes plan item #1"
```

---

### Task 2: Rewrite Dockerfile with multi-stage build

**Files:**
- Modify: `Dockerfile`

This is the main change. The entire Dockerfile will be rewritten. Read the current Dockerfile first, then replace it entirely.

- [ ] **Step 1: Write the new Dockerfile**

Replace the entire contents of `Dockerfile` with:

```dockerfile
# === Builder stage: compile dependencies ===
FROM python:3.14-slim AS builder

# Install build deps + clean apt cache in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential libcairo2-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first (cache-friendly: code changes don't invalidate pip layer)
COPY pyproject.toml uv.lock ./

# Copy source code (setuptools requires all package dirs present)
COPY library/ ./library/
COPY routes/ ./routes/
COPY static/ ./static/
COPY templates/ ./templates/
COPY web-tool.py README.md ./

# Install Python dependencies
RUN uv pip install --system --no-cache .

# Download NLTK data to a world-readable location
ENV NLTK_DATA=/usr/share/nltk_data
RUN python -m nltk.downloader -d /usr/share/nltk_data wordnet words

# === Runtime stage: minimal production image ===
FROM python:3.14-slim

# Install only runtime system deps (no compiler, no dev headers)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libcairo2 wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/

# Copy NLTK data from builder
COPY --from=builder /usr/share/nltk_data /usr/share/nltk_data
ENV NLTK_DATA=/usr/share/nltk_data

WORKDIR /app

# Copy application source (changes most frequently — last layer)
COPY library/ ./library/
COPY routes/ ./routes/
COPY static/ ./static/
COPY templates/ ./templates/
COPY web-tool.py README.md ./

# Non-root user for security
RUN useradd --uid 1000 --create-home appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /data && chown appuser:appuser /data

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:8532/ || exit 1

EXPOSE 8532
ENTRYPOINT ["python", "web-tool.py"]
```

Key changes from the original:
1. Two `FROM` stages — `builder` and the unnamed runtime
2. Builder installs `build-essential` + `libcairo2-dev`, runtime only installs `libcairo2` + `wget`
3. `COPY --from=builder` for site-packages and NLTK data — no compiler or uv in runtime
4. `pyproject.toml` + `uv.lock` copied before source code for better layer caching
5. Healthcheck uses `wget --spider` instead of Python one-liner
6. `--no-install-recommends` on both apt-get commands

- [ ] **Step 2: Build the image and verify it starts**

```bash
docker build -t dockmann/web-tool:test .
```

Expected: Build succeeds with two stages visible in the output.

Then run:
```bash
docker run -d --name web-tool-test -p 8532:8532 dockmann/web-tool:test && sleep 3 && docker logs web-tool-test
```

Expected: Application starts and listens on port 8532.

- [ ] **Step 3: Verify the healthcheck works**

```bash
docker inspect --format='{{.State.Health.Status}}' web-tool-test
```

Expected: `healthy` (may take ~30s for first check to pass).

- [ ] **Step 4: Verify image size reduction**

```bash
docker images dockmann/web-tool:test --format '{{.Size}}'
```

Expected: ~800-850MB (down from 1.53GB).

- [ ] **Step 5: Verify no build tools in runtime image**

```bash
docker run --rm dockmann/web-tool:test which gcc make uv 2>&1
```

Expected: All three return nothing or "not found" — no compiler or uv in the runtime image.

- [ ] **Step 6: Stop and remove the test container**

```bash
docker stop web-tool-test && docker rm web-tool-test
```

- [ ] **Step 7: Commit**

```bash
git add Dockerfile
git commit -m "feat: multi-stage Dockerfile — reduces image from 1.53GB to ~850MB - completes plan item #2

- Split into builder (build-essential, dev headers, uv) and runtime stages
- Runtime image has only libcairo2 + wget, no compiler or dev headers
- Cache-friendly: pyproject.toml + uv.lock copied before source code
- Healthcheck uses wget --spider instead of Python one-liner
- uv binary excluded from runtime image (49.6MB savings)"
```

---

### Task 3: Update TEST_COVERAGE.md if needed

**Files:**
- Modify: `TEST_COVERAGE.md` (only if test count changed)

This task only applies if the previous tasks changed any tests. Since we're only modifying infrastructure files (Dockerfile, .dockerignore), no test changes are expected. Skip this task unless tests were added/modified.

- [ ] **Step 1: Check if any test files changed**

```bash
git diff --name-only main..HEAD -- tests/
```

Expected: No output (no test files changed).

If there are changes, update `TEST_COVERAGE.md` with the new test count and class listings.

- [ ] **Step 2: Skip commit if no test changes**

No commit needed if no test files were modified.
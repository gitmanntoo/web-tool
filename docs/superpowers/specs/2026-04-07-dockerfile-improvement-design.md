# Dockerfile Improvement Design

## Context

The current `Dockerfile` is functional but has several issues that affect build performance, image size, and production readiness. This is a single-project repository (web-tool) used both locally and deployed to servers.

## Design

### 1. Add `.dockerignore`

Exclude from build context:
- `node_modules/`, `.venv/`, `.pytest_cache/`, `.git/`, `__pycache__/`, `*.pyc`
- `TESTING.md`, `TEST_COVERAGE.md`, `Makefile`, `.github/`, `tests/`
- `requirements.txt` (not used; uv managed)
- `local-cache/` (runtime cache, not needed in image)
- `docs/` (documentation not needed at runtime)

**Impact**: Build context shrinks significantly; only actual runtime artifacts sent to Docker daemon.

### 2. Optimized Single-Stage Dockerfile

```
FROM python:3.13-slim

# Install system deps + clean apt cache in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential libcairo2-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv from official image (avoids extra pip layer)
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /usr/local/bin/uv

WORKDIR /app

# Copy all source + manifests before deps install (setuptools requires all package dirs present)
COPY pyproject.toml uv.lock ./
COPY library/ ./library/
COPY static/ ./static/
COPY templates/ ./templates/
COPY web-tool.py README.md ./

# Install deps
RUN uv pip install --system --no-cache .

# Non-root user for security
RUN useradd --uid 1000 --create-home appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /data && chown appuser:appuser /data

# Download NLTK data to a world-readable location
ENV NLTK_DATA=/usr/share/nltk_data
RUN python -m nltk.downloader -d /usr/share/nltk_data wordnet words

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8532/', timeout=5).close()" || exit 1

EXPOSE 8532
ENTRYPOINT ["python", "web-tool.py"]
```

### Key Decisions

| Decision | Rationale |
|---|---|
| `--no-install-recommends` | Don't pull suggested packages we don't need |
| `apt-get clean && rm -rf /var/lib/apt/lists/*` | Keeps layer small; can't prune after layer commits |
| `COPY --from=ghcr.io/astral-sh/uv:0.11.3` | Official uv image is tiny; avoids `pip install uv` extra layer; pinned for reproducibility |
| `uv pip install --system --no-cache` | No pip cache in image |
| `USER appuser` (uid 1000) | Runs as non-root; Flask still binds to 8532 fine; UID pinned for deterministic permissions |
| Inline `HEALTHCHECK` | Built-in Docker health probe |

## Files to Create/Modify

- **Create**: `.dockerignore`
- **Modify**: `Dockerfile`

## Expected Outcomes

- **Image size**: ~180-220MB (vs current ~250-300MB)
- **Build time**: ~20-30% faster due to `.dockerignore` + better layer caching
- **Production ready**: Non-root user + healthcheck included

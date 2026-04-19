# Dockerfile Improvements Design

**Date:** 2026-04-18
**Status:** Approved
**Goal:** Reduce Docker image size, improve security, and improve build cache efficiency

## Current State

- Image size: 1.53GB
- Single-stage build with build-essential and dev headers in runtime image
- uv binary (49.6MB) included at runtime
- Python-based healthcheck
- No cache optimization for dependency installation

## Approach

Multi-stage build separating compile-time dependencies from runtime dependencies.

### Builder Stage

Base: `python:3.14-slim`

1. Install system build dependencies (`build-essential`, `libcairo2-dev`)
2. Copy `uv` binary from `ghcr.io/astral-sh/uv`
3. Copy `pyproject.toml` + `uv.lock` (cache-friendly — code changes don't invalidate pip layer)
4. Copy all source code (setuptools requires all package dirs present)
5. Run `uv pip install --system --no-cache .`
6. Download NLTK data to `/usr/share/nltk_data`

### Runtime Stage

Base: `python:3.14-slim`

1. Install only runtime system deps (`libcairo2`, no `-dev` headers, no `build-essential`)
2. Copy installed Python packages from builder's `site-packages`
3. Copy NLTK data from builder
4. Copy application source code
5. Create non-root user, set permissions
6. Set healthcheck with `wget` (available in slim images, no extra install)
7. Expose 8532, set entrypoint

### Healthcheck

Replace Python one-liner with `wget`:
```
wget -q --spider http://localhost:8532/ || exit 1
```

`--spider` validates the URL responds without downloading the body. `wget` is installed via `apt-get` in the runtime stage (~4MB installed size).

### .dockerignore Updates

Add entries not needed at runtime:
- `specs/` — design/spec documentation
- `.claude/` — Claude Code session files

### Security Improvements

- `libcairo2-dev` removed from runtime (no dev headers)
- `build-essential` removed from runtime (no compiler)
- uv binary removed from runtime (no package manager)
- `--no-install-recommends` on runtime apt-get
- Non-root user preserved

### Layer Ordering

Least-changing layers first, most-changing last:
1. System runtime deps
2. Python packages from builder
3. NLTK data from builder
4. Application source
5. User creation + permissions
6. Healthcheck, EXPOSE, ENTRYPOINT

### Expected Image Size

~800-850MB (down from 1.53GB, ~45% reduction)

| Layer | Current | After |
|-------|---------|-------|
| Base image | ~450MB | ~450MB |
| System deps | 405MB | ~15MB |
| Python deps | 265MB | ~265MB |
| uv binary | 49.6MB | 0MB |
| NLTK data | 22.6MB | ~22MB |
| App source | ~1MB | ~1MB |

### Makefile Impact

None — existing `docker-build`, `docker-buildx`, and `docker-push` targets work as-is.

## Out of Scope

- Alpine-based image (CairoSVG compatibility risks with musl libc)
- CI/CD pipeline changes
- Docker Compose configuration
- Application-level changes
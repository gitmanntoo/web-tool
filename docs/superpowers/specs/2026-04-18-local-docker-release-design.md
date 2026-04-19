# Local Docker Release Workflow Design

**Date:** 2026-04-18  
**Topic:** Replace GitHub Actions with local Docker build/push workflow  
**Status:** Approved for implementation

## Overview

Replace the `.github/workflows/docker.yml` GitHub Actions workflow with local Makefile targets and scripts that handle multi-platform Docker builds, Docker Hub pushes, and README synchronization. Uses git tags for versioning instead of auto-incrementing a VERSION file.

## Goals

- Enable local Docker image builds and pushes without relying on GitHub Actions
- Use git tags for explicit version control (replacing auto-increment VERSION file)
- Maintain multi-platform support (linux/amd64, linux/arm64)
- Automatically sync README.md to Docker Hub description
- Remove CI-based version bump commits

## Architecture

### Version Resolution

Versions are determined at build time using this priority:

1. **Exact git tag** (if current commit is tagged): `v1.0.1` → `1.0.1`
2. **Development build**: `dev-$(git rev-parse --short HEAD)` → e.g., `dev-abc123`

This replaces the auto-increment VERSION file approach.

### Credentials

Docker Hub authentication uses environment variables:

- `DOCKERHUB_USERNAME` — Docker Hub username (e.g., `dockmann`)
- `DOCKERHUB_TOKEN` — Docker Hub access token (create at https://hub.docker.com/settings/security)

These must be set before running release commands.

### Build Process

1. Verify credentials are set
2. Determine version from git state
3. Create buildx builder if needed (for multi-platform)
4. Build and push multi-platform image:
   - `dockmann/web-tool:latest`
   - `dockmann/web-tool:${VERSION}`
5. Update Docker Hub description from README.md via API

## Components

### Makefile Targets

| Target | Purpose |
|--------|---------|
| `make docker-release` | Full release: build, push, update description |
| `make docker-push` | Build and push (update to support versioning) |
| `make docker-describe` | Update Docker Hub description only |

### Docker Hub Description Update

Uses Docker Hub API endpoint:
```
PATCH /v2/repositories/{username}/{repo}/
{
  "full_description": "{README content}"
}
```

Authentication: Basic auth with username/token.

## Workflow

### Release a new version

Two workflows are supported for creating release tags. Both use the same `make docker-release` command.

**Option 1: Local Tagging**

Create and push the tag locally, then build:

```bash
# 1. Set credentials (in ~/.zshrc or export)
export DOCKERHUB_USERNAME=dockmann
export DOCKERHUB_TOKEN=your-token-here

# 2. Create and push a git tag
git tag v1.0.1
git push origin v1.0.1

# 3. Run release (while checked out at the tagged commit)
make docker-release
```

**Option 2: GitHub Releases**

Create a release via the GitHub UI, then build locally:

```bash
# 1. Go to https://github.com/gitmanntoo/web-tool/releases/new
# 2. Click "Choose a tag" → type "v1.0.1" → click "Create new tag"
# 3. Fill in release title and description
# 4. Click "Publish release"

# 5. Pull the new tag locally
git fetch origin --tags

# 6. Check out the tagged commit
git checkout v1.0.1

# 7. Run release
make docker-release
```

**When to use GitHub Releases:**
- Writing release notes in GitHub's UI
- Wanting the tag visible in GitHub releases list
- Separating tagging decision from build process

### Build dev version

```bash
# Builds and pushes as dev-abc123 (short sha)
make docker-release
```

### Update description only

```bash
make docker-describe
```

## Files Changed

- `.github/workflows/docker.yml` — **DELETE** entire workflow
- `Makefile` — **MODIFY** update `docker-push`, add `docker-release`, `docker-describe`
- `VERSION` — **DELETE** (no longer needed)

## Error Handling

- Missing credentials: Fail fast with clear message
- Not at a tagged commit: Use dev- prefix version
- Docker not running: Standard docker error
- Push fails: Standard docker error with buildx context

## Testing

Test scenarios:
1. Run `make docker-release` without credentials → clear error
2. Run `make docker-release` on untagged commit → builds as dev-xxx
3. Run `make docker-release` on tagged commit → builds as tag version
4. Verify Docker Hub description updated → check hub.docker.com

## Backwards Compatibility

- Existing `make docker-build` and `make docker-buildx` remain unchanged
- `make docker-push` behavior enhanced (adds versioned tag)
- Users who relied on VERSION file can use git tags instead

## Security Considerations

- Token should have "Read, Write, Delete" scope (Docker Hub)
- Token stored in environment, not committed
- No secrets in Makefile or scripts

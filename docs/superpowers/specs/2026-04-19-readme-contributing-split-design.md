# README / CONTRIBUTING Split Design

## Context

The web-tool README currently serves two audiences:
1. **Users** — people who install and run web-tool to extract information from web pages
2. **Developers** — people who build, release, and contribute to the project

These audiences have different needs. The README should focus on user-facing content (how to use web-tool), while developer-facing content (building, releasing, dependencies) belongs in a separate document.

## Goals

- README.md contains only user-facing content
- CONTRIBUTING.md contains developer-facing content
- No content is lost or rewritten — purely a separation

## Design

### New File: `CONTRIBUTING.md`

Contains all developer-facing content moved from README:

1. **Building and Publishing** section
   - Prerequisites (Docker, Docker Hub token)
   - Setup instructions
   - Commands table (`make docker-release`, `make docker-push`, `make docker-describe`)
   - Versioning scheme

2. **Release Workflows** section
   - Option 1: Local Tagging (git tag → push → make docker-release)
   - Option 2: GitHub Releases (create release via UI → fetch tag → checkout → make docker-release)

3. **Dependencies** section
   - Full list of Python packages with links

4. **Header** — brief note that this is the developer reference

### Updated `README.md`

Remove developer-facing sections:

- Remove "Building and Publishing" section (lines 148-169)
- Remove "Release Workflows" section (lines 174-215)
- Remove "Dependencies" section (lines 216-227)
- Add a single line at the end: "For development and release instructions, see [CONTRIBUTING.md](CONTRIBUTING.md)."

Retained user-facing sections:

- Header/badges
- Overview and pattern description
- Bookmarklet Endpoints
- Debug Endpoints
- Favicon Cache (user-facing portion — overrides, inline images, adding overrides)
- Running with Docker (user-oriented run instructions)

## Files Changed

| File | Change |
|------|--------|
| `README.md` | Remove developer sections; add CONTRIBUTING.md reference |
| `CONTRIBUTING.md` | New file with developer content moved from README |

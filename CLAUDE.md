# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup & Running
- **Install dependencies**: `make install`
- **Run application**: `make run` (starts the web-tool locally via `uv run python web-tool.py`)
- **Development dependencies**: `make dev`

### Quality & Testing
- **Prerequisite**: Run `make dev` first to install lint/format/test tools (ruff, pytest)
- **Lint code**: `make lint`
- **Format code**: `make format`
- **All quality checks**: `make check` (lint + format + import sorting)
- **Run all tests**: `make test`
- **Run tests with coverage**: `make testcov`
- **Run tests with verbose output**: `make testv`
- **Run a specific test file**: `uv run pytest tests/test_filename.py -v`
- **Run a specific test class**: `uv run pytest tests/test_filename.py::TestClassName -v`

### Docker
- **Run published image**: `make docker-run`
- **Build image**: `make docker-build`
- **Stop container**: `make docker-stop`

### Git Workflow
- **Delete merged branch**: `git branch -d <branch>` (safe delete; use `-D` to force delete unmerged)

## Python Runtime
- **Use `uv run`** for all commands — `pyproject.toml` requires Python 3.13. pytest must be run via `uv run python -m pytest`; using a pyenv-managed Python will fail to find test dependencies.

## Testing
- **Mocking Pillow images:** When mocking `Image.resize`, set `.resize.return_value = mock_img` so callers can chain `.width`/`.height` on the returned image

## Workflow
- **Multi-step implementations:** Use `superpowers:subagent-driven-development` skill. Create tasks with `TaskCreate`, set dependencies, dispatch one `general-purpose` subagent per task.

## Architecture & Project Structure

The `web-tool` is a utility for extracting and processing information from web pages, primarily interacting with the user via browser bookmarklets.

### High-Level Flow
1. **Client-Side**: Bookmarklets (`static/js/*.js`) capture page data and copy it to the clipboard.
2. **Server-Side**: A Flask application (`web-tool.py`) processes the captured data via various endpoints (e.g., `/clip-collector`, `/mirror-clip`).
3. **Processing**: The `library/` directory contains the core logic for HTML parsing, text extraction, and favicon management.

### Key Components
- **Core Application**: `web-tool.py` - The main entry point and Flask server.
- **Logic Library**: `library/` - Contains the business logic, utility functions, and helper classes.
- **Favicon System**: Implements a three-tier cache for favicons:
    1. `static/favicon-overrides.yml` (User Overrides - Highest priority)
    2. `static/favicon.yml` (App Defaults - Medium priority)
    3. `local-cache/favicon.yml` or `/data/favicon.yml` (Auto-discovered - Lowest priority)
- **Static Assets**: `static/` contains JavaScript for bookmarklets, CSS, and favicon configurations.
- **Templates**: `templates/` contains HTML templates for the web interface.
- **Specs**: `specs/` contains permanent page specs (one per web-tool page) and a parent spec documenting shared architecture. See `specs/web-tool-spec.md` for the full index.

### Specs Conventions
- Each web-tool page has a spec at `specs/pages/<name>.md` following the `mirror-links.md` format
- Parent spec at `specs/web-tool-spec.md` documents shared patterns (clipboard flow, favicon cache, `plain_text_response`)
- When modifying a page: update its spec first. When adding a page: create its spec first
- **Any change that conflicts with or contradicts an existing spec must be explicitly approved by the user before proceeding**

### Known Bug Patterns
- `buildWikiLink`/`buildSimpleLink` in `mirror-links.html` require `escapeHtml(url)` — URLs are inserted into innerHTML and must be escaped
- `buildHtmlLink` uses `favH`/`favW` (the local const aliases, not the outer parameter names)
- Template domain extraction must use backend-computed `override_domain`/`override_path_scope` — string-splitting on `/` reverses the TLD

### Technical Stack
- **Backend**: Python 3.13, Flask
- **HTML Parsing**: BeautifulSoup4, lxml
- **Image/SVG Processing**: CairoSVG, Pillow, Magika
- **Text Processing**: NLTK, anyascii
- **Package Management**: `uv`
- **Linting/Formatting**: Ruff
- **Testing**: coverage.py (via `make testcov`)

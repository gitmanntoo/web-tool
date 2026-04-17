# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup & Running
- **Install dependencies**: `make install`
- **Run application**: `make run` (starts the web-tool locally via `uv run python web-tool.py`)
- **Development dependencies**: `make dev`

### Quality & Testing
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
- **Use `uv run`** for all commands — `pyproject.toml` requires Python 3.14 only (`>=3.14,<3.15`). Using a pyenv-managed Python will fail to find test dependencies.
- **Dev deps required:** Run `make dev` before `make test` or `uv run python -m pytest` — pytest/ruff are dev dependencies, not installed by `make install`

## Module Packaging
- **New Python packages:** When adding new packages (e.g., `routes/`), update both `Dockerfile` (COPY command) and `pyproject.toml` (`packages` list in `[tool.setuptools]`)

## Template Security
- **XSS prevention:** Use `|e` filter for HTML context, `|tojson` filter for JavaScript context when rendering user-controlled data in templates

## URL Parsing
- **Schemeless URLs:** `urlparse()` treats schemeless inputs as paths; handle by reparsing with `//` prefix when `netloc` is empty and scheme is missing

## PR Review Comments
- **View Copilot comments:** `gh api repos/<owner>/<repo>/pulls/<num>/comments` — addresses these before merge

## Testing
- **Mocking Pillow images:** When mocking `Image.resize`, set `.resize.return_value = mock_img` so callers can chain `.width`/`.height` on the returned image
- **Doc sync:** When adding/removing test files or test classes, update `TESTING.md` and `TEST_COVERAGE.md` in the same commit or a follow-up — update both test count totals and list new classes
- **Unused variables:** Run `ruff check --select F841` before committing; unused assignments in tests often indicate incomplete assertions
- **Test pattern consistency:** When adding paired tests (e.g., ICO/SVG variants), match the existing test's structure exactly — don't assign `result` if sibling test doesn't use it
- **Test count tracking:** Total test count is tracked in `TEST_COVERAGE.md` — update when adding tests (current: 328)
- **JS template testing:** Template rendering tests (`test_js_escaping.py`) verify JS variable names and structure in rendered output, but cannot catch runtime ReferenceErrors — use Playwright/browser testing for JS runtime bugs

## Workflow
- **Multi-step implementations:** Use `superpowers:subagent-driven-development` skill. Create tasks with `TaskCreate`, set dependencies, dispatch one `general-purpose` subagent per task.

## Architecture & Project Structure

The `web-tool` is a utility for extracting and processing information from web pages, primarily interacting with the user via browser bookmarklets.

### High-Level Flow
1. **Client-Side**: Bookmarklets capture page data and copy it to the clipboard. Bookmarklet JS is served dynamically via `/js/<name>.js`.
2. **Server-Side**: A Flask application (`web-tool.py`) processes the captured data via various endpoints (e.g., `/clip-collector`, `/mirror-clip`).
3. **Processing**: The `library/` directory contains the core logic for HTML parsing, text extraction, and favicon management.

### Key Components
- **Core Application**: `web-tool.py` - The main entry point and Flask server. Registers blueprints from `routes/` (`mirror_links`, `mirror_favicons`, `javascript`, `debug`).
- **Logic Library**: `library/` — `util.py` (PageMetadata, MirrorData, TitleVariants, ClipCache), `html_util.py` (favicon system, link parsing), `text_util.py` (NLP extraction), `text_format.py` (ascii_text, html_text, path_safe_filename), `title_variants.py` (deduplicate_variants), `url_util.py` (URL parsing, fetching), `img_util.py` (ICO/SVG conversion), `unicode_util.py` (category names), `content_type.py` (MIME type detection), `fragment_handlers.py` (anchor/heading fragment resolution), `docker_util.py` (container detection)
- **Favicon System**: Implements a three-tier cache for favicons:
    1. `static/favicon-overrides.yml` (User Overrides - Highest priority)
    2. `static/favicon.yml` (App Defaults - Medium priority)
    3. `local-cache/favicon.yml` or `/data/favicon.yml` (Auto-discovered - Lowest priority)
- **Static Assets**: `static/` contains CSS and favicon YAML configs. Bookmarklet JS is served dynamically via `/js/<name>.js` from `mirror.js` in templates; only `inline-image.js` and `paste-favicon.js` live in `static/js/`.
- **Templates**: `templates/` — key templates: `mirror-links.html` (link generation), `mirror-favicons.html` (favicon management), `plain_text.html` (auto-copy wrapper), `clip-proxy.html` (container clipboard bridge)
- **Specs**: `specs/` contains 17 page specs and a parent spec. See `specs/web-tool-spec.md` for the full index.

### Specs Conventions
- Each web-tool page has a spec at `specs/pages/<name>.md` following the `mirror-links.md` format
- Parent spec at `specs/web-tool-spec.md` documents shared patterns (clipboard flow, favicon cache, `plain_text_response`)
- When modifying a page: update its spec first. When adding a page: create its spec first
- **Any change that conflicts with or contradicts an existing spec must be explicitly approved by the user before proceeding**
- **Spec template:** Copy `specs/pages/mirror-links.md` when creating new page specs

### Known Bug Patterns
- `buildWikiLink`/`buildSimpleLink` in `mirror-links.html` require `escapeHtml(url)` — URLs are inserted into innerHTML and must be escaped
- `buildHtmlLink` uses `favH`/`favW` (the local const aliases, not the outer parameter names)
- Template domain extraction must use backend-computed `override_domain`/`override_path_scope` — string-splitting on `/` reverses the TLD
- Walrus operator precedence: `(t := resp.get_type()) != "image/svg"` — parentheses required around walrus assignment before comparison

### Technical Stack
- **Backend**: Python 3.14, Flask
- **HTML Parsing**: BeautifulSoup4, lxml
- **Image/SVG Processing**: CairoSVG, Pillow, Magika, PyMuPDF
- **Text Processing**: NLTK, anyascii
- **JS Processing**: jsmin, esprima (bookmarklet minification and parsing)
- **URL Handling**: urllib.parse (URL parsing), requests (HTTP fetching)
- **Package Management**: `uv`
- **Linting/Formatting**: Ruff
- **Testing**: coverage.py (via `make testcov`)

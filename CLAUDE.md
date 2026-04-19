# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow Preferences

### Implementation Plans

**Always create an implementation plan before making changes if one does not exist.**

For any non-trivial task, create a plan using any available mechanism (`TaskCreate`, `superpowers:writing-plans` skill, `superpowers:feature-dev` skill, or manual planning). Then:

1. Mark plan items as `in_progress` when starting work on them
2. Mark plan items as `completed` when finished
3. Create corresponding git commits to track progress

**Commit linkage:** Each git commit message should reference the plan item it completes (e.g., "feat: add error handling for edge cases - completes plan item #3").

This ensures:
- Clear visibility into what was done and what's remaining
- Git history that maps directly to the implementation plan
- Easy to resume work if interrupted

### Coding Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

#### 1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:
- State assumptions explicitly. If uncertain, ask.
- If multiple valid approaches exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

#### 2. Simplicity First

Write the minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Ask: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

#### 3. Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

**The test:** Every changed line should trace directly to the user's request.

#### 4. Goal-Driven Execution

Define success criteria. Loop until verified.

Transform vague tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]

Strong success criteria enable independent progress. Weak criteria ("make it work") require constant clarification.

#### 5. Testable Code

Write code that can be tested without external dependencies.

- **Isolate side effects** — I/O, network calls, and external services should be behind interfaces that can be mocked or stubbed.
- **Avoid global state** — Functions should receive dependencies as parameters, not reach for globals.
- **Prefer pure functions** — Given the same inputs, always return the same outputs with no side effects. Easiest to test.
- **Don't test through the database** — Business logic shouldn't require a running database to verify.
- **Constructor injection over service locators** — Explicit dependencies are clearer and easier to fake.

**The test:** Can you run the test suite offline? If not, the code is too coupled.

#### 6. Stay Focused

Keep work narrowly scoped to the current task. Resist the urge to improve adjacent code.

- **Don't simplify existing code** just because you notice it could be shorter or clearer.
- **Don't refactor** unless it's directly required to implement the requested change.
- **Don't improve** variable names, comments, or formatting in code you aren't otherwise touching.
- **If you discover issues** — bugs, security holes, or needed improvements — surface them to the user immediately, then ask:
  - Address now?
  - Add to ISSUES.md for later?
  - Ignore for now?
- **Don't fix pre-existing bugs** you encounter unless the user explicitly says yes.

**The test:** After completing the task, only the lines directly related to the request should have changed. If you "couldn't help but notice" something and fixed it, you went too far.

### Pull Request Discipline

**Never create a pull request without asking the user first.**

- Do not run `gh pr create` or equivalent commands unless explicitly instructed.
- Do not push branches to remote without confirmation.
- When work is complete, present a summary and ask: "Ready to create a PR?" or "Shall I push this branch?"
- Wait for explicit user approval before creating PRs, pushing branches, or opening GitHub/Merge requests.

This prevents surprise PRs and ensures the user controls when and how their work is shared.

#### 7. Test Documentation

When writing tests, always add a comment describing what the test does and why it is important.

- **Describe the behavior being tested** — What specific scenario or edge case does this cover?
- **Explain the importance** — Why does this test matter? What would break if this behavior changed?
- **Keep it concise** — One or two sentences is usually sufficient.
- **Update comments when tests change** — Ensure the description stays accurate.

**The test:** Can someone reading the test file understand the intent without reading the implementation?

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
- **Build multi-platform**: `make docker-buildx`
- **Push to registry**: `make docker-push` (requires DOCKERHUB_USERNAME/TOKEN env vars)
- **Full release**: `make docker-release` (build, push, update description)
- **Update description**: `make docker-describe` (sync README to Docker Hub)
- **Stop container**: `make docker-stop`
- **Clean build cache**: `make docker-clean` (stop container and prune buildx cache)

**Docker Release Patterns:**
- **Version from git tag**: Use `VERSION =` (lazy, not `:=`) to avoid running git on non-docker targets; include `dev` fallback for non-git contexts
- **Shell pipeline gotcha**: `cmd | sed ... || fallback` won't trigger fallback on first command failure because pipelines return the last command's exit code; use variable storage first: `var=$$(cmd) && echo "$$var" | sed ... || fallback`
- **docker-describe hardening (recommended for future Makefile updates)**: Current `make docker-describe` still uses `curl -u`, `sed` escaping, and `curl -s | grep`; prefer the safer patterns below when updating it
- **Docker Hub API auth**: Use `curl --netrc-file` with temp file + `umask 077` + `trap` cleanup — `curl -u` leaks credentials via argv (visible in `ps`)
- **JSON payloads in Make**: Use `python3 -c 'import json; print(json.dumps(...))'` — `sed` doesn't escape backslashes, producing invalid JSON
- **curl failure propagation**: Use `curl -fsS` (fail on HTTP errors) with explicit `exit 1` — `curl | grep` pattern exits 0 on failure
- **Repo variable**: Define `DOCKER_REPO` once, derive `DOCKER_IMAGE = $(DOCKER_REPO):latest` — avoids hardcoded repo name drift between `:latest` and version tags
- **Two tagging workflows**: (1) Local: `git tag && git push && make docker-release`; (2) GitHub Releases: create via UI → `git fetch origin --tags` → `git checkout` → `make docker-release`

### Git Workflow

#### Branch Verification Check
- **Always verify branch before committing** — run `git branch --show-current` after subagent work completes
- **Subagents may not respect branch rules** — the parent session must enforce branch discipline
- **If on main/master/develop/trunk after subagent work**: stop and create feature branch before proceeding

- **Delete merged branch**: `git branch -d <branch>` (safe delete; use `-D` to force delete unmerged)
- **Feature branches**: Never commit directly to `main`/`master` — always create feature branch first
- **Style hygiene**: Move inline styles to CSS classes; use existing design tokens before creating new ones
- **Worktrees:** Use `git worktree add .worktrees/<branch> -b <branch>` for isolated feature work. Always run `make dev` and `make test` in the worktree before dispatching subagents. Verify with `git worktree list` to confirm active worktrees.

## Python Runtime
- **Use `uv run`** for all commands — `pyproject.toml` requires Python 3.14 only (`>=3.14,<3.15`). Using a pyenv-managed Python will fail to find test dependencies.
- **Dev deps required:** Run `make dev` before `make test` or `uv run python -m pytest` — pytest/ruff are dev dependencies, not installed by `make install`

## Python Version Upgrades
- **Hard cutover:** Update `requires-python`, ruff `target-version`, Dockerfile base image, `.python-version`, and docs together
- **PEP 649:** Python 3.14+ supports unquoted forward references; ruff `py314` target flags quoted annotations as unnecessary

## Type Annotations
- Use `Type | None` for optional/nullable fields (e.g., `parent: SoupElem | None` when None is passed)
- Unquote forward references when upgrading to Python 3.14+ (PEP 649 deferred evaluation)

## Module Packaging
- **New Python packages:** When adding new packages (e.g., `routes/`), update both `Dockerfile` (COPY command) and `pyproject.toml` (`packages` list in `[tool.setuptools]`)

## Template Security
- **XSS prevention:** Use `|e` filter for HTML context, `|tojson` filter for JavaScript context when rendering user-controlled data in templates

## CSS Design System
- **Tokens:** Use CSS custom properties (`--color-*`, `--space-*`, `--font-size-*`) from `static/mirror.css`
- **Fluid widths:** Use `width: clamp(min, preferred%, max)` instead of media queries for responsive containers
- **Components:** Prefer semantic classes (`.panel`, `.variant-row`, `.btn-copy`) over inline styles
- **Tooltip positioning:** Add `window.scrollX/Y` to `getBoundingClientRect()` coords for accurate placement
- **Long metadata strings:** Add `word-wrap: break-word` to any text container that may hold long unbreakable strings (cookie strings, base64, URLs)

## Shared JavaScript
- **tooltip.js:** Shared `showTooltip()` and `attachCopyListeners()` functions — import in templates with `<script src="/static/js/tooltip.js">`
- **Paste handlers:** Use `document.body.querySelector()` for tooltip cleanup (tooltips appended to body, not trigger element)

## URL Parsing
- **Schemeless URLs:** `urlparse()` treats schemeless inputs as paths; handle by reparsing with `//` prefix when `netloc` is empty and scheme is missing

## PR Review Comments
- **Check before addressing:** When asked to address PR comments, first run `gh pr view <num> --json state,headRefName` to verify the PR isn't merged or the branch doesn't already contain the fixes
- **View all PR details:** `gh pr view <num> --json body,comments --jq '.'` shows body + all comments in one command
- **View Copilot comments:** `gh api repos/<owner>/<repo>/pulls/<num>/comments` — addresses these before merge

## Documentation
- Keep CONTRIBUTING.md dependency versions in sync with pyproject.toml constraints

## Superpowers Plans and Specs

**Attach to PR comments, don't commit.** When superpowers plans and specs are created for a PR:
1. Write the files to `docs/superpowers/plans/` and `docs/superpowers/specs/` as local untracked files (not committed to git)
2. Attach the files directly to the PR comment using GitHub's file attachment feature — this keeps docs alongside the PR for reviewer context without adding commit noise
3. Delete local untracked copies after the PR is merged or closed

## Testing
- **Mocking Pillow images:** When mocking `Image.resize`, set `.resize.return_value = mock_img` so callers can chain `.width`/`.height` on the returned image
- **Unused variables:** Run `ruff check --select F841` before committing; unused assignments in tests often indicate incomplete assertions
- **Test pattern consistency:** When adding paired tests (e.g., ICO/SVG variants), match the existing test's structure exactly — don't assign `result` if sibling test doesn't use it
- **JS template testing:** Template rendering tests (`test_js_escaping.py`) verify JS variable names and structure in rendered output, but cannot catch runtime ReferenceErrors — use Playwright/browser testing for JS runtime bugs

## Workflow
- **Multi-step implementations:** Use `superpowers:subagent-driven-development` skill. Create tasks with `TaskCreate`, set dependencies, dispatch one `general-purpose` subagent per task.
- **Code reviews:** Score issues 0-100 for confidence; only report issues ≥80 to minimize false positives

## Architecture & Project Structure

The `web-tool` is a utility for extracting and processing information from web pages, primarily interacting with the user via browser bookmarklets.

### High-Level Flow
1. **Client-Side**: Bookmarklets capture page data and copy it to the clipboard. Bookmarklet JS is served dynamically via `/js/<name>.js`.
2. **Server-Side**: A Flask application (`web-tool.py`) processes the captured data via various endpoints (e.g., `/clip-collector`, `/mirror-clip`).
3. **Processing**: The `library/` directory contains the core logic for HTML parsing, text extraction, and favicon management.

### Key Components
- **Core Application**: `web-tool.py` - The main entry point and Flask server. Registers blueprints from `routes/` (`mirror_links`, `mirror_favicons`, `javascript`, `debug`).
- **Logic Library**: `library/` — Core modules:
  - `util.py` (PageMetadata, MirrorData, TitleVariants, ClipCache)
  - `html_util.py` (favicon system, link parsing)
  - `text_util.py` (NLP extraction)
  - `text_format.py` (ascii_text, html_text, path_safe_filename)
  - `title_variants.py` (deduplicate_variants)
  - `url_util.py` (URL parsing, fetching)
  - `img_util.py` (ICO/SVG conversion)
  - `unicode_util.py` (category names)
  - `content_type.py` (MIME type detection)
  - `fragment_handlers.py` (anchor/heading fragment resolution)
  - `docker_util.py` (container detection)
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
- **Dynamic radio buttons:** `querySelectorAll` at `DOMContentLoaded` misses elements added later. Use event delegation on a parent container that exists at load time (e.g., `#favicon-options`) for dynamically added radio/checkbox groups

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

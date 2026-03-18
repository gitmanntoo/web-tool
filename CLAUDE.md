# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Web-tool is a Flask-based utility service that extracts information from web pages through browser bookmarklets. It runs on port 8532 by default and provides endpoints for content extraction, transformation, and caching.

## Common Commands

### Development

```bash
# Install dependencies (uses uv)
uv pip install -e ".[dev]"

# Run the application locally
uv run python web-tool.py

# Run with Docker
docker run -d --restart always -p 8532:8532 -v $(pwd)/web-tool:/data --name web-tool dockmann/web-tool
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_title_variants.py -v

# Run specific test class
uv run pytest tests/test_title_variants.py::TestAsciiAndEmojis -v

# Run with coverage
uv run pytest tests/ --cov=library --cov-report=html

# Run tests matching a pattern
uv run pytest -k "emoji" -v
```

### Code Quality

```bash
# Format code with ruff
make format

# Run ruff linting
make lint

# Run all quality checks
make check

# Clean temporary files
make clean
```

## Architecture

### Core Pattern: Capture-and-Process

The application follows a bookmarklet-driven workflow:

1. **Capture Phase**: Browser bookmarklets capture page metadata (URL, title, HTML) via JavaScript
2. **Transmission Phase**: Large data is split into chunks and sent to clipboard collection endpoints
3. **Processing Phase**: Server endpoints retrieve and process data from the clipboard cache
4. **Output Phase**: Results are returned in multiple formats (HTML, JSON, plain text)

### Clipboard System

A batch-based cache handles large payloads that exceed clipboard limits:

- **POST /clip-collector**: Receives numbered chunks with a batchId UUID
- **GET /mirror-clip**: Reconstructs full clipboard from cached chunks
- **TTL**: 10 minutes (`CLIP_CACHE_TTL_SECONDS`)
- **Limits**: 100 batches max, memory-capped at 50% of available RAM
- **Container vs Local**: In containers, uses proxy-based clipboard access; locally uses `pyperclip`

### Text Extraction Pipeline

Two extraction methods are available:

1. **NLP-based** (`/mirror-text`): Uses NLTK to intelligently filter content, includes script tags with readable text, removes boilerplate via word/token analysis
2. **Simple** (`/mirror-soup-text`): Uses BeautifulSoup's `get_text()`, excludes script/style tags, faster but less comprehensive

### Favicon Cache System

Three-tier hierarchical lookup (highest to lowest priority):

1. **User Overrides** (`static/favicon-overrides.yml`): Manual customizations
2. **App Defaults** (`static/favicon.yml`): Distributed defaults
3. **Auto-Discovered** (`local-cache/favicon.yml` or `/data/favicon.yml` in container): Dynamically cached

**Cache Key Rules**:
- Domain-only: `example.com` applies to all pages on domain
- Path-specific: `example.com/docs` applies to specific sections
- `www.` prefix is normalized away
- More specific keys take precedence

### Key Modules

| Module | Purpose |
|--------|---------|
| `web-tool.py` | Flask application with all endpoints |
| `library/util.py` | PageMetadata, MirrorData, TitleVariants, clipboard cache |
| `library/text_util.py` | NLP-based text extraction, content filtering |
| `library/html_util.py` | Favicon discovery, HTML parsing, cache management |
| `library/url_util.py` | URL fetching, parsing, image size detection |
| `library/img_util.py` | ICO/SVG to PNG conversion |
| `library/unicode_util.py` | ASCII conversion, emoji handling, path-safe filenames |
| `library/docker_util.py` | Container detection |

### Title Variant Generation

The `TitleVariants` class generates four variants for each page title:

- **Original**: Unchanged
- **ASCII + Emoji**: Unicode converted to ASCII, emojis preserved
- **ASCII Only**: Full ASCII conversion (emojis → text equivalents)
- **Path Safe**: Valid filename (invalid chars removed, unicode converted)

### URL Variant Generation

Pages generate multiple URL variants for different use cases:

- **Original**: Full URL with query string
- **With Fragment**: Includes anchor hash
- **Clean**: No query string or fragment
- **Root**: First path segment only
- **Host**: Domain and protocol only

### Fragment Text Extraction

When URLs contain fragments (`#anchor`), the system attempts to find associated content through multiple strategies: heading elements with matching IDs, anchor tags inside headings, wrapper sections, sibling headings, etc.

## Key Dependencies

- **BeautifulSoup**: HTML parsing
- **NLTK**: Natural language processing for intelligent text filtering
- **Magika**: Content type detection for text filtering
- **CairoSVG/Pillow**: Image conversion (ICO/SVG → PNG)
- **Flask/Jinja2**: Web framework and templating
- **pyperclip**: Local clipboard access (non-container only)

## Constraints

- **Python Version**: Strictly 3.11 (not 3.12)
- **Line Length**: 100 characters (ruff configuration)
- **Test Coverage Target**: 80%+ for new features

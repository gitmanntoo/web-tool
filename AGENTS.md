# Repository Guidelines

## Project Overview

This Flask-based web tool extracts information from web pages via bookmarklets. The application runs on port 8532 and includes utilities for extracting links, favicons, text, HTML source, and other page metadata.

## Project Structure

```
web-tool/
├── library/              # Python source modules (core logic)
│   ├── util.py          # General utility functions
│   ├── text_util.py     # Text extraction and processing
│   ├── html_util.py     # HTML parsing and manipulation
│   ├── url_util.py      # URL processing
│   ├── unicode_util.py  # Unicode handling and ASCII conversion
│   ├── img_util.py      # Image processing
│   └── docker_util.py   # Docker-related utilities
├── templates/            # HTML templates for web interface
│   ├── *.html           # Page templates
│   ├── mirror.js        # JavaScript for bookmarklets
│   └── *.css            # Stylesheets
├── static/               # Static assets
│   ├── *.css            # Global styles
│   ├── prism*.js        # Syntax highlighting
│   ├── favicon.yml      # Default favicon mappings
│   ├── favicon-overrides.yml  # User-defined overrides
│   └── *.png            # Images
├── tests/                # Pytest test files
│   └── test_*.py        # Test suites
├── web-tool.py           # Flask application entry point
├── Dockerfile            # Docker container definition
├── pyproject.toml        # Python project dependencies
├── pytest.ini            # Pytest configuration
└── run-it.sh             # Local development script
```

## Build, Test, and Development Commands

### Installation

```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Or install test dependencies only
uv pip install pytest pytest-cov
```

### Running the Application

```bash
# Local development (uses uv and local cache)
./run-it.sh

# With Docker
docker pull dockmann/web-tool
docker run -d --restart always -p 8532:8532 -v $(pwd)/web-tool:/data --name web-tool dockmann/web-tool
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_title_variants.py -v

# Run with coverage
uv run pytest tests/ --cov=library --cov-report=html

# Run specific test class
uv run pytest tests/test_title_variants.py::TestAsciiAndEmojis -v
```

## Coding Style & Conventions

### Python Style

- **Indentation**: 4 spaces (no tabs)
- **Python Version**: 3.11 only (no 3.12)
- **Docstrings**: Use triple-quoted strings with descriptive content
- **Module Imports**: Import only what's needed from library modules
- **Naming**:
  - Modules: lowercase with underscores (e.g., `text_util.py`)
  - Functions: lowercase with underscores (e.g., `text_with_ascii_and_emojis()`)
  - Classes: `CamelCase` (e.g., `TitleVariants`)
  - Constants: `UPPER_SNAKE_CASE` (if applicable)

### HTML/CSS/JavaScript Style

- **HTML**: Semantic markup with proper indentation
- **CSS**: Use classes and maintain consistency with existing stylesheets
- **JavaScript**: Keep bookmarklet code clean and minimal

### Code Organization

- Place utility functions in `library/util.py` unless a more specific module exists
- HTML templates in `templates/` with descriptive filenames
- Static assets in `static/` organized by type

## Testing Guidelines

### Testing Framework

- **pytest** for all tests
- Tests organized in `tests/` directory
- Test discovery patterns: `test_*.py`, `Test*` classes, `test_*` functions

### Test Structure

```python
# tests/test_feature.py
import pytest
from library.module import function_under_test


class TestFeatureName:
    """Tests for module.feature_name function."""
    
    def test_basic_functionality(self):
        """Description of what this test verifies."""
        assert function_under_test() == expected_value
```

### Test Naming

- Use descriptive names: `test_unicode_converted_to_ascii`
- Include docstrings for each test
- Group related tests in test classes

### Coverage Requirements

- Target 80%+ code coverage for new features
- Run coverage reports: `uv run pytest --cov=library`

## Commit & Pull Request Guidelines

### Commit Message Format

Use imperative mood and descriptive language:

```
Add <feature>
Fix <issue>
Enhance <component>
Remove <deprecated feature>
```

**Examples**:
- `Add debug endpoint for testing title variants`
- `Enhance mirror-favicons with cache visibility`
- `Fix missing favicon for pdf documents`

### Pull Request Requirements

- Clear description of changes
- Reference related issues or commit messages
- Tests for new features (add to appropriate test file)
- No unrelated changes in the same PR
- Pass all tests before requesting review

## Configuration Files

### favicon-overrides.yml

Edit this file for user-specific favicon overrides:

```yaml
# Domain-level override
example.com: https://example.com/favicon.ico

# Path-level override
example.com/docs: https://example.com/custom-favicon.png
```

### Static Assets

Changes to templates, CSS, or JavaScript require:

1. Updates in `templates/` or `static/`
2. Refresh browser cache when testing
3. Consider favicon cache invalidation if updating default mappings

## Linting and Formatting

This project uses **ruff** for code formatting and linting.

### Running Formatters and Linters

Use the Makefile for convenience:

```bash
# Format Python code
make format

# Run all linting checks
make lint

# Run all quality checks (linting + formatting)
make check
```

### Using Makefile Commands

The Makefile provides a comprehensive set of commands:

```bash
# Show available commands
make

# Install with all dependencies
make install

# Install development dependencies
make dev

# Run tests
make test
make testcov   # With coverage report
make testv     # With verbose output

# Clean temporary files
make clean

# Run the application
make run

# Build Docker image
make docker
```

### Manual Commands

```bash
# Format with ruff
ruff format library/ tests/

# Check with ruff
ruff check library/ tests/

# Fix auto-fixable issues
ruff check --fix library/ tests/

# Sort imports
ruff check --select I --fix library/ tests/
```

### Configuration Files

- **pyproject.toml**: Contains ruff configuration under `[tool.ruff]`

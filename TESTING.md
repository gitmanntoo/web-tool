# Testing Guide for web-tool

## Overview

This project uses **pytest** as the testing framework with tests organized in a dedicated `tests/` directory, following Python best practices.

## Directory Structure

```
web-tool/
├── tests/
│   ├── __init__.py
│   ├── test_docker_util.py         # Tests for Docker detection
│   ├── test_fragment_variants.py   # Tests for fragment variant duplicate detection
│   ├── test_favicon_validation.py # Tests for favicon validation (get_valid_favicon_links)
│   ├── test_html_util.py          # Tests for HTML parsing and favicon discovery
│   ├── test_img_util.py           # Tests for image conversion
│   ├── test_js_escaping.py        # Tests for JavaScript string escaping in templates
│   ├── test_text_util.py          # Tests for text utilities
│   ├── test_title_strings.py      # Test data for title variants
│   ├── test_title_variants.py     # Tests for title variant generation
│   ├── test_unicode_util.py       # Tests for Unicode utilities
│   ├── test_url_decoding.py       # Tests for URL encoding/decoding
│   └── test_url_util.py           # Tests for URL utilities
├── pytest.ini                      # Pytest configuration
├── pyproject.toml                  # Project configuration with test dependencies
└── [old test files - deprecated]
    ├── test_title_variants.py      # Deprecated - see tests/
    └── test_title_strings.py       # Deprecated - see tests/
```

## Installation

### Install Testing Dependencies with uv

```bash
# Install the package with development dependencies
uv pip install -e ".[dev]"

# Or just install test dependencies
uv pip install pytest pytest-cov
```

## Running Tests

### Run All Tests
```bash
# Using uv
uv run pytest

# Or directly if pytest is already installed
pytest
```

### Run Specific Test File
```bash
uv run pytest tests/test_title_variants.py -v
```

### Run Specific Test Class
```bash
uv run pytest tests/test_title_variants.py::TestAsciiAndEmojis -v
```

### Run Tests Matching a Pattern
```bash
uv run pytest -k "emoji" -v
```

### Run with Coverage Report
```bash
uv run pytest tests/ --cov=library --cov-report=html
```

### Run with Verbose Output
```bash
uv run pytest tests/ -vv
```

### Stop on First Failure
```bash
uv run pytest tests/ -x
```

## Test Organization

### Test Classes

#### `TestAsciiAndEmojis` (10 tests)
Tests for `text_with_ascii_and_emojis()` function:
- Pure ASCII text passthrough
- Emoji preservation
- Unicode accent conversion
- Mixed content handling

#### `TestAsciiOnly` (5 tests)
Tests for `text_ascii_only()` function:
- Pure ASCII output
- Emoji removal
- Unicode conversion to ASCII

#### `TestPathSafeFilename` (13 tests)
Tests for `path_safe_filename()` function:
- Invalid character removal/replacement
- OS-specific character handling (Windows, macOS, Linux)
- Edge cases (empty input, long strings)
- Realistic scenarios (URLs, emails, document names)

#### `TestTitleVariants` (7 tests)
Tests for `TitleVariants` class:
- All four variants generation
- Consistency across variants
- Type checking

#### `TestEdgeCases` (5 tests)
Edge case testing:
- Empty and whitespace input
- Combining diacriticals
- Very long strings
- Special characters and newlines

#### `TestFragmentVariants` (8 tests)
Tests for fragment variant generation in mirror-links endpoint:
- None option is never marked duplicate
- Fragment Text is marked duplicate when equal to Fragment (fallback case)
- Fragment Text is not duplicate when different from Fragment
- All three options present with correct values
- Empty fragment/text case handled correctly
- Pydantic-style URLs (fragment_text equals fragment) detected

#### `TestGetValidFaviconLinks` (6 tests)
Tests for `get_valid_favicon_links()` function in `html_util.py`:
- Returns only validated links (filters out broken favicon URLs)
- Returns empty list when no valid favicons found
- Passes `max_count` and `favicon_height` parameters correctly
- Composes `get_favicon_links`, `sort_favicon_links`, and `validate_top_candidates`

#### `TestValidateTopCandidates` (3 tests)
Tests for `validate_top_candidates()` function:
- Returns empty list for empty input
- Returns single valid link
- Returns multiple valid links up to max_count

#### `TestPageMetadataUrlDecoding` (6 tests)
Tests for URL decoding in `PageMetadata`:
- URL with fragment containing dots is properly decoded
- URL without fragment is decoded
- URL with query string is decoded
- URL with `%23` (encoded `#`) is decoded to `#`
- Already-decoded URLs pass through unchanged
- Empty URL handled gracefully

#### `TestMirrorLinksJsEscaping` (7 tests)
Tests for JavaScript string escaping in `mirror-links.html` template:
- Fragment text with newlines properly escaped (using `|tojson`)
- Fragment text with special characters (quotes) escaped
- Title with Unicode characters escaped
- URL with fragment containing dots rendered correctly
- Empty fragment renders empty string for `fragmentText`
- Null favicon renders as `null` in JavaScript
- Favicon URL renders as JavaScript string

## Test Data

Test strings covering various scenarios are available in `tests/test_title_strings.py`:
- Pure ASCII
- Unicode (multiple languages: Russian, Chinese, Japanese, Korean, Hindi, Arabic, Greek, Hebrew)
- Emoji (individual, sequences, with skin tone modifiers)
- Mixed combinations
- Edge cases (empty, whitespace, control characters)

### Using Test Data

```python
from tests.test_title_strings import TEST_TITLES

for title in TEST_TITLES:
    # Use title in tests or demonstrations
    print(title)
```

## Configuration

### pytest.ini

The `pytest.ini` file configures:
- Test discovery patterns
- Test paths
- Output formatting
- Test markers for organizing tests
- Default command-line options

### pyproject.toml

Development dependencies are defined in `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    "ipykernel>=6.29.5",
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
]
```

## Best Practices

1. **Run tests before committing**: Ensure all tests pass
   ```bash
   uv run pytest
   ```

2. **Write tests for new features**: Add tests to appropriate class in `tests/test_title_variants.py`

3. **Use descriptive test names**: `test_unicode_converted_to_ascii` is better than `test_unicode`

4. **Group related tests**: Use test classes to organize related test functions

5. **Test edge cases**: Empty strings, very long strings, special characters

6. **Use markers for categorization**: Mark slow tests, integration tests, etc.
   ```python
   @pytest.mark.slow
   def test_very_long_title():
       ...
   ```

7. **Keep tests independent**: Each test should be able to run in isolation

8. **Mock clipboard access**: Tests that instantiate `PageMetadata` should patch `pyperclip.paste` to avoid environment-dependent failures:
   ```python
   from unittest.mock import patch

   @patch("pyperclip.paste")
   def test_url_decoding(self, mock_paste):
       mock_paste.return_value = ""
       # ... test code
   ```

## Common Issues

### Import Errors

If you get import errors when running tests, ensure you're running from the project root:
```bash
cd /Users/keith/github/gitmanntoo/web-tool
uv run pytest tests/
```

### Deprecated Test Files

The old test files (`test_title_variants.py` and `test_title_strings.py` in the root directory) are deprecated. Use the versions in the `tests/` directory instead.

To remove the deprecated files:
```bash
rm test_title_variants.py test_title_strings.py
```

## Adding New Tests

1. **Create test file** (if needed): `tests/test_feature.py`

2. **Define test class**: Group related tests
   ```python
   class TestNewFeature:
       def test_basic_functionality(self):
           assert function_under_test() == expected_value
   ```

3. **Use descriptive assertions**:
   ```python
   # Good
   assert result == "expected", f"Expected 'expected', got {result!r}"
   
   # Less good
   assert result == "expected"
   ```

4. **Run tests frequently**:
   ```bash
   uv run pytest tests/test_feature.py -v
   ```

## Continuous Integration

For CI/CD pipelines, use:
```bash
uv pip install -e ".[dev]"
uv run pytest tests/ --cov=library --cov-report=xml
```

## Manual/Integration Testing

Some edge cases require end-to-end testing via the browser bookmarklet since unit tests cannot fully capture the clipboard/bookmarklet flow.

### Edge-Case URLs for Manual Testing

Test these URLs by bookmarking them and clicking the bookmarklet on each page:

| URL | Description | Expected Behavior |
|-----|-------------|-------------------|
| `https://example.com` | Simple URL, no fragment | No fragment section displayed |
| `https://example.com/page#section1` | URL with simple fragment | Fragment section shows "section1" |
| `https://pydantic.com.cn/en/api/json_schema/#pydantic.json_schema.GenerateJsonSchema.build_schema_type_to_method` | Fragment containing dots | Fragment section shows correct fragment text, link displays correctly |
| `https://example.com/page#has-dots.and.dots.and.dots` | Fragment with multiple dot sequences | Fragment preserved correctly |
| `https://example.com/favicon.ico` | Favicon is ICO, not PNG | ICO converted to PNG inline |
| `https://example.com/no-such-favicon.png` | Favicon URL returns 404 | Favicon section hidden (URL not valid image) |

### Manual Test Checklist

1. **URL with no fragment** (`https://example.com`):
   - [ ] Fragment section does not appear
   - [ ] URL section shows "Original", "Clean", "Root", "Host"
   - [ ] Link displays correctly with title

2. **URL with fragment containing dots** (`https://pydantic.com.cn/...#pydantic.json_schema...`):
   - [ ] Fragment section appears with correct fragment text
   - [ ] All radio buttons work and update the Link preview
   - [ ] URL "With Fragment" variant includes full fragment
   - [ ] Copy buttons work

3. **Favicon validation**:
   - [ ] URLs with broken favicons (404) show no favicon section
   - [ ] URLs with valid favicons show favicon section
   - [ ] Inline vs URL options work

### Bookmarklet Testing

To test the bookmarklet:
1. Run the web-tool server: `make run`
2. Navigate to a test URL in your browser
3. Click the "Mirror Links" bookmarklet
4. Verify the mirror-links page displays correctly

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Test Markers](https://docs.pytest.org/en/stable/example/markers.html)

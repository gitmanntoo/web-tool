# Testing Guide for web-tool

## Overview

This project uses **pytest** as the testing framework with tests organized in a dedicated `tests/` directory, following Python best practices.

## Directory Structure

```
web-tool/
├── tests/
│   ├── __init__.py
│   ├── test_title_variants.py      # Tests for title variant generation
│   └── test_title_strings.py       # Test data for title variants
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

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Test Markers](https://docs.pytest.org/en/stable/example/markers.html)

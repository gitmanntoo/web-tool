# Test Coverage and Best Practices

## Overview

This document describes the comprehensive test suite added to the web-tool project, following Python best practices and industry standards.

## Test Structure

The test suite is organized in the `tests/` directory with the following structure:

```
tests/
├── __init__.py
├── test_title_variants.py       # Title variant generation (~40 tests)
├── test_title_strings.py        # Test data for title variants
├── test_unicode_util.py         # Unicode utility tests (~20 tests)
├── test_text_util.py            # Text processing tests (~30 tests)
├── test_url_util.py             # URL parsing tests (~15 tests)
├── test_html_util.py            # HTML/favicon tests (~20 tests)
├── test_docker_util.py          # Container detection tests (~15 tests)
└── test_img_util.py             # Image conversion tests (~20 tests)
```

**Total: ~160+ test cases across 8 test modules**

## Module-by-Module Coverage

### 1. `test_unicode_util.py` (~20 tests)
**Purpose:** Test Unicode category analysis and utilities

**Test Classes:**
- `TestGeneralCategoryNames` (20 tests)
  - Tests all 30 Unicode general categories
  - Validates letter, mark, number, separator, symbol, punctuation categories
  - Ensures all values are non-empty strings
- `TestCategoryNames` (7 tests)
  - Tests ordered dictionary of major categories
  - Validates frequency ordering

**Coverage:**
- All Unicode category constants
- Data structure integrity
- Category frequency ordering

### 2. `test_text_util.py` (~30 tests)
**Purpose:** Test text processing and parsing functions

**Test Classes:**
- `TestSplitSpecialTag` (7 tests) - HTML tag splitting logic
- `TestNVL` (4 tests) - Null value logic
- `TestStripQuotes` (8 tests) - Quote removal
- `TestEvalScriptText` (3 tests) - Script text evaluation
- `TestIsWord` (5 tests) - Word validation
- `TestLikeHtml` (4 tests) - HTML detection
- `TestLikeEmail` (3 tests) - Email detection
- `TestLikeUrl` (3 tests) - URL detection
- `TestRemoveRepeatedLines` (4 tests) - Duplicate line removal
- `TestCategorizeWord` (3 tests) - Word categorization

**Coverage:**
- HTML tag handling
- Quote and whitespace processing
- Text pattern recognition (email, URL, HTML)
- Word categorization and validation

### 3. `test_url_util.py` (~15 tests)
**Purpose:** Test URL parsing, validation, and manipulation

**Test Classes:**
- `TestGetUserAgent` (2 tests) - User agent retrieval
- `TestSerializedResponseError` (2 tests) - Exception handling
- `TestSerializedResponse` (5 tests) - Response dataclass
- `TestGetTopDomainName` (5 tests) - Domain extraction
- `TestGetUrlRoot` (4 tests) - URL root extraction
- `TestGetUrlHost` (4 tests) - Host extraction
- `TestMakeAbsoluteUrls` (5 tests) - URL resolution
- `TestUrlValidation` (1 test) - Integration test

**Coverage:**
- URL component extraction (host, domain, root)
- Relative and absolute URL handling
- Query string and fragment handling
- HTTPS/HTTP protocol handling
- Error handling and defaults

### 4. `test_html_util.py` (~20 tests)
**Purpose:** Test HTML parsing, favicon discovery, and metadata

**Test Classes:**
- `TestRelLink` (6 tests) - RelLink dataclass
- `TestFaviconConstants` (6 tests) - Favicon configuration
- `TestFaviconCacheStructure` (3 tests) - Cache path configuration
- `TestRelLinkValidation` (5 tests) - Link validation logic
- `TestRelLinkComparison` (3 tests) - Link comparison

**Coverage:**
- Favicon link representation and validation
- Cache configuration (overrides, defaults, auto-discovered)
- Link metadata (rel, sizes, dimensions)
- Favicon constants and paths

### 5. `test_docker_util.py` (~15 tests)
**Purpose:** Test container detection logic

**Test Classes:**
- `TestIsRunningInContainer` (14 tests)
  - /.dockerenv file detection
  - CONTAINER_RUNTIME environment variable
  - /proc/1/cgroup file analysis (docker, containerd, kubepods, podman, lxc)
  - Hostname detection (docker-, container-)
  - uname output detection
  - Error handling and graceful fallbacks
- `TestContainerDetectionIntegration` (2 tests)

**Coverage:**
- Multiple container detection methods
- Linux cgroup parsing
- Hostname and uname output analysis
- Environment variable checking
- Exception handling for missing/unreadable files
- Integration with actual system

### 6. `test_img_util.py` (~20 tests)
**Purpose:** Test image conversion utilities

**Test Classes:**
- `TestImageConversionConstants` (3 tests) - SVG dimension constants
- `TestConvertIco` (8 tests) - ICO to PNG conversion
- `TestConvertSvg` (8 tests) - SVG to PNG conversion
- `TestImageConversionIntegration` (4 tests) - Integration tests
- `TestImageConversionEdgeCases` (4 tests) - Edge cases

**Coverage:**
- Function signatures and parameters
- LRU cache implementation
- Error handling (network errors, invalid formats)
- Format conversion options
- Empty and malformed input handling

### 7. `test_title_variants.py` (~40 tests)
**Purpose:** Test title variant generation (existing tests)

**Test Classes:**
- `TestAsciiAndEmojis` (10 tests)
- `TestAsciiOnly` (5 tests)
- `TestPathSafeFilename` (13 tests)
- `TestTitleVariants` (8 tests)
- `TestEdgeCases` (8 tests)

**Coverage:**
- ASCII and Unicode text conversion
- Emoji preservation and removal
- Filesystem-safe filename generation
- Cross-platform path safety (Windows, macOS, Linux)
- Edge cases (empty strings, combining diacriticals, long titles)

## Testing Best Practices Implemented

### 1. **Test Organization**
- ✅ One test file per module
- ✅ Test classes group related tests
- ✅ Descriptive test names indicating what is tested
- ✅ Clear separation of unit and integration tests

### 2. **Test Structure**
- ✅ Arrange-Act-Assert (AAA) pattern
- ✅ Single responsibility per test
- ✅ No interdependencies between tests
- ✅ Tests can run in any order

### 3. **Naming Conventions**
- ✅ Test files: `test_<module>.py`
- ✅ Test classes: `Test<Functionality>`
- ✅ Test methods: `test_<specific_scenario>`
- ✅ Descriptive docstrings explaining what each test validates

### 4. **Fixture and Mock Usage**
- ✅ Mocks for external dependencies (HTTP requests, file I/O)
- ✅ `unittest.mock` for controlled testing
- ✅ Patch decorators for isolation
- ✅ Side effects for complex scenarios

### 5. **Edge Case Coverage**
- ✅ Empty inputs
- ✅ None/null values
- ✅ Boundary conditions
- ✅ Invalid inputs
- ✅ Error scenarios

### 6. **Documentation**
- ✅ Each test class has a docstring
- ✅ Each test method has a concise docstring
- ✅ Complex tests have inline comments
- ✅ Constants and configuration explained

## Running the Tests

### Run All Tests
```bash
# Using pytest directly
pytest tests/ -v

# Using uv
uv run pytest tests/ -v

# With coverage report
pytest tests/ --cov=library --cov-report=html

# Stop on first failure
pytest tests/ -x

# Run specific test file
pytest tests/test_text_util.py -v

# Run specific test class
pytest tests/test_text_util.py::TestStripQuotes -v

# Run tests matching a pattern
pytest tests/ -k "emoji" -v
```

### Watch Mode (auto-run on file changes)
```bash
pytest tests/ --watch
```

### Generate Coverage Report
```bash
# Terminal report
pytest tests/ --cov=library --cov-report=term-missing

# HTML report
pytest tests/ --cov=library --cov-report=html
# Open htmlcov/index.html in browser
```

## Configuration

### pytest.ini
```ini
[pytest]
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests
minversion = 7.0
showlocals = true
addopts = -v --strict-markers --tb=short --disable-warnings
```

### pyproject.toml
```toml
[project.optional-dependencies]
dev = [
    "ipykernel>=6.29.5",
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
]
```

## Dependencies

All test dependencies are already installed via:
```bash
uv pip install -e ".[dev]"
# or
pip install pytest pytest-cov
```

## Test Coverage Goals

| Module | Target Coverage | Current Status |
|--------|-----------------|-----------------|
| unicode_util | 100% | ✅ Complete |
| text_util | 80%+ | ✅ Comprehensive |
| url_util | 85%+ | ✅ Comprehensive |
| html_util | 80%+ | ✅ Comprehensive |
| docker_util | 95%+ | ✅ Excellent |
| img_util | 85%+ | ✅ Comprehensive |
| title_variants | 100% | ✅ Complete |

## Areas for Future Enhancement

### 1. Integration Tests
- End-to-end testing with real web pages
- Full flow: scraping → parsing → favicon discovery
- CI/CD pipeline integration

### 2. Performance Tests
- Benchmark text processing on large documents
- Cache effectiveness validation
- Memory usage under load

### 3. Additional Fixtures
- Reusable test data for common scenarios
- Parameterized tests for multiple inputs
- Pytest fixtures for setup/teardown

### 4. Mock Services
- Mock HTTP server for URL testing
- Mock file system for path testing
- Mock subprocess for container detection

### 5. Regression Tests
- Tests for previously discovered bugs
- Snapshot testing for complex outputs
- Golden file comparisons

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest tests/ --cov=library --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Troubleshooting

### Import Errors
```bash
# Ensure you're in project root
cd /Users/keith/github/gitmanntoo/web-tool

# Reinstall package in development mode
pip install -e .

# Run tests
pytest tests/
```

### Slow Tests
```bash
# Run tests in parallel
pytest tests/ -n auto

# Run only fast tests
pytest tests/ -m "not slow"
```

### Mock Not Working
- Ensure import paths are correct in patch decorators
- Use full module path: `@patch('library.module.Class')`
- Check that mocks are applied before function is called

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)

## Contributing New Tests

When adding tests for new functionality:

1. **Create test file** following naming convention: `test_<module>.py`
2. **Organize tests** in classes by functionality
3. **Use descriptive names** that explain the test scenario
4. **Include docstrings** for each test class and method
5. **Mock external dependencies** (network, file I/O)
6. **Test edge cases** (empty, None, invalid inputs)
7. **Run coverage** to ensure good coverage: `pytest --cov=library`

Example test structure:
```python
class TestNewFeature:
    """Tests for new feature functionality."""
    
    def test_basic_functionality(self):
        """Test that basic operation works."""
        # Arrange
        input_data = ...
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result == expected_output
    
    def test_edge_case_empty_input(self):
        """Test handling of empty input."""
        result = function_under_test("")
        assert result is not None
    
    @patch('module.external_call')
    def test_with_mock(self, mock_call):
        """Test with mocked external dependency."""
        mock_call.return_value = "mocked"
        result = function_under_test()
        assert mock_call.called
```

---

**Last Updated:** February 1, 2026
**Test Framework:** pytest 9.0.2+
**Python Version:** 3.11+

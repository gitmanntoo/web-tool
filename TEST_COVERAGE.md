# Test Coverage and Best Practices

## Overview

This document describes the comprehensive test suite added to the web-tool project, following Python best practices and industry standards.

## Test Structure

The test suite is organized in the `tests/` directory with the following structure:

```
tests/
├── __init__.py
├── test_title_variants.py       # Title variant generation (~46 tests)
├── test_title_strings.py        # Test data for title variants
├── test_unicode_util.py         # Unicode utility tests (~13 tests)
├── test_text_util.py            # Text processing tests (~44 tests)
├── test_url_util.py             # URL parsing tests (~22 tests)
├── test_html_util.py            # HTML/favicon tests (~37 tests)
├── test_docker_util.py          # Container detection tests (~16 tests)
├── test_img_util.py             # Image conversion tests (~55 tests)
├── test_favicon_validation.py   # Favicon validation tests (~9 tests)
├── test_fragment_variants.py    # Fragment variant duplicate detection (~8 tests)
├── test_integration_pages.py    # Integration tests (~21 tests)
├── test_js_escaping.py          # JavaScript escaping tests (~13 tests)
├── test_markdown_escaping.py    # Markdown link escaping tests (~31 tests)
└── test_url_decoding.py         # URL decoding tests (~6 tests)
```

**Total: 328 test cases across 14 test modules**

## Module-by-Module Coverage

### 1. `test_unicode_util.py` (~13 tests)
**Purpose:** Test Unicode category analysis and utilities

**Test Classes:**
- `TestGeneralCategoryNames` (9 tests)
  - Tests all 30 Unicode general categories
  - Validates letter, mark, number, separator, symbol, punctuation categories
  - Ensures all values are non-empty strings
- `TestCategoryNames` (4 tests)
  - Tests ordered dictionary of major categories
  - Validates frequency ordering

**Coverage:**
- All Unicode category constants
- Data structure integrity
- Category frequency ordering

### 2. `test_text_util.py` (~44 tests)
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

### 3. `test_url_util.py` (~29 tests)
**Purpose:** Test URL parsing, validation, and manipulation

**Test Classes:**
- `TestGetUserAgent` (2 tests) - User agent retrieval
- `TestSerializedResponseError` (2 tests) - Exception handling
- `TestSerializedResponse` (4 tests) - Response dataclass
- `TestGetUrlRoot` (4 tests) - URL root extraction
- `TestGetUrlHost` (4 tests) - Host extraction
- `TestMakeAbsoluteUrls` (5 tests) - URL resolution
- `TestNormalizeNetloc` (3 tests) - Netloc normalization (www stripping, schemeless URLs)
- `TestGetFirstPathSegment` (4 tests) - First path segment extraction
- `TestUrlValidation` (1 test) - Integration test

**Coverage:**
- URL component extraction (host, domain, root)
- Relative and absolute URL handling
- Query string and fragment handling
- HTTPS/HTTP protocol handling
- Error handling and defaults
- `normalize_netloc()` - www prefix stripping, schemeless URL support
- `get_first_path_segment()` - path segment extraction for cache key scoping

### 4. `test_html_util.py` (~37 tests)
**Purpose:** Test HTML parsing, favicon discovery, and metadata

**Test Classes:**
- `TestRelLink` (5 tests) - RelLink dataclass
- `TestFaviconConstants` (7 tests) - Favicon configuration
- `TestFaviconCacheStructure` (3 tests) - Cache path configuration
- `TestRelLinkValidation` (5 tests) - Link validation logic
- `TestRelLinkComparison` (3 tests) - Link comparison
- `TestRelLinkInlineImage` (3 tests) - inline_image field handling
- `TestGetFaviconCacheDictFormat` (3 tests) - Dict-format cache entries
- `TestGetFaviconCacheSource` (3 tests) - Cache source detection with dict format
- `TestPrettifyHtml` (5 tests) - HTML pretty-printing

**Coverage:**
- Favicon link representation and validation
- Cache configuration (overrides, defaults, auto-discovered)
- Link metadata (rel, sizes, dimensions)
- Favicon constants and paths
- Inline base64 image storage in cache
- Dict-format cache entry handling
- HTML pretty-printing

### 5. `test_docker_util.py` (~16 tests)
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

### 6. `test_img_util.py` (~55 tests)
**Purpose:** Test image conversion utilities

**Test Classes:**
- `TestImageConversionConstants` (3 tests) - SVG dimension constants
- `TestConvertIco` (11 tests) - ICO to PNG conversion
- `TestConvertSvg` (10 tests) - SVG to PNG conversion (incl. walrus operator regression tests)
- `TestImageConversionIntegration` (4 tests) - Integration tests
- `TestImageConversionEdgeCases` (2 tests) - Edge cases
- `TestEncodeFaviconInline` (12 tests) - Favicon inline base64 encoding
- `TestEncodeFaviconInlineIntegration` (2 tests) - Integration tests
- `TestEncodeImageInline` (11 tests) - Image inline base64 encoding

**Coverage:**
- Function signatures and parameters
- LRU cache implementation
- Error handling (network errors, invalid formats)
- Format conversion options
- Empty and malformed input handling
- Favicon inline base64 encoding with height-based resizing
- Walrus operator precedence regression tests (ICO and SVG)
- Image inline base64 encoding

### 7. `test_title_variants.py` (~46 tests)
**Purpose:** Test title variant generation (existing tests)

**Test Classes:**
- `TestAsciiAndEmojis` (9 tests)
- `TestAsciiOnly` (5 tests)
- `TestPathSafeFilename` (13 tests)
- `TestTitleVariants` (7 tests)
- `TestDeduplicateVariants` (6 tests)
- `TestEdgeCases` (6 tests)

**Coverage:**
- ASCII and Unicode text conversion
- Emoji preservation and removal
- Filesystem-safe filename generation
- Cross-platform path safety (Windows, macOS, Linux)
- Edge cases (empty strings, combining diacriticals, long titles)

### 8. `test_favicon_validation.py` (~9 tests)
**Purpose:** Test favicon validation pipeline

**Test Classes:**
- `TestGetValidFaviconLinks` (6 tests) - Validates favicon links pipeline
- `TestValidateTopCandidates` (3 tests) - Validates top candidate selection

**Coverage:**
- `get_valid_favicon_links()` composing `get_favicon_links`, `sort_favicon_links`, and `validate_top_candidates`
- Filtering out broken favicon URLs
- Passing `max_count` and `favicon_height` parameters

### 9. `test_fragment_variants.py` (~8 tests)
**Purpose:** Test fragment variant generation and duplicate detection

**Test Classes:**
- `TestFragmentVariants` (8 tests) - Fragment variant duplicate detection

**Coverage:**
- None option never marked duplicate
- Fragment Text marked duplicate when equal to Fragment
- All three options present with correct values
- Pydantic-style fragment fallback

### 10. `test_integration_pages.py` (~21 tests)
**Purpose:** Integration tests for URL/fragment/title handling via Flask test client

**Test Classes:**
- `TestFragmentResolution` (4 tests) - Fragment text resolution
- `TestTitleVariants` (3 tests) - Title variant generation
- `TestURLVariants` (3 tests) - URL variant generation
- `TestMirrorLinksEndpoint` (4 tests) - /mirror-links endpoint
- `TestTestPageEndpoint` (7 tests) - /test-page endpoint

**Coverage:**
- Fragment resolution via PageMetadata handlers
- Title and URL variant generation
- Emoji in page content
- Batch ID parameter handling
- buildHtmlLink uses favW (not undefined faviconW) in rendered JS

### 11. `test_js_escaping.py` (~13 tests)
**Purpose:** Test JavaScript string escaping and variable references in mirror-links template

**Test Classes:**
- `TestMirrorLinksJsEscaping` (7 tests) - JS string escaping via tojson filter
- `TestBuildHtmlLinkTemplate` (4 tests) - buildHtmlLink JS variable references
- Additional tests for markdown escape template logic

**Coverage:**
- Fragment text with newlines/special characters properly escaped
- Title with Unicode characters
- Null favicon handling
- Markdown link template URL wrapping logic
- buildHtmlLink uses favW/favH local consts (not undefined faviconW/faviconHeight)
- Local constant definitions present before favicon branches
- No undefined variable references in buildHtmlLink function body

### 12. `test_markdown_escaping.py` (~31 tests)
**Purpose:** Test Markdown link escaping (escapeMarkdownText, buildMarkdownLink)

**Test Classes:**
- `TestEscapeMarkdownText` (9 tests) - Backslash, bracket escaping
- `TestMarkdownUrlWrapping` (9 tests) - URL angle bracket wrapping
- `TestBuildMarkdownLink` (8 tests) - Full link construction
- `TestRealWorldExamples` (4 tests) - Real-world escaping scenarios

**Coverage:**
- Plain text passthrough
- Escaping `[`, `]`, `\` in link text
- Wrapping URLs in `<>` when containing `()`, `[]`, `<`, spaces
- HTML-encoding `>` inside `<>`-wrapped URLs
- Fragment prefixing in link text
- Wiki-link format unchanged

### 13. `test_url_decoding.py` (~6 tests)
**Purpose:** Test URL decoding in PageMetadata

**Test Classes:**
- `TestPageMetadataUrlDecoding` (6 tests) - URL percent-decoding behavior

**Coverage:**
- URL with fragment containing dots
- URL without fragment
- URL with query string
- URL with percent-encoded hash
- Already-decoded URLs
- Empty URL handling

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
| markdown_escaping | 95%+ | ✅ Comprehensive |
| js_escaping | 85%+ | ✅ Comprehensive |
| url_decoding | 90%+ | ✅ Comprehensive |
| favicon_validation | 80%+ | ✅ Comprehensive |
| fragment_variants | 90%+ | ✅ Comprehensive |

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
        python-version: ["3.13"]
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

**Last Updated:** April 17, 2026 (updated for PR #33 - code simplification)
**Test Framework:** pytest 9.0.3+
**Python Version:** 3.13+

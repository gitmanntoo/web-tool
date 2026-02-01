# Title Variants Enhancement

## Overview

Enhanced title generation with four distinct variants for different use cases:

1. **original** - Unmodified original title string
2. **ascii_and_emojis** - ASCII text with emoji preserved (Unicode stripped)
3. **ascii_only** - Pure ASCII (all Unicode and emoji removed)
4. **path_safe** - Filesystem-safe filename (works on macOS, Linux, Windows)

## New Functions in `library/util.py`

### `text_with_ascii_and_emojis(text: str) -> str`
Converts Unicode characters to ASCII equivalents while preserving emoji.

**Examples:**
- `"Café ☕"` → `"Cafe "` (Unicode converted, ☕ is symbol not emoji)
- `"Hello 👋"` → `"Hello 👋"` (emoji preserved)
- `"Москва 🏛️"` → `"Moskva 🏛️"` (Cyrillic → ASCII, emoji preserved)

**Use case:** When you need ASCII-compatible text but want to keep emoji for visual appeal.

### `text_ascii_only(text: str) -> str`
Converts all text to pure ASCII, removing both Unicode and emoji.

**Examples:**
- `"Café"` → `"Cafe"`
- `"Tokyo 東京"` → `"Tokyo Dong Jing"`
- `"Hello 👋"` → `"Hello "`

**Use case:** Legacy systems, email subjects, or data that requires pure ASCII.

### `path_safe_filename(text: str, replacement: str = "_") -> str`
Creates a filesystem-safe filename compatible with all major operating systems.

**Removes/replaces:**
- Windows invalid: `< > : " / \ | ? *`
- Unix invalid: `/` and null byte
- macOS problematic: `:` (classic path separator)
- Control characters: `\x00-\x1f`
- Leading/trailing spaces and dots

**Examples:**
- `"My <File>: Document?"` → `"My _File_ Document_"`
- `"Path/To/File"` → `"Path_To_File"`
- `"Café"` → `"Cafe"`
- `""` → `"untitled"` (fallback for empty)

**Use case:** Generating safe filenames from page titles, HTML titles, or user input.

### `TitleVariants` Class
Container class that generates all four variants at once.

**Usage:**
```python
from library.util import TitleVariants

tv = TitleVariants("Café 👋 Москва")
print(tv.original)           # "Café 👋 Москва"
print(tv.ascii_and_emojis)   # "Cafe 👋 Moskva"
print(tv.ascii_only)         # "Cafe  Moskva"
print(tv.path_safe)          # "Cafe __Moskva"
```

## Testing

### Testing Framework: **pytest**

**Why pytest?**
- Simple, intuitive syntax
- Great for parametrized tests
- Built-in fixtures and powerful assertions
- Excellent output and error reporting
- Industry standard for Python testing
- Works well with the existing Flask project

### Installation
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Or just pytest
pip install pytest pytest-cov
```

### Running Tests

```bash
# Run all tests
pytest test_title_variants.py -v

# Run specific test class
pytest test_title_variants.py::TestAsciiAndEmojis -v

# Run tests matching pattern
pytest test_title_variants.py -k "emoji" -v

# Run with coverage report
pytest test_title_variants.py --cov=library --cov-report=html

# Run and stop on first failure
pytest test_title_variants.py -x

# Run with verbose output showing variable values
pytest test_title_variants.py -vv
```

## Test Suite Structure

**test_title_variants.py** contains ~90+ test cases organized in test classes:

1. **TestAsciiAndEmojis** (10 tests)
   - ASCII passthrough
   - Emoji preservation
   - Unicode conversion
   - Mixed content handling

2. **TestAsciiOnly** (5 tests)
   - Pure ASCII output
   - Emoji removal
   - Unicode conversion

3. **TestPathSafeFilename** (13 tests)
   - Invalid character removal
   - OS-specific characters handling
   - Empty input fallback
   - Custom replacement characters
   - Realistic scenarios (URLs, emails, etc.)

4. **TestTitleVariants** (8 tests)
   - Class initialization
   - Variant consistency
   - Repr output

5. **TestEdgeCases** (8 tests)
   - Empty/whitespace input
   - Combining diacriticals
   - Very long titles
   - Newlines and special characters

## Integration with Existing Code

The new functions complement existing title handling:

```python
# In mirror-links route, could add variants:
tv = TitleVariants(metadata.title)

# Now template can access:
# {{ tv.original }}           # Full title with emoji
# {{ tv.ascii_and_emojis }}   # ASCII + emoji for compatibility
# {{ tv.ascii_only }}         # Pure ASCII for legacy
# {{ tv.path_safe }}          # Safe for filenames
```

## Key Design Decisions

1. **Separate concerns**: Each variant has a specific use case
2. **Emoji detection**: Uses Unicode code point ranges for common emoji blocks
3. **Graceful degradation**: Empty results become "untitled"
4. **anyascii dependency**: Leverages existing library for reliable Unicode→ASCII conversion
5. **Cross-platform focus**: path_safe works on Windows, macOS, and Linux

## Future Enhancements

- Add `max_length` parameter to truncate long filenames
- Add preservation mode for specific Unicode ranges (e.g., keep CJK characters)
- Add slug generation (lowercase, dash-separated)
- Integration with URL slug patterns

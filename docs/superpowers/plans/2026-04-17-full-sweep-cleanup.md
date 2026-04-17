# Full Sweep Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the walrus operator bug in `convert_svg`, remove dead code left after PR #17 refactor, clean up stale docs/specs, and add missing tests.

**Architecture:** Four task groups executed sequentially: bug fix first (highest risk), then dead code removal, then doc/spec cleanup, then test additions. Each task is self-contained and produces a commit.

**Tech Stack:** Python 3.13, pytest, Flask, lxml, BeautifulSoup4

---

### Task 1: Fix walrus operator bug in `convert_svg`

**Files:**
- Modify: `library/img_util.py:64`

**Bug:** Line 64 has `if t := resp.get_type() != "image/svg":` which evaluates as `t := (resp.get_type() != "image/svg")`, assigning a boolean to `t` instead of the type string. When the response IS an SVG, `t` becomes `False`, and `False != "image/svg"` is `True`, causing the function to return `None` for valid SVGs.

- [ ] **Step 1: Fix the walrus operator precedence**

Change line 64 in `library/img_util.py` from:
```python
        if t := resp.get_type() != "image/svg":
```
to:
```python
        if (t := resp.get_type()) != "image/svg":
```

This matches the correct pattern already used in `convert_ico` at line 33.

- [ ] **Step 2: Run tests to verify nothing broke**

Run: `uv run python -m pytest tests/ -v`
Expected: All 308 tests pass. The `test_uses_cairosvg_conversion` test in `TestConvertSvg` should now actually exercise the correct code path.

- [ ] **Step 3: Commit**

```bash
git add library/img_util.py
git commit -m "fix: correct walrus operator precedence in convert_svg

The walrus operator on line 64 had incorrect precedence:
`if t := resp.get_type() != 'image/svg'` evaluated as
`t := (resp.get_type() != 'image/svg')`, assigning a boolean
to t instead of the type string. This caused SVG favicons to
be silently rejected. Added parentheses to match the pattern
already used in convert_ico."
```

---

### Task 2: Remove dead code from `library/html_util.py`

**Files:**
- Modify: `library/html_util.py`

Remove the following dead code that duplicates functionality now in `util.py`:

- [ ] **Step 1: Remove the `PageMetadata` class (lines 128-138)**

Delete the entire `PageMetadata` dataclass:
```python
@dataclass
class PageMetadata:
    # Passed in parameters
    title: str
    url: str
    html: str = None
    # Derived values.
    clean_url: str = None
    host_url: str = None
    host: str = None
    favicons: list[RelLink] = field(default_factory=list)
    error: str = None
```

- [ ] **Step 2: Remove the `get_page_metadata` function (lines 141-186)**

Delete the entire `get_page_metadata` function including the docstring and body. This function is never called — all routes use `util.get_page_metadata()`.

- [ ] **Step 3: Remove the `get_common_favicon_links` function (lines 578-586)**

Delete:
```python
def get_common_favicon_links(page_url):
    """Get the common favicon links for the page URL."""

    # Build links for the common favicon files.
    links = []
    for f in COMMON_FAVICON_FILES:
        links.append(RelLink(url_util.make_absolute_urls(page_url, f)))

    return links
```

- [ ] **Step 4: Remove unused imports**

Remove `pyperclip` import (line 7) — only used by the dead `get_page_metadata`. Remove `json` import (line 2) — only used by the dead `get_page_metadata`. The `BeautifulSoup` import (line 9) is still used by `get_favicon_links`, so keep it. The `field` import from `dataclasses` (line 3) — check if still needed after removing `PageMetadata`. The `RelLink` dataclass still uses `field(default_factory=list)`, but that's in the same file. After removing `PageMetadata`, check whether `field` is still used. If not, remove the `field` import from the `dataclasses` line.

Also remove `request` from `flask` import (line 10) if it was only used by the dead `get_page_metadata` — check `html_util.py` for other uses of `request`. After review: `request` is used at line 491 (`request.host` in `get_favicon_links`) and line 64 (`ICO_TO_PNG_PATH`), so keep `request`.

After removing `PageMetadata`, `get_page_metadata`, and `get_common_favicon_links`, the `field` import from dataclasses should be removed since it's no longer used in this file.

- [ ] **Step 5: Run tests to verify nothing broke**

Run: `uv run python -m pytest tests/ -v`
Expected: All 308 tests pass. The dead code had no callers.

- [ ] **Step 6: Commit**

```bash
git add library/html_util.py
git commit -m "refactor: remove dead code from html_util.py

Remove PageMetadata class, get_page_metadata function, and
get_common_favicon_links function — all superseded by the
active versions in util.py. Remove unused pyperclip, json,
and field imports."
```

---

### Task 3: Remove dead code from `library/util.py`

**Files:**
- Modify: `library/util.py`

- [ ] **Step 1: Remove the `url_domain` property (lines 254-261)**

Delete:
```python
    @property
    def url_domain(self):
        extracted = tldextract.extract(self.parsed_url.netloc)

        # Return domain name starting with www if subdomain is 'www'
        if extracted.subdomain == "www":
            return f"{extracted.subdomain}.{extracted.domain}.{extracted.suffix}"
        else:
            return f"{extracted.domain}.{extracted.suffix}"
```

This property is never referenced from any template or route handler. Templates use `override_domain` and `override_path_scope` instead.

- [ ] **Step 2: Remove the `parse_cookie_string` function (lines 585-610)**

Delete the entire function:
```python
def parse_cookie_string(cookie_string, url):
    """
    Parse a cookie string into a list of dictionaries with keys: name, value, domain, path
    - Ignored: expires, size, httpOnly, secure, sameSite
    """
    cookie_string = cookie_string.strip()
    if not cookie_string:
        return []

    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    cookies = []
    for cookie in cookie_string.split(";"):
        tokens = cookie.split("=", 1)
        c = {
            "name": tokens[0].strip(),
            "value": "",
            "domain": domain,
            "path": "/",
        }
        if len(tokens) > 1:
            c["value"] = tokens[1].strip()
        cookies.append(c)

    return cookies
```

The only reference was the commented-out line at line 699, which we're also removing.

- [ ] **Step 3: Remove the commented-out code block (lines 660-702)**

Delete the entire ~40-line commented-out block inside `get_page_metadata()`. This is old dictionary-based approach code that's no longer relevant.

- [ ] **Step 4: Check if `tldextract` import is still needed**

After removing `url_domain` (the only user of `tldextract` in `util.py`), check if `tldextract` is imported at line 18 and still used elsewhere. Search for other `tldextract` uses in `util.py`. If none remain, remove the import.

- [ ] **Step 5: Run tests to verify nothing broke**

Run: `uv run python -m pytest tests/ -v`
Expected: All 308 tests pass. The removed code had no callers.

- [ ] **Step 6: Commit**

```bash
git add library/util.py
git commit -m "refactor: remove dead code from util.py

Remove url_domain property (never used by templates),
parse_cookie_string function (only reference was commented
out), and commented-out dictionary-based metadata block."
```

---

### Task 4: Remove dead code from `library/url_util.py`

**Files:**
- Modify: `library/url_util.py`
- Modify: `tests/test_url_util.py`

- [ ] **Step 1: Remove `get_url_bytes` function (lines 230-236)**

Delete:
```python
def get_url_bytes(url: str) -> bytes | None:
    """
    Gets the bytes of a URL. Returns None if the URL does not exist.
    """

    resp = get_url(url)
    return resp.content
```

- [ ] **Step 2: Remove `head_url` function (lines 198-215)**

Delete the entire `head_url` function including its docstring and body.

- [ ] **Step 3: Remove `check_url_exists` function (lines 218-228)**

Delete the entire `check_url_exists` function including its docstring and body.

- [ ] **Step 4: Remove `get_top_domain_name` function (lines 240-266)**

Delete the entire `get_top_domain_name` function including its docstring and body.

- [ ] **Step 5: Remove unused imports in `url_util.py`**

After removing the four functions, check whether `tldextract` (line 11) and `Image` from PIL (line 13) are still used. `tldextract` was only used by `get_top_domain_name`. `Image` from `PIL` is used in `image_size()` (line 284). Remove `tldextract` import if unused. Also remove `lru_cache` decorator from `head_url` and `get_top_domain_name` — but since those functions are being removed, just clean up the remaining `lru_cache` imports. After removing all four functions, check whether `lru_cache` is still needed (it's used by `get_url` and `get_image_size` and `get_url_root` and `get_url_host` and `make_absolute_urls`), so keep it.

- [ ] **Step 6: Remove corresponding tests from `test_url_util.py`**

Remove the `TestGetTopDomainName` class (lines 85-111) entirely — it tests the deleted `get_top_domain_name` function.

Also remove `get_top_domain_name` from the import list on line 12.

- [ ] **Step 7: Run tests to verify nothing broke**

Run: `uv run python -m pytest tests/ -v`
Expected: 303 tests pass (5 fewer: the 5 tests from `TestGetTopDomainName`).

- [ ] **Step 8: Commit**

```bash
git add library/url_util.py tests/test_url_util.py
git commit -m "refactor: remove unused url_util functions and tests

Remove get_url_bytes, head_url, check_url_exists, and
get_top_domain_name — none are called by application code.
Remove TestGetTopDomainName test class. Remove unused
tldextract import."
```

---

### Task 5: Clean up stale specs and docs

**Files:**
- Remove: `specs/pages/mirror-links-original.md`
- Modify: `TESTING.md`
- Modify: `TEST_COVERAGE.md`
- Modify: `web-tool.py:426,444`

- [ ] **Step 1: Remove stale spec**

Delete `specs/pages/mirror-links-original.md` — this spec documents a removed feature with no corresponding route.

- [ ] **Step 2: Update TESTING.md**

Remove the "old test files - deprecated" section from the directory tree (lines 31-32):
```
└── [old test files - deprecated]
    ├── test_title_variants.py      # Deprecated - see tests/
    └── test_title_strings.py       # Deprecated - see tests/
```

Remove the "Deprecated Test Files" section (lines 392-399):
```
### Deprecated Test Files

The old test files (`test_title_variants.py` and `test_title_strings.py` in the root directory) are deprecated. Use the versions in the `tests/` directory instead.

To remove the deprecated files:
```bash
rm test_title_variants.py test_title_strings.py
```
```

- [ ] **Step 3: Fix incomplete docstrings in `web-tool.py`**

At line 426, change:
```python
    """Convert """
```
to:
```python
    """Convert an ICO favicon to PNG format."""
```

At line 444, change:
```python
    """Convert """
```
to:
```python
    """Convert an SVG favicon to PNG format."""
```

Also fix the variable name on line 445 — `ico_url` should be `svg_url`:
```python
    ico_url = request.args.get('url')
```
Change to:
```python
    svg_url = request.args.get('url')
```

And update the reference on line 450 to use `svg_url`:
```python
    png_bytes = img_util.convert_svg(ico_url)
```
Change to:
```python
    png_bytes = img_util.convert_svg(svg_url)
```

- [ ] **Step 4: Update TEST_COVERAGE.md test count**

Update the test count from "308" to "303" (reflecting the 5 removed `TestGetTopDomainName` tests from Task 4). Also update the `test_url_util.py` entry to reflect the removal of `TestGetTopDomainName`.

Change:
```
- `TestGetTopDomainName` (5 tests) - Domain extraction
```
Remove this entry entirely since the class is deleted.

Update the total count from "308 test cases" to "303 test cases".

Update the `test_url_util.py` description from "~15 tests" to "~10 tests" and remove the `TestGetTopDomainName` entry.

- [ ] **Step 5: Run tests to verify nothing broke**

Run: `uv run python -m pytest tests/ -v`
Expected: 303 tests pass.

- [ ] **Step 6: Commit**

```bash
git add specs/pages/mirror-links-original.md TESTING.md TEST_COVERAGE.md web-tool.py
git commit -m "docs: clean up stale specs and docs

Remove mirror-links-original.md spec (no corresponding route).
Remove references to deprecated root-level test files from
TESTING.md. Fix incomplete docstrings on ICO/SVG conversion
routes. Fix variable name ico_url -> svg_url in convert_svg
route. Update test count in TEST_COVERAGE.md."
```

---

### Task 6: Add SVG walrus operator regression tests

**Files:**
- Modify: `tests/test_img_util.py`

- [ ] **Step 1: Add `test_svg_file_passes_magika_check` to `TestConvertSvg` class**

Add this test after the existing `test_accepts_format_parameter` test (around line 223) in the `TestConvertSvg` class:

```python
    @patch("library.img_util.svg2png")
    @patch("library.img_util.url_util.get_url")
    def test_svg_file_passes_magika_check(self, mock_get_url, mock_svg2png):
        """Regression: walrus operator precedence must not short-circuit SVG files.

        Without parentheses, `t := resp.get_type() != "image/svg"` evaluates as
        `t := (resp.get_type() != "image/svg")`, making t a boolean. Since
        `False != "image/svg"` is True, the early return fires even for valid
        SVG files. This test verifies svg2png is called (not short-circuited).
        """
        mock_response = MagicMock()
        mock_response.get_type.return_value = "image/svg"
        mock_response.content = b"<svg></svg>"
        mock_get_url.return_value = mock_response
        mock_svg2png.return_value = None

        convert_svg.cache_clear()
        convert_svg("http://example.com/icon.svg")

        # svg2png MUST be called — assert no early return at magika check
        assert mock_svg2png.called
```

- [ ] **Step 2: Add `test_svg_walrus_operator_captures_type_string_not_boolean` to `TestConvertSvg` class**

Add this test after the previous one:

```python
    @patch("library.img_util.svg2png")
    @patch("library.img_util.url_util.get_url")
    def test_svg_walrus_operator_captures_type_string_not_boolean(self, mock_get_url, mock_svg2png):
        """Regression: verify t captures the type string, not a comparison result.

        If the walrus has wrong precedence, t becomes a bool (False when types
        match), causing incorrect early returns for valid SVG files.
        """
        mock_response = MagicMock()
        mock_response.get_type.return_value = "image/svg"
        mock_response.content = b"<svg></svg>"
        mock_get_url.return_value = mock_response
        mock_svg2png.return_value = None

        convert_svg.cache_clear()
        convert_svg("http://example.com/icon.svg")

        # svg2png must be called — no early return
        assert mock_svg2png.called
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_img_util.py::TestConvertSvg -v`
Expected: All SVG tests pass, including the two new regression tests.

- [ ] **Step 4: Commit**

```bash
git add tests/test_img_util.py
git commit -m "test: add SVG walrus operator regression tests

Add test_svg_file_passes_magika_check and
test_svg_walrus_operator_captures_type_string_not_boolean
to TestConvertSvg, mirroring the ICO tests that caught the
same class of bug."
```

---

### Task 7: Add `prettify_html` unit test

**Files:**
- Modify: `tests/test_html_util.py`

- [ ] **Step 1: Add `TestPrettifyHtml` class to `test_html_util.py`**

First, check if `prettify_html` is already imported or tested in the test file. Then add a new test class:

```python
class TestPrettifyHtml:
    """Tests for prettify_html function."""

    def test_empty_string(self):
        """Test that empty string returns empty string."""
        from library.html_util import prettify_html

        assert prettify_html("") == ""

    def test_none_input(self):
        """Test that None returns None."""
        from library.html_util import prettify_html

        assert prettify_html(None) is None

    def test_simple_html(self):
        """Test that simple HTML is prettified."""
        from library.html_util import prettify_html

        result = prettify_html("<div><p>Hello</p></div>")
        assert "<div>" in result
        assert "<p>Hello</p>" in result

    def test_self_closing_tags(self):
        """Test that self-closing tags are handled correctly."""
        from library.html_util import prettify_html

        result = prettify_html("<div><br/><p>Text</p></div>")
        assert "<br" in result
        assert "Text" in result

    def test_invalid_html_returns_original(self):
        """Test that invalid HTML returns the original string."""
        from library.html_util import prettify_html

        bad_html = "not html at all"
        result = prettify_html(bad_html)
        assert result == bad_html
```

- [ ] **Step 2: Run the new tests**

Run: `uv run python -m pytest tests/test_html_util.py::TestPrettifyHtml -v`
Expected: All 5 new tests pass.

- [ ] **Step 3: Run full test suite**

Run: `uv run python -m pytest tests/ -v`
Expected: 310 tests pass (303 + 2 SVG walrus + 5 prettify_html).

- [ ] **Step 4: Commit**

```bash
git add tests/test_html_util.py
git commit -m "test: add unit tests for prettify_html

Add TestPrettifyHtml class with tests for empty string, None,
simple HTML, self-closing tags, and invalid HTML."
```

---

### Task 8: Update test counts in docs

**Files:**
- Modify: `TESTING.md`
- Modify: `TEST_COVERAGE.md`

- [ ] **Step 1: Update TESTING.md test counts**

Update the total test count from "308" (or whatever stale number) to the actual count after all changes. Run `uv run python -m pytest tests/ --co -q` to get the exact number and update TESTING.md accordingly.

Also update the test class descriptions to reflect the additions:
- Add `TestPrettifyHtml (5 tests)` entry
- Add `test_svg_file_passes_magika_check` and `test_svg_walrus_operator_captures_type_string_not_boolean` to the `TestConvertSvg` description
- Remove `TestGetTopDomainName` from url_util section

- [ ] **Step 2: Update TEST_COVERAGE.md test counts**

Update the test count to match the new total. Update the `test_url_util.py` line to reflect the reduced count. Add `test_html_util.py` entry for the new `TestPrettifyHtml` class.

- [ ] **Step 3: Run full test suite one final time**

Run: `uv run python -m pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add TESTING.md TEST_COVERAGE.md
git commit -m "docs: update test counts and class listings

Update test counts and class descriptions in TESTING.md and
TEST_COVERAGE.md to reflect removed dead code tests and
added regression/prettify_html tests."
```
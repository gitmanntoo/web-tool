# Full Sweep Cleanup Design

**Date:** 2026-04-17
**Scope:** Single PR addressing regressions, dead code, stale docs, and missing tests identified in the last 20 PRs.

## 1. Bug Fix: Walrus Operator in `convert_svg`

**File:** `library/img_util.py:64`

The walrus operator has incorrect precedence:

```python
# Broken — t gets a boolean, not the type string:
if t := resp.get_type() != "image/svg":

# Fixed — matches the pattern in convert_ico at line 33:
if (t := resp.get_type()) != "image/svg":
```

**Impact:** SVG favicons are silently rejected. The function returns `None` for valid SVG input.

**Tests to add in `tests/test_img_util.py`:**
- `test_svg_file_passes_magika_check` — mirrors `test_ico_file_passes_magika_check`
- `test_svg_walrus_operator_captures_type_string_not_boolean` — mirrors `test_walrus_operator_captures_type_string_not_boolean`

## 2. Dead Code Removal

### 2a. `library/html_util.py`

Remove:
- `PageMetadata` class (lines 128-138) — duplicates the active version in `util.py`
- `get_page_metadata()` function (lines 141-186) — never called by any route or template
- `get_common_favicon_links()` (lines 578-586) — never called
- Unused imports: `pyperclip` (line 7), `json` (line 2) — only needed by dead code
- Typo `rueqest` in comment (line 147) — removed with the dead function

### 2b. `library/util.py`

Remove:
- `parse_cookie_string()` (lines 585-610) — never called; only reference is a commented-out line
- `url_domain` property (lines 254-261) — never referenced by templates or routes
- ~40 lines of commented-out code (lines 660-702) — old dictionary-based approach

### 2c. `library/url_util.py`

Remove:
- `get_url_bytes()` (lines 230-236) — never called by application code
- `head_url()` (lines 198-215) — never called by application code
- `check_url_exists()` (lines 218-228) — never called by application code
- `get_top_domain_name()` (lines 240-266) — never called by application code

**Tests:** Remove corresponding tests in `tests/test_url_util.py` for functions being deleted. Keep any tests for functions that remain.

## 3. Stale Spec & Doc Cleanup

- **Remove** `specs/pages/mirror-links-original.md` — documents a removed feature with no route
- **Update** `TESTING.md` — remove references to deprecated root-level test files (`test_title_variants.py`, `test_title_strings.py`) that no longer exist
- **Update** `TEST_COVERAGE.md` — add `ruff` configuration section, verify test counts match current suite
- **Fix** incomplete docstrings on `convert_ico_to_png` (web-tool.py:424) and `convert_svg_to_png` (web-tool.py:442) routes — currently just `"""Convert """`

## 4. Test Additions

- Add SVG-specific walrus operator tests in `tests/test_img_util.py` (listed in section 1)
- Add `prettify_html` unit test — the function at `html_util.py:16-36` is used by `/mirror-html-source` but has no direct tests

Broader route-level integration tests are out of scope for this PR.

## Out of Scope

- `console.log` statements in templates — low priority, useful for debugging
- `.python-version` file — minor consistency issue, not a regression
- Route-level integration tests for `/mirror-favicons`, `/add-favicon-override`, `/debug/*` — separate effort
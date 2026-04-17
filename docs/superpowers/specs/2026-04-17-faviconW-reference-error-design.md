# Fix: `faviconW` ReferenceError in `buildHtmlLink`

**Date:** 2026-04-17
**Status:** Proposed

## Problem

When the mirror-links page renders for any URL that has a favicon, all four link
format displays (HTML, Markdown, Wiki-link, Simple) appear empty. The browser
console shows:

```
ReferenceError: faviconW is not defined
    at buildHtmlLink (mirror-links:256:100)
    at render (mirror-links:306:30)
    at HTMLDocument.<anonymous> (mirror-links:387:13)
```

## Root Cause

In `templates/mirror-links.html`, the `buildHtmlLink` function defines local
constants for fallback dimensions:

```javascript
const favH = faviconHeight || 20;   // line 202
const favW = faviconWidth || 20;     // line 203
```

Lines 205, 207, and 209 reference `faviconW` (capital W after "favicon")
instead of the local const `favW`. Since `faviconW` is not declared in the
function scope, JavaScript throws a `ReferenceError`.

The `height` attributes on those same lines correctly use `favH`; only the
`width` attributes use the wrong identifier.

**Affected lines:**

| Line | Current (broken) | Intended |
|------|-------------------|----------|
| 205  | `width="${faviconW}"` | `width="${favW}"` |
| 207  | `width="${faviconW}"` | `width="${favW}"` |
| 209  | `width="${faviconW}"` | `width="${favW}"` |

## Impact

- Any page with a favicon triggers the error on initial render because the
  default favicon option is "url"
- Pages without favicons are unaffected (the favicon branches are skipped)
- The error prevents all four link formats from rendering, not just HTML

## Fix

Replace `faviconW` with `favW` on lines 205, 207, and 209 of
`templates/mirror-links.html`. Three character-for-character substitutions.

No other changes:
- The existing `favH` references are correct
- No test changes needed (Python test suite doesn't cover client-side JS)
- The CLAUDE.md "Known Bug Patterns" entry for `buildHtmlLink` is accurate
  documentation of this pattern and should remain

## Verification

After applying the fix, navigate to `mirror-links` for a URL with a favicon
(e.g., ibm.com). Confirm:
1. No `ReferenceError` in the browser console
2. All four link format rows display content
3. Favicon image appears with correct dimensions (width ≈ height ≈ 20px)
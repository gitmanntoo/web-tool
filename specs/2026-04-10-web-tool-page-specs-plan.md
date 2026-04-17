# Web-Tool Page Specs — Implementation Plan

**Design:** `specs/2026-04-10-web-tool-page-specs-design.md`

---

## Pages: Three Categories

Every route falls into one of three categories:

| Category | Routes | Has template? |
|----------|--------|---------------|
| **Template pages** | `clip-proxy`, `mirror-favicons`, `mirror-links`, `debug-title-variants`, `debug-url-variants`, `test-page`, `test-pages-interactive`, `debug-inline-image` (GET) | Yes |
| **Plain-text pages** | `mirror-clip`, `mirror-html-source`, `mirror-text`, `mirror-text-debug`, `mirror-soup-text` | No (uses `plain_text.html`) |
| **API-only (no spec)** | `/get`, `/debug/container`, `/debug/clip-cache`, `/debug/favicon-files`, `/clip-collector`, `/add-favicon-override`, `/convert-ico-to-png`, `/convert-svg-to-png` | No |

**`debug-inline-image` (GET):** Renders a template — full spec. POST is JSON API — covered within the GET page spec.

---

## Critical Flags Found During Research

### Flag 1: `mirror-links` `extracted_links` Not Yet Implemented

The existing `specs/mirror-links-spec.md` references `extracted_links` as "NEW" — a planned feature. The current `web-tool.py::get_mirror_links()` does **not** extract links from HTML, and `mirror-links.html` has no "Extracted Links" section.

**Resolution:** `specs/pages/mirror-links.md` documents **current behavior only** (no extracted links). The parent spec notes this as a planned future feature.

### Flag 2: `debug-clipboard-proxy` — Inline HTML, No Template File

`debug_clipboard_proxy()` builds HTML as an f-string and returns it directly. No template file.

**Resolution:** Spec documents inline HTML output from handler.

### Flag 3: `plain_text_response` Shared Auto-Copy Pattern

Only `mirror-clip` and `mirror-html-source` use `util.plain_text_response()`. `mirror-text`, `mirror-text-debug`, and `mirror-soup-text` return raw `Response(mimetype="text/plain")`. The `/js/<filename>.js` route also uses `plain_text_response()` for JS serving.

**Resolution:** Parent spec documents this shared pattern once. Each plain-text page spec references it.

---

## Task List

| # | Task | Output | Notes |
|---|------|--------|-------|
| 1 | Create `specs/pages/` directory + `.gitkeep` | `specs/pages/.gitkeep` | Git requires at least one file in directory |
| 2 | Write `specs/pages/mirror-links.md` | `specs/pages/mirror-links.md` | Based on existing spec; removes `extracted_links` (not implemented) |
| 3 | Write `specs/pages/mirror-favicons.md` | `specs/pages/mirror-favicons.md` | Template: `mirror-favicons.html`, handler: `get_mirror_favicons()` |
| 4 | Write `specs/pages/mirror-text.md` | `specs/pages/mirror-text.md` | Plain-text page via `plain_text_response()` |
| 5 | Write `specs/pages/mirror-html-source.md` | `specs/pages/mirror-html-source.md` | Plain-text page; notes fallback to `mirror_clip()` |
| 6 | Write `specs/pages/mirror-clip.md` | `specs/pages/mirror-clip.md` | Plain-text page |
| 7 | Write `specs/pages/clip-proxy.md` | `specs/pages/clip-proxy.md` | Template: `clip-proxy.html`; documents container vs non-container behavior |
| 8 | Write `specs/pages/debug-title-variants.md` | `specs/pages/debug-title-variants.md` | Template: `debug-title-variants.html` |
| 9 | Write `specs/pages/debug-url-variants.md` | `specs/pages/debug-url-variants.md` | Template: `debug-url-variants.html` |
| 10 | Write `specs/pages/debug-inline-image.md` | `specs/pages/debug-inline-image.md` | Template GET + POST API |
| 11 | Write `specs/pages/debug-favicon-files.md` | `specs/pages/debug-favicon-files.md` | GET-only JSON; documents response shape |
| 12 | Write `specs/pages/debug-clipboard-proxy.md` | `specs/pages/debug-clipboard-proxy.md` | Inline HTML, no template |
| 13 | Write `specs/pages/debug-container.md` | `specs/pages/debug-container.md` | GET-only JSON |
| 14 | Write `specs/pages/debug-clip-cache.md` | `specs/pages/debug-clip-cache.md` | GET-only JSON |
| 15 | Write `specs/pages/test-page.md` | `specs/pages/test-page.md` | Template: `test-page.html` |
| 16 | Write `specs/pages/test-pages-interactive.md` | `specs/pages/test-pages-interactive.md` | Template: `test-pages-interactive.html` |
| 17 | Write `specs/web-tool-spec.md` | `specs/web-tool-spec.md` | Parent spec: architecture, shared patterns, full page index |
| 18 | Commit all page specs + parent | git commit | All 16 spec files |
| 19 | Move design doc to `specs/` | `docs/superpowers/specs/2026-04-10-...` → `specs/` | Historical record |

---

## Commit Strategy

**Single batch commit** for all 16 spec files (clean, atomic). The design doc move can be a separate commit or folded in.

---

## Files to Read Per Page

- Route handler in `web-tool.py`
- Template file in `templates/` (if exists)
- `library/util.py` for shared `plain_text_response`, `get_page_metadata`
- `static/mirror.css` for CSS classes
- `web-tool.py::get_mirror_links()` for `extracted_links` gap note

---

## Open Items

- [x] Flag `extracted_links` not implemented in mirror-links — resolved (spec reflects current code)
- [x] Flag `debug-clipboard-proxy` inline HTML — resolved (spec documents inline output)
- [x] Flag API-only routes excluded — resolved (8 routes get no spec)
- [x] Flag `plain_text_response` shared auto-copy — resolved (parent docs it once)

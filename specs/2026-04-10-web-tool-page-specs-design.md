# Web-Tool Page Specs — Design

**Date:** 2026-04-10
**Author:** keith (Claude Code)
**Status:** Draft

---

## Context

The web-tool currently has one page spec (`specs/mirror-links-spec.md`) for the `/mirror-links` page. As the project grows, there is no systematic documentation for the other 14 web pages. This creates risk of feature drift — when modifying an existing page, there is no authoritative reference for what the page *should* do, making it easy to accidentally change behavior without noticing.

**Goal:** Create a permanent, detailed spec for every web-tool web page, stored in the `specs/` folder, to prevent feature drift during modifications.

---

## Design

### Directory Structure

```
specs/
├── web-tool-spec.md          # Parent spec
└── pages/
    ├── mirror-links.md       # (moved from specs/mirror-links-spec.md)
    ├── mirror-favicons.md
    ├── mirror-text.md
    ├── mirror-html-source.md
    ├── mirror-clip.md
    ├── clip-proxy.md
    ├── debug-title-variants.md
    ├── debug-url-variants.md
    ├── debug-inline-image.md
    ├── debug-favicon-files.md
    ├── debug-clipboard-proxy.md
    ├── debug-container.md
    ├── debug-clip-cache.md
    ├── test-page.md
    └── test-pages-interactive.md
```

### Why This Structure

- **`specs/web-tool-spec.md`** — The parent spec provides architectural context that no single page can carry alone: overall system purpose, shared patterns (clipboard flow, favicon system), how pages reference each other, and a quick index of all pages. A new contributor should be able to read this one file and understand the whole system.

- **`specs/pages/*.md`** — One file per page keeps specs focused and reviewable in isolation. A git diff on a page spec directly reflects what changed in that page's behavior. No cross-page noise.

### Page Spec Template

Each page spec follows this structure:

```markdown
# {Page Name}

**Route:** `{path}` ({GET|POST|GET,POST})
**Template:** `templates/{name}.html`
**Backend:** `web-tool.py::{handler}()`

---

## Overview

{Purpose — what this page does and why it exists. Who uses it and when.}

---

## Data Flow

```
{Server → template → client flow, one level of abstraction}
```

---

## Page Sections

### {Section Name}

**Purpose:** {what this section does}

**Content:** {what it shows/displays}

**Behavior:** {user interaction and what happens}

---

## JavaScript State

```javascript
// State object and default values
```

---

## CSS Classes

| Class | Used on |
|-------|---------|
| ...   | ...     |

---

## Error Handling

{How errors manifest (clipboard parse failure, network error, etc.)}

---

## Edge Cases

| Case | Behavior |
|------|----------|
| ...  | ...      |

---

## Dependencies

- ...
```

### What Each Spec Covers

Per page spec:
- Route path and HTTP methods
- Template file and backend handler function
- Purpose and intended user flow
- All server-side template data passed to the page
- All client-side JavaScript state
- All interactive elements (forms, buttons, radios, copy actions)
- CSS classes used on the page
- Error states and how they surface
- Edge cases specific to that page

Parent spec (`web-tool-spec.md`):
- Overall web-tool purpose and architecture
- Shared patterns across all pages:
  - Clipboard-based data flow (bookmarklet → clipboard → web-tool endpoint)
  - Three-tier favicon cache system
  - pyperclip clipboard access pattern
- Index of all pages with one-line descriptions
- Relationship between pages
- Conventions that all page specs follow

### Implementation Order

Write specs in this order (most-used pages first):

1. `web-tool-spec.md` (parent — written first to establish context, updated at the end with the full page index)
2. `mirror-links.md`
3. `mirror-favicons.md`
4. `mirror-text.md`
5. `mirror-html-source.md`
6. `mirror-clip.md`
7. `clip-proxy.md`
8. Debug pages (alphabetical)
9. Test pages

### Maintenance Policy

- When modifying a web-tool page: update the corresponding page spec first
- When adding a new page: create a new page spec in `specs/pages/`
- When changing shared patterns (clipboard flow, favicon system): update parent spec
- Specs are authoritative — if spec and code disagree, fix the spec or the code (decide per case)

---

## Alternatives Considered

### Flat structure (all specs in `specs/` root)

Rejected: A flat list of 16 files without subdirectories is harder to navigate. The `pages/` subdirectory groups related content cleanly.

### Single monolithic spec

Rejected: A 50-page single file is hard to review, impossible to diff meaningfully, and becomes a bottleneck. No two people can review it in parallel.

### Brief summary specs

Rejected: The user's goal is preventing feature drift. Brief specs don't capture enough detail to catch unintended changes. Full detail is required for the specs to serve their purpose.

---

## Open Questions

None — all clarified with user.

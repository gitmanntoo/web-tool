# Visual Redesign: Mirror Links & Related Pages

**Date:** 2026-04-17
**Status:** Draft
**Scope:** mirror-links, mirror-favicons, debug-title-variants, debug-url-variants, debug-inline-image

## Motivation

The production and debug pages work functionally but look dated — generic Arial font, flat gray panels, inconsistent inline styles, and duplicated code. This redesign modernizes the visual design while keeping the vertical panel layout and all existing functionality intact.

## Design Direction

**Clean Modern** style: system fonts, rounded cards with subtle shadows, blue accent color, white elevated panels on a light gray background.

## Decisions

| Decision | Choice |
|---|---|
| Layout | Keep vertical panel stack |
| CSS approach | Full overhaul — new design system with custom properties, eliminate all inline styles |
| Copy buttons | Subtle Pills — small, rounded, low visual weight |
| Badges | Soft Dot + Label — colored dot before text, no filled background |
| Panels | Elevated Cards — white on light gray with subtle box-shadow |
| Rollout | Unified — all in-scope pages updated in one pass |

## Design Tokens

### Colors

| Token | Value | Usage |
|---|---|---|
| `--color-primary` | `#3b82f6` | Buttons, active radio, links |
| `--color-primary-hover` | `#2563eb` | Button hover |
| `--color-success` | `#22c55e` | Default badge dot, success states |
| `--color-warning` | `#f59e0b` | Discovered badge dot |
| `--color-error` | `#ef4444` | Invalid badge dot, error text |
| `--color-text` | `#1e293b` | Primary text |
| `--color-text-secondary` | `#64748b` | Labels, secondary text |
| `--color-text-muted` | `#94a3b8` | Disabled/muted items |
| `--color-bg` | `#f8fafc` | Page background |
| `--color-surface` | `#ffffff` | Card/panel background |
| `--color-border` | `#e2e8f0` | Panel borders |
| `--color-border-subtle` | `#f1f5f9` | Row dividers |

### Spacing & Sizing

| Token | Value | Usage |
|---|---|---|
| `--space-xs` | `4px` | Tight gaps |
| `--space-sm` | `8px` | Inner padding |
| `--space-md` | `16px` | Section padding |
| `--space-lg` | `24px` | Panel padding |
| `--radius-sm` | `6px` | Badges, inputs |
| `--radius-md` | `12px` | Cards, panels |
| `--radius-pill` | `20px` | Copy buttons, pill badges |

### Typography

| Token | Value | Usage |
|---|---|---|
| `--font-sans` | `system-ui, -apple-system, sans-serif` | All UI text |
| `--font-mono` | `ui-monospace, 'Cascadia Code', 'SF Mono', monospace` | URLs, code |
| `--font-size-xs` | `11px` | Section labels (uppercase) |
| `--font-size-sm` | `12px` | Badges, buttons, secondary |
| `--font-size-base` | `14px` | Body text |
| `--font-size-md` | `16px` | Selected item text |
| `--font-size-lg` | `18px` | Panel headings |

## Component Classes

### Panel (replaces `.metadata-panel` and `.cache-panel`)

- `background: var(--color-surface)`
- `border-radius: var(--radius-md)`
- `box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)`
- `padding: var(--space-lg)`
- Section label: uppercase, `var(--font-size-xs)`, `var(--color-text-secondary)`, letter-spacing 0.08em

### Variant Row (replaces `.url-item`)

- Flex row with `gap: var(--space-sm)`
- Radio buttons: `accent-color: var(--color-primary)`, 14px size
- Selected: full opacity, `var(--color-text)`
- Duplicate: `opacity: 0.45`, `color: var(--color-text-muted)` via `.variant-row--duplicate` class
- Row dividers: `border-bottom: 1px solid var(--color-border-subtle)` (except last child)

### Copy Button (replaces `.copy-btn`)

- Pill shape: `border-radius: var(--radius-pill)`
- `background: var(--color-primary)`, white text
- `font-size: var(--font-size-sm)`, padding `3px 10px`
- Hover: `var(--color-primary-hover)`
- Disabled: `var(--color-text-muted)` background, `cursor: not-allowed`

### Badge (replaces `.cache-badge`)

- Soft dot + label: `display: inline-flex; align-items: center; gap: 5px`
- 8px colored dot with `border-radius: 50%`
- Text in `var(--color-text)` (no badge background)
- Dot colors by precedence:
  - Override: `--color-primary`
  - Default: `--color-success`
  - Discovered: `--color-warning`
  - None: `--color-text-muted`
  - Invalid: `--color-error`

### Cache Item (replaces `.cache-file-item`)

- Left border: 3px, colored by precedence (same dot colors)
- `padding: var(--space-sm) var(--space-md)`
- Path in monospace, `var(--font-size-sm)`

### Link Format Row (replaces `.link-entry`)

- Format label (HTML/Markdown/Wiki/Simple): `var(--font-size-sm)`, `font-weight: 500`, `min-width: 75px`
- Rendered preview and plain text stacked below
- Plain text in monospace, `var(--font-size-sm)`, `var(--color-text-secondary)`

### Tooltip (replaces inline `showTooltip()`)

- Extracted to `static/js/tooltip.js`
- `position: absolute`, `background: var(--color-text)`, white text
- `border-radius: var(--radius-sm)`, `var(--font-size-xs)`
- Auto-remove after 2 seconds

### Primary Button (`.btn-primary`)

- `background: var(--color-primary)`, white text
- `padding: 8px 16px`, `border-radius: var(--radius-sm)`
- `font-size: var(--font-size-base)`
- Hover: `var(--color-primary-hover)`
- Used for form submit buttons, "Add Override", "Paste Favicon", etc.

### Text Input (`.text-input`)

- `border: 1px solid var(--color-border)`, `border-radius: var(--radius-sm)`
- `padding: var(--space-sm) var(--space-sm)`
- `font-size: var(--font-size-base)`, `font-family: var(--font-sans)`
- Focus: `border-color: var(--color-primary)`, `outline: none`, `box-shadow: 0 0 0 3px rgba(59,130,246,0.15)`

### Code Block (`.code-block`)

- `font-family: var(--font-mono)`, `font-size: var(--font-size-sm)`
- `color: var(--color-text-secondary)`
- `padding: var(--space-sm) var(--space-md)`
- `background: var(--color-bg)`, `border-radius: var(--radius-sm)`
- `word-break: break-all`

### Copy Button (`.btn-copy`)

- Same as the Copy Button component described above (pill shape)
- This IS the `.btn-copy` class — the two names refer to the same component

### Page Layout

- `<body>`: `background: var(--color-bg); padding: var(--space-lg)`
- Container: `max-width: 720px; margin: 0 auto`
- Gap between panels: `var(--space-md)`

## Template Changes

### `mirror-links.html`

- Remove all ~15 `style=` attributes
- Replace `.metadata-panel` with `.panel`, `.url-item` with `.variant-row`, `.copy-btn` with new pill style
- Links panel format rows become `.link-format-row` — flex row with label, copy button, rendered preview, plain text
- Duplicate item styling: class `.variant-row--duplicate` instead of inline style
- Favicon panel: `.panel` + new badge style with soft dots
- Paste Favicon button: consistent pill style
- `<body>` wrapper: centered max-width container

### `mirror-favicons.html`

- Remove 1 inline style
- Replace `.cache-panel` with `.panel`, `.cache-file-item` with `.cache-item`
- Badges switch from filled pills to soft dot + label
- Override form inputs/buttons use design tokens
- Success/error messages use `--color-success` / `--color-error`

### `debug-title-variants.html` and `debug-url-variants.html`

- Remove ~5 inline styles each
- Replace `.metadata-panel` with `.panel`, inline flex layouts with `.variant-row`
- Replace duplicated `showTooltip()` with `<script src="/static/js/tooltip.js">`
- Input form: `.text-input` and `.btn-primary` classes

### `debug-inline-image.html`

- Remove ~10 inline styles and the `<style>` block for file-input
- Replace `.metadata-panel` with `.panel`
- Height control: `.text-input` for number input
- File upload: `.btn-primary` styling
- Output area: `.code-block` class instead of inline monospace

## CSS Files

### `mirror.css` — Full rewrite

- `:root` block with all design tokens
- New component classes: `.panel`, `.variant-row`, `.variant-row--duplicate`, `.link-format-row`, `.badge`, `.badge-dot`, `.btn-primary`, `.btn-copy`, `.text-input`, `.code-block`, `.tooltip`
- Remove unused: `.links-section`, `.link-entry`, `.link-html-rendered`, `.link-html-code`
- Remove old: `.metadata-panel`, `.cache-panel`, `.url-item`, `.cache-badge`, `.cache-override`, `.cache-default`, `.cache-discovered`, `.cache-none`, `.cache-invalid`

### `default.css` — Simplified

- `body { font-family: system-ui, -apple-system, sans-serif; background: #f8fafc; }`
- Uses literal values (not custom properties) so out-of-scope pages that only load `default.css` still work
- Remove conflicting `.copy-btn` rule (now fully in `mirror.css`)

### New: `static/js/tooltip.js`

- Shared `showTooltip(element, text)` function
- Extracted from mirror-links, debug-title-variants, debug-url-variants
- Uses `.tooltip` class from new CSS

## Out of Scope

- `plain_text.html`, `clip-proxy.html`, `test-page.html`, `test-pages-interactive.html`, `debug-clipboard-proxy.html`
- `static/prism-mini.css`, `static/prism.css` (Prism themes stay as-is)
- No functional changes — all behavior preserved, only visual presentation changes

## Testing

- Existing integration tests cover all page rendering — they must continue to pass
- Visual changes are CSS-only (class names change, but DOM structure and data remain)
- Tooltip extraction must be tested: verify copy-to-clipboard "Copied!" tooltip appears on mirror-links, debug-title-variants, debug-url-variants
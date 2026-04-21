# Fragment Text UI Fix — Implementation Plan

## Background

Design spec: `docs/superpowers/specs/2026-04-20-fragment-text-ui-fix-design.md`

**Problem:** Fragment Text row (for `#pretty-printing` anchor) shows nothing when radio is not selected. Expected: radio + "Fragment Text" label + value "Pretty-printing" visible at all times, text becomes editable when radio selected.

**Root cause:** The fragment text row only renders an editable `<input>`. No read-only display exists for the non-selected state.

---

## Tasks

- [ ] **1. Add read-only `<span>` to Fragment Text row** (`templates/mirror-links.html`)
  - In the `{% if variant.label == 'Fragment Text' %}` branch (lines 69–80)
  - Add `<span class="fragment-text-readonly">{{ variant.value|e }}</span>` inside the label, before the input
  - Remove `placeholder` from input (not needed with dual-display design)

- [ ] **2. Add CSS `:has()` rules** (`static/mirror.css`)
  - In the "Fragment Text Input" section (after line 423)
  - Rule to hide read-only span when radio is checked
  - Rule to show editable input when radio is checked
  - Default state (radio unchecked): span visible, input hidden

- [ ] **3. Remove obsolete JavaScript toggle** (`templates/mirror-links.html`)
  - Remove lines 407–414 (`Initialize fragment text input visibility based on checked radio` block)
  - The CSS `:has()` handles the swap; JavaScript only updates state

- [ ] **4. Verify with test URL**
  - Run `make test` to confirm no regressions
  - Optional: manual browser test with `https://www.crummy.com/software/BeautifulSoup/bs4/doc/#pretty-printing`

---

## Verification

| Check | Method |
|-------|--------|
| No regressions | `make test` passes |
| Fragment Text row visible when radio unchecked | Manual inspection |
| Editable input shown when radio checked | Manual inspection |
| CSS `:has()` browser support | Modern browsers only (bookmarklet flow) |

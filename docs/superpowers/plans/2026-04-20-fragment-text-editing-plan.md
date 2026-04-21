# Implementation Plan: Fragment Text Editing

**Status:** Superseded — see PR #56 for actual implementation. This document is retained for historical context.

## Context
Mirror Links page needs an editable text field for fragment text. When URL has a fragment, user can select "Fragment Text" and edit the derived text inline.

## Actual Implementation (PR #56)

The final implementation uses a CSS `:has()` approach instead of JavaScript style toggling:

### HTML Structure

```html
<div class="variant-row">
    <input type="radio" name="fragment_variant" value="fragment{{ loop.index0 }}"
      data-text="{{ variant.value|e }}" data-has-text-input="true"
      id="fragment-radio-{{ loop.index0 }}">
    <button class="btn-copy" data-html="{{ variant.value|e }}">Copy</button>
    <span class="variant-label"><strong>{{ variant.label }}</strong></span>
    <label for="fragment-radio-{{ loop.index0 }}" class="fragment-text-label">
        <span class="fragment-text-readonly">{{ variant.value|e }}</span>
        <input type="text" class="fragment-text-input"
               aria-label="Fragment text"
               value="{{ variant.value|e }}">
    </label>
</div>
```

Key differences from original plan:
- Added Copy button to match other fragment variant rows
- Added `.fragment-text-readonly` span for displaying value when radio is unchecked
- Removed `placeholder` attribute (not needed with read-only span)
- Uses `for`/`id` linking (not nesting) to prevent input click from toggling radio off

### CSS Approach (using `:has()`)

Instead of JavaScript toggling `display`, the CSS uses `:has()` to swap visibility:

```css
/* Read-only span shown by default, hidden when radio is checked */
.fragment-text-readonly {
    display: inline;
}

/* Editable input hidden by default */
.fragment-text-input {
    display: none;
    /* ... other styles ... */
}

/* When Fragment Text radio is checked, hide read-only span and show input */
.variant-row:has(input[name="fragment_variant"]:checked) .fragment-text-readonly {
    display: none;
}

.variant-row:has(input[name="fragment_variant"]:checked) .fragment-text-input {
    display: inline-block;
}
```

Key CSS pattern:
- `:has()` must target the common ancestor (`.variant-row`), not the label, since radio and label are siblings
- Read-only span is visible when radio is not selected (matching other fragment rows)
- Editable input appears only when Fragment Text radio is selected

### JavaScript Changes

The JavaScript no longer toggles `textInput.style.display`. Instead, it only:
1. Reads the input value when Fragment Text is selected
2. Syncs the read-only span and Copy button when the input changes (to keep UI consistent)

```javascript
// Fragment text input — live update on typing
fragmentOptions.addEventListener('input', (e) => {
    if (e.target.classList.contains('fragment-text-input')) {
        const checkedRadio = fragmentOptions.querySelector('input[name="fragment_variant"]:checked');
        if (checkedRadio && checkedRadio.dataset.hasTextInput) {
            state.fragmentText = e.target.value;
            // Sync the read-only span and Copy button with the edited value
            const row = e.target.closest('.variant-row');
            if (row) {
                const readonlySpan = row.querySelector('.fragment-text-readonly');
                const copyBtn = row.querySelector('.btn-copy');
                if (readonlySpan) readonlySpan.textContent = e.target.value;
                if (copyBtn) copyBtn.dataset.html = e.target.value;
            }
            render();
        }
    }
});
```

### Browser Support Note

The CSS `:has()` selector requires modern browsers (Firefox 121+, Chrome 105+, Safari 15.4+). In older browsers:
- The `.fragment-text-input` remains hidden (default rule)
- Fragment text is displayed read-only but not editable
- This is an intentional trade-off for cleaner code; the bookmarklet flow targets modern browsers

## Original Plan (Deprecated)

The original plan below described a JavaScript-driven approach with `textInput.style.display` toggling. This was abandoned in favor of the CSS `:has()` approach for cleaner separation of concerns and to avoid the flash-of-unstyled-content issue on page load.

---

### ~~Task 1: Update fragment panel HTML~~

Modify the fragment panel to use a radio + label with embedded text input for the "Fragment Text" option.

Key changes:
- Wrapped fragment options in `id="fragment-options"` for delegated events
- "Fragment Text" uses radio + label structure with embedded text input
- Radio uses `id` and label uses `for` to link them
- Other options (None, Fragment) use original static style
- `data-has-text-input="true"` on Fragment Text radio to mark it

### ~~Task 2: Add CSS styles~~

Add new styles for `.fragment-text-label` and `.fragment-text-input`.

### ~~Task 3: JavaScript event handlers~~

Modify the existing radio change listener to handle Fragment Text selection and toggle `textInput.style.display` based on radio state.

### ~~Task 4: Test~~

Run existing test suite to verify no regressions.

/**
 * Paste Favicon - clipboard image to base64 favicon option
 *
 * Uses the paste event (no browser permission required) after a button click.
 * After clicking "Paste Favicon", the next Ctrl/Cmd+V (or Edit → Paste) anywhere
 * on the page captures the image.
 */

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const PASTE_TIMEOUT_MS = 5000; // 5 second window to paste after clicking

let _pasteTimer = null; // timeout handle for paste window
let _pasteHandler = null; // bound paste event handler
let _pasteKeyHandler = null; // keydown handler for Esc cancel

/**
 * Show a temporary tooltip near the paste favicon button.
 * Uses fixed positioning relative to the button, appended to body.
 * @param {HTMLElement} btn
 * @param {string} message
 */
function showPasteTooltip(btn, message) {
    // Remove any existing tooltip
    const existing = btn.querySelector('.paste-tooltip');
    if (existing) existing.remove();

    const tooltip = document.createElement('span');
    tooltip.className = 'paste-tooltip';
    tooltip.textContent = message;
    tooltip.style.cssText =
        'position: fixed; background: #333; color: white; padding: 4px 8px; ' +
        'border-radius: 4px; font-size: 12px; white-space: nowrap; z-index: 9999; ' +
        'pointer-events: none; display: block;';

    const rect = btn.getBoundingClientRect();
    // Position below the button, left-aligned
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.bottom + 4) + 'px';

    document.body.appendChild(tooltip);

    setTimeout(() => tooltip.remove(), 2000);
}

/**
 * Convert a Blob to a base64 string (no data URL prefix).
 * @param {Blob} blob
 * @returns {Promise<string>}
 */
function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const base64 = reader.result.split(',', 2)[1];
            resolve(base64);
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(blob);
    });
}

/**
 * Send image data to the server and return the resized inline data.
 * @param {string} base64Image  Raw base64 string (no prefix)
 * @returns {Promise<{inline: string, base64: string}>}
 */
async function sendToServer(base64Image) {
    const response = await fetch('/debug/inline-image', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({image_data: base64Image, height: 20}),
    });
    const data = await response.json();
    if (!data.success) {
        throw new Error(data.error || 'Server error');
    }
    return data; // {inline: '<img...>', base64: '...'}
}

/**
 * Add a "Pasted" favicon option to the mirror-links favicon section.
 * Removes any existing "Pasted" option first.
 * @param {string} base64Image  Base64 string (no data URL prefix)
 * @param {HTMLElement} container  The .url-list div inside the favicon section
 * @param {function(string): void} [onSelect]  Called when the pasted option is selected
 */
function addPastedFavicon(base64Image, container, onSelect) {
    // Remove existing Pasted option if present
    const existing = container.querySelector('.favicon-pasted-option');
    if (existing) existing.remove();

    // Create the pasted option div
    const pastedDiv = document.createElement('div');
    pastedDiv.className = 'url-item favicon-pasted-option';

    // Build the full data URL for preview
    const dataUrl = `data:image/png;base64,${base64Image}`;
    const escapedDataUrl = escapeHtml(dataUrl);
    const escapedBase64 = escapeHtml(base64Image);

    pastedDiv.innerHTML = `
        <input type="radio" name="favicon_option" value="pasted">
        <button class="copy-btn" data-html="&lt;img src=&quot;${escapedDataUrl}&quot; height=&quot;20&quot; alt=&quot;Favicon&quot; /&gt;">Copy</button>
        <span style="min-width: 100px;"><strong>Pasted</strong></span>
        <img src="${escapedDataUrl}" height="20" alt="Favicon" />
        <span style="font-family: monospace; font-size: 0.85em; color: #666; word-break: break-all;">
            ${truncateMiddle(escapedBase64, 60)}
        </span>
    `;

    // Insert before the Paste button (last child minus 1)
    const pasteBtn = container.querySelector('.paste-favicon-btn');
    if (pasteBtn && pasteBtn.parentNode === container) {
        container.insertBefore(pastedDiv, pasteBtn.parentNode);
    } else {
        container.appendChild(pastedDiv);
    }

    // Auto-select the pasted option
    const radio = pastedDiv.querySelector('input[type="radio"]');
    if (radio) {
        radio.checked = true;
    }

    // Attach copy button listener
    const copyBtn = pastedDiv.querySelector('.copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(copyBtn.dataset.html).then(() => {
                showPasteTooltip(copyBtn, 'Copied!');
            });
        });
    }

    // Notify state change
    if (onSelect) {
        onSelect('pasted');
    }

    // Update the global state and render
    if (typeof state !== 'undefined') {
        state.faviconOption = 'pasted';
    }
    if (typeof defaultValues !== 'undefined') {
        defaultValues.pastedFavicon = dataUrl;
    }
    if (typeof render === 'function') {
        render();
    }
}

/**
 * Escape text for safe use in HTML.
 * @param {string} text
 * @returns {string}
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Truncate a string in the middle with an ellipsis.
 * @param {string} str
 * @param {number} maxLen
 * @returns {string}
 */
function truncateMiddle(str, maxLen) {
    if (str.length <= maxLen) return str;
    const half = Math.floor((maxLen - 3) / 2);
    return str.slice(0, half) + '...' + str.slice(-half);
}

/**
 * Disarm the paste listener and clear the timeout.
 * @param {HTMLButtonElement} btn
 */
function disarmPaste(btn) {
    if (_pasteHandler) {
        document.removeEventListener('paste', _pasteHandler);
        _pasteHandler = null;
    }
    if (_pasteKeyHandler) {
        document.removeEventListener('keydown', _pasteKeyHandler);
        _pasteKeyHandler = null;
    }
    if (_pasteTimer) {
        clearTimeout(_pasteTimer);
        _pasteTimer = null;
    }
    if (btn) {
        btn.textContent = 'Paste Favicon';
    }
}

/**
 * Handle the Paste Favicon button click on mirror-links.html.
 * Arms a one-time paste event listener. The next Ctrl/Cmd+V anywhere on the
 * page will capture the image. The listener auto-disarms after 5 seconds.
 * @param {HTMLButtonElement} btn
 * @param {HTMLElement} container
 */
async function handlePasteFavicon(btn, container) {
    // Disarm any previous paste session
    disarmPaste(null);

    btn.textContent = 'Waiting for paste... (Esc to cancel)';

    // Build the paste handler
    _pasteHandler = async (e) => {
        // Prevent the default paste (no browser auto-insert)
        e.preventDefault();

        // Disarm immediately — single use only
        disarmPaste(btn);
        btn.textContent = 'Pasting...';

        // Get image from clipboard
        const items = e.clipboardData?.items;
        if (!items) {
            btn.textContent = 'Paste Failed';
            showPasteTooltip(btn, 'No clipboard data');
            return;
        }

        let imageBlob = null;
        for (const item of items) {
            if (item.kind === 'file' && item.type.startsWith('image/')) {
                imageBlob = item.getAsFile();
                break;
            }
        }

        if (!imageBlob) {
            btn.textContent = 'Paste Failed';
            showPasteTooltip(btn, 'No image in clipboard');
            return;
        }

        if (imageBlob.size > MAX_FILE_SIZE) {
            btn.textContent = 'Paste Failed';
            showPasteTooltip(btn, 'Image too large (max 5MB)');
            return;
        }

        try {
            const rawBase64 = await blobToBase64(imageBlob);

            // Send to server — receives resized base64 at height=20
            const data = await sendToServer(rawBase64);

            addPastedFavicon(data.base64, container, (option) => {
                if (typeof state !== 'undefined') {
                    state.faviconOption = option;
                }
            });

            btn.textContent = 'Pasted!';
        } catch (err) {
            console.error('handlePasteFavicon:', err);
            btn.textContent = 'Paste Failed';
            showPasteTooltip(btn, err.message || 'Paste failed');
        }
    };

    // Attach the paste listener
    document.addEventListener('paste', _pasteHandler);

    // Esc to cancel
    _pasteKeyHandler = (e) => {
        if (e.key === 'Escape') {
            disarmPaste(btn);
            btn.textContent = 'Paste Favicon';
        }
    };
    document.addEventListener('keydown', _pasteKeyHandler);

    // Auto-disarm after timeout
    _pasteTimer = setTimeout(() => {
        if (_pasteHandler) {
            disarmPaste(btn);
            btn.textContent = 'Paste Favicon';
        }
    }, PASTE_TIMEOUT_MS);
}

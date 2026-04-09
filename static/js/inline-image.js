/**
 * Inline Image Generator - debug page JS
 *
 * Uses the paste event (no browser permission required) after a button click.
 * After clicking "Paste Image", the next Ctrl/Cmd+V anywhere on the page captures
 * the image.
 */

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const PASTE_TIMEOUT_MS = 5000; // 5 second window to paste after clicking

let _pasteTimer = null;
let _pasteHandler = null;
let _pasteKeyHandler = null;

/**
 * Show a temporary tooltip on a button element.
 * @param {HTMLElement} btn
 * @param {string} message
 */
function showInlineTooltip(btn, message) {
    const existing = btn.querySelector('.inline-tooltip');
    if (existing) existing.remove();

    const tooltip = document.createElement('span');
    tooltip.className = 'inline-tooltip';
    tooltip.textContent = message;
    tooltip.style.cssText =
        'position: absolute; background: #333; color: white; padding: 4px 8px; ' +
        'border-radius: 4px; font-size: 12px; white-space: nowrap; z-index: 1000; ' +
        'pointer-events: none; display: inline-block;';

    const rect = btn.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.top - 30) + 'px';

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
 * Read a File as a base64 string (no data URL prefix).
 * @param {File} file
 * @returns {Promise<string>}
 */
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const base64 = reader.result.split(',', 2)[1];
            resolve(base64);
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
    });
}

/**
 * Send image data to the server and update the output display.
 * @param {string} base64Image  Raw base64 string (no prefix)
 * @param {number} height
 * @returns {Promise<void>}
 */
async function sendToServer(base64Image, height) {
    const response = await fetch('/debug/inline-image', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({image_data: base64Image, height: height}),
    });

    const data = await response.json();

    if (data.success) {
        updatePreview(data.inline, data.base64, data.width, data.height);
        const widthDisplay = document.getElementById('width-display');
        if (widthDisplay && data.width) {
            widthDisplay.value = data.width;
        }
        showInlineTooltip(document.getElementById('copy-output-btn'), 'Ready!');
    } else {
        showInlineTooltip(document.getElementById('copy-output-btn'), 'Error: ' + data.error);
        clearPreview();
    }
}

/**
 * Update the output section with the generated img tag and raw base64.
 * @param {string} imgTag  Complete <img .../> tag
 * @param {string} base64  Raw base64 string
 * @param {number} width  Image width in pixels
 * @param {number} height  Image height in pixels
 */
function updatePreview(imgTag, base64, width, height) {
    const outputTag = document.getElementById('output-tag');
    const outputBase64 = document.getElementById('output-base64');
    const outputDimensions = document.getElementById('output-dimensions');
    const copyBtn = document.getElementById('copy-output-btn');

    if (outputTag) outputTag.innerHTML = imgTag;
    if (outputBase64) outputBase64.textContent = base64;
    if (outputDimensions) {
        outputDimensions.textContent = `Dimensions: ${width}×${height}px`;
    }
    if (copyBtn) {
        copyBtn.dataset.html = imgTag;
        copyBtn.disabled = false;
    }
}

/**
 * Clear the preview area.
 */
function clearPreview() {
    const outputTag = document.getElementById('output-tag');
    const outputBase64 = document.getElementById('output-base64');
    const outputDimensions = document.getElementById('output-dimensions');
    const copyBtn = document.getElementById('copy-output-btn');
    const widthDisplay = document.getElementById('width-display');

    if (outputTag) outputTag.innerHTML = '';
    if (outputBase64) outputBase64.textContent = '';
    if (outputDimensions) outputDimensions.textContent = '';
    if (widthDisplay) widthDisplay.value = '';
    if (copyBtn) {
        copyBtn.dataset.html = '';
        copyBtn.disabled = true;
    }
}

/**
 * Copy the generated img tag to clipboard.
 */
async function copyOutput() {
    const btn = document.getElementById('copy-output-btn');
    const html = btn && btn.dataset.html;
    if (!html) return;

    try {
        await navigator.clipboard.writeText(html);
        showInlineTooltip(btn, 'Copied!');
    } catch (err) {
        showInlineTooltip(btn, 'Copy failed');
    }
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
        btn.textContent = 'Paste Image';
    }
}

/**
 * Handle the Paste Image button click.
 * Arms a one-time paste event listener. The next Ctrl/Cmd+V anywhere on the
 * page will capture the image. The listener auto-disarms after 5 seconds.
 */
async function handlePaste() {
    const btn = document.getElementById('paste-btn');
    const height = parseInt(document.getElementById('height-input')?.value, 10) || 20;

    // Disarm any previous paste session
    disarmPaste(null);

    showInlineTooltip(btn, 'Waiting for paste... (Esc to cancel)');
    btn.textContent = 'Waiting...';

    _pasteHandler = async (e) => {
        e.preventDefault();
        disarmPaste(btn);

        const items = e.clipboardData?.items;
        if (!items) {
            showInlineTooltip(btn, 'No clipboard data');
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
            showInlineTooltip(btn, 'No image in clipboard');
            return;
        }

        if (imageBlob.size > MAX_FILE_SIZE) {
            showInlineTooltip(btn, 'Image too large (max 5MB)');
            return;
        }

        try {
            const base64 = await blobToBase64(imageBlob);
            showInlineTooltip(btn, 'Processing...');
            await sendToServer(base64, height);
            // Clear the file input so no filename is shown
            document.getElementById('file-input').value = '';
        } catch (err) {
            console.error('handlePaste:', err);
            showInlineTooltip(btn, 'Paste failed');
        }
    };

    document.addEventListener('paste', _pasteHandler);

    // Esc to cancel
    _pasteKeyHandler = (e) => {
        if (e.key === 'Escape') {
            disarmPaste(btn);
            showInlineTooltip(btn, 'Paste cancelled');
        }
    };
    document.addEventListener('keydown', _pasteKeyHandler);

    _pasteTimer = setTimeout(() => {
        if (_pasteHandler) {
            disarmPaste(btn);
            showInlineTooltip(btn, 'Paste cancelled');
        }
    }, PASTE_TIMEOUT_MS);
}

/**
 * Handle a file input change event.
 * @param {File} file
 */
async function handleFileUpload(file) {
    const height = parseInt(document.getElementById('height-input')?.value, 10) || 20;

    if (!file || !file.type.startsWith('image/')) {
        return;
    }

    if (file.size > MAX_FILE_SIZE) {
        showInlineTooltip(document.getElementById('file-input'), 'Image too large (max 5MB)');
        return;
    }

    const base64 = await fileToBase64(file);
    await sendToServer(base64, height);
}

/**
 * Attach event listeners for the debug inline-image page.
 */
function attachListeners() {
    const pasteBtn = document.getElementById('paste-btn');
    if (pasteBtn) {
        pasteBtn.addEventListener('click', handlePaste);
    }

    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files && e.target.files[0];
            if (file) handleFileUpload(file);
        });
    }

    const copyBtn = document.getElementById('copy-output-btn');
    if (copyBtn) {
        copyBtn.disabled = true;
        copyBtn.addEventListener('click', copyOutput);
    }
}

// Auto-attach on DOMContentLoaded
document.addEventListener('DOMContentLoaded', attachListeners);

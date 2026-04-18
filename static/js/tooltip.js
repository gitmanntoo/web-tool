/**
 * Show a temporary tooltip above an element.
 * @param {HTMLElement} element - The element to position the tooltip above
 * @param {string} message - The tooltip text to display
 * @param {number} [duration=1500] - Duration in ms before auto-remove
 */
function showTooltip(element, message, duration) {
    duration = duration || 1500;
    var tooltip = document.createElement('span');
    tooltip.textContent = message;
    tooltip.className = 'tooltip';

    var rect = element.getBoundingClientRect();
    tooltip.style.left = (rect.left + window.scrollX) + 'px';
    tooltip.style.top = (rect.top + window.scrollY - 30) + 'px';

    document.body.appendChild(tooltip);

    setTimeout(function() {
        tooltip.remove();
    }, duration);
}

/**
 * Attach copy button listeners to all .btn-copy elements.
 * Looks for data-html attribute to copy to clipboard.
 */
function attachCopyListeners() {
    document.querySelectorAll('.btn-copy').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var html = btn.dataset.html;
            if (html) {
                navigator.clipboard.writeText(html).then(function() {
                    showTooltip(btn, 'Copied!');
                }).catch(function(err) {
                    console.error('Copy failed:', err);
                });
            }
        });
    });
}
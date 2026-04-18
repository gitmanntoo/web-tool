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
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.top - 30) + 'px';

    document.body.appendChild(tooltip);

    setTimeout(function() {
        tooltip.remove();
    }, duration);
}
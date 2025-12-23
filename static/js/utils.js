// Utility functions for the Smart Curriculum System

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - Type of toast: 'success', 'error', 'warning'
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showToast(message, type = 'success', duration = 3000) {
    // Remove existing toasts
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // Icon based on type
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        warning: 'fa-exclamation-triangle'
    };

    const iconClass = icons[type] || icons.success;

    toast.innerHTML = `
        <i class="fas ${iconClass}"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Show a loading overlay
 * @param {string} message - Optional loading message
 */
function showLoading(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'message-overlay';
    overlay.innerHTML = `
        <div class="message-box">
            <div class="spinner spinner-lg" style="margin: 0 auto 1rem;"></div>
            <p style="color: #6b7280;">${message}</p>
        </div>
    `;
    document.body.appendChild(overlay);
}

/**
 * Hide the loading overlay
 */
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * Auto-dismiss flash messages after a delay
 */
function initFlashMessages() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.3s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

/**
 * Format date to readable string
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
    const d = new Date(date);
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return d.toLocaleDateString('en-US', options);
}

/**
 * Format time to readable string
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted time string
 */
function formatTime(date) {
    const d = new Date(date);
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

/**
 * Detect if user is on mobile device
 * @returns {boolean} True if mobile
 */
function isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<void>}
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied to clipboard!', 'success');
    } catch (err) {
        showToast('Failed to copy', 'error');
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initFlashMessages();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showToast,
        showLoading,
        hideLoading,
        formatDate,
        formatTime,
        isMobile,
        copyToClipboard
    };
}

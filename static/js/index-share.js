// Index page: share-link helpers.

// Copy share link to clipboard
function copyShareLink(recipeKey) {
    const shareUrl = `${window.location.origin}/recipe/${recipeKey}`;
    
    // Try to use modern clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(shareUrl).then(() => {
            showShareNotification('הקישור הועתק ללוח!');
        }).catch(() => {
            fallbackCopyTextToClipboard(shareUrl);
        });
    } else {
        fallbackCopyTextToClipboard(shareUrl);
    }
}

// Fallback for older browsers
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showShareNotification('הקישור הועתק ללוח!');
        } else {
            showShareNotification('לא ניתן להעתיק. הקישור: ' + text, true);
        }
    } catch (err) {
        showShareNotification('לא ניתן להעתיק. הקישור: ' + text, true);
    }
    
    document.body.removeChild(textArea);
}

// Show notification
function showShareNotification(message, isError = false) {
    // Remove existing notification if any
    const existing = document.getElementById('share-notification');
    if (existing) {
        existing.remove();
    }

    const notification = document.createElement('div');
    notification.id = 'share-notification';
    notification.className = `fixed top-4 left-1/2 transform -translate-x-1/2 bg-${isError ? 'red' : 'green'}-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 fade-in`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

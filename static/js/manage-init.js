// Manage page: event listeners, share-link helpers and startup.

// Initialize form event listeners
function initializeFormListeners() {
    const toggleBtn = document.getElementById('toggle-form-btn');
    const cancelBtn = document.getElementById('cancel-form-btn');
    const recipeForm = document.getElementById('recipe-form');
    const parseBtn = document.getElementById('parse-recipe-btn');
    const freeTextArea = document.getElementById('free-text-recipe');
    const emojiSelect = document.getElementById('recipe-emoji');
    const emojiCustom = document.getElementById('recipe-emoji-custom');

    // Typing a valid emoji selects it; picking from the list clears the typed text
    emojiCustom.addEventListener('input', () => {
        const value = emojiCustom.value.trim();
        if (isValidEmoji(value)) {
            setRecipeEmoji(value);
        }
    });
    emojiSelect.addEventListener('change', () => { emojiCustom.value = ''; });

    if (parseBtn) {
        parseBtn.addEventListener('click', parseFreeTextRecipe);
    }
    
    // Allow Enter+Shift to submit, or just Enter if text is long enough
    if (freeTextArea) {
        freeTextArea.addEventListener('keydown', (e) => {
            // Ctrl+Enter or Cmd+Enter to parse
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                parseFreeTextRecipe();
            }
        });
    }
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleForm);
    }
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            document.getElementById('add-recipe-form').classList.add('hidden');
            document.getElementById('recipe-form').reset();
            document.getElementById('form-message').classList.add('hidden');
            editingRecipeKey = null;
            // Update form title back to "Add Recipe"
            reviewingParsedRecipe = false;
            const formTitle = document.getElementById('add-recipe-title');
            formTitle.textContent = translations[currentLanguage].add_recipe_title;
        });
    }
    if (recipeForm) {
        recipeForm.addEventListener('submit', handleRecipeSubmit);
    }
}

// Language button event listeners
document.querySelectorAll('.language-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        switchLanguage(btn.dataset.lang);
    });
});

// Copy share link to clipboard
function copyShareLink(recipeKey) {
    const shareUrl = `${window.location.origin}/recipe/${recipeKey}`;
    
    // Try to use modern clipboard API
    const t = translations[currentLanguage];
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(shareUrl).then(() => {
            showShareNotification(t.link_copied);
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
    
    const t = translations[currentLanguage];
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showShareNotification(t.link_copied);
        } else {
            showShareNotification(t.link_copy_error.replace('{link}', text), true);
        }
    } catch (err) {
        showShareNotification(t.link_copy_error.replace('{link}', text), true);
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

// Initialize the app
// Initialize form listeners first (they need to be available)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeFormListeners();
        loadRecipes();
    });
} else {
    initializeFormListeners();
    loadRecipes();
}

// Index page: language buttons and startup.

// Language button event listeners
document.querySelectorAll('.language-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        switchLanguage(btn.dataset.lang);
    });
});

// Initialize the app
// Load recipes when page loads
loadRecipes();

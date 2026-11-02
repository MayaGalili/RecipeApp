// Index page: language buttons and startup.

// Language button event listeners
document.querySelectorAll('.language-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        switchLanguage(btn.dataset.lang);
    });
});

// Recipe search (the input event also fires on the browser's native clear button)
document.getElementById('recipe-search').addEventListener('input', (e) => {
    searchQuery = e.target.value;
    createRecipeSelector();
});

// Initialize the app
// Load recipes when page loads
loadRecipes();

// Index page: shared state and language switching.

let currentLanguage = 'he';

// API endpoints (URLs come from Flask url_for via APP_CONFIG, set in index.html)
const API_ENDPOINTS = {
    recipes: APP_CONFIG.recipes
};

let selectedRecipes = {}; // { recipeKey: servings } for the combined shopping list
let shoppingListGenerated = false; // The list is only shown after "Generate"
let currentRecipe = null; // Will be set after recipes load
let searchQuery = ''; // Recipe name filter; kept across language switches
const collapsedCategories = new Set(); // Category keys whose recipe row is folded away

// Initialize the application after recipes are loaded
function initializeApp() {
    // Set default recipe if not set
    if (!currentRecipe || !recipes[currentRecipe]) {
        // Get the first available recipe from any category
        const firstCategory = Object.keys(recipeCategoryMap)[0];
        if (firstCategory && recipeCategoryMap[firstCategory].length > 0) {
            currentRecipe = recipeCategoryMap[firstCategory][0];
        } else {
            // Fallback: get first recipe from recipes object
            const recipeKeys = Object.keys(recipes);
            if (recipeKeys.length > 0) {
                currentRecipe = recipeKeys[0];
            }
        }
    }
    
    // Initialize the UI
    createRecipeSelector();
    renderSelectedRecipes();
    updateAll();
}

// Language switching function
function switchLanguage(lang) {
    currentLanguage = lang;
   
    // Update language button states
    document.querySelectorAll('.language-btn').forEach(btn => {
        const isActive = btn.dataset.lang === lang;
        btn.classList.toggle('is-active', isActive);
        btn.setAttribute('aria-pressed', String(isActive));
    });

    // Update page direction
    const html = document.documentElement;
    if (lang === 'he') {
        html.setAttribute('dir', 'rtl');
        html.setAttribute('lang', lang);
    } else {
        html.setAttribute('dir', 'ltr');
        html.setAttribute('lang', lang);
    }

    // Update all text elements
    updateLanguageTexts();
}

// Update all text elements based on current language
function updateLanguageTexts() {
    const t = translations[currentLanguage];
   
    document.title = t.recipe_title;
    document.getElementById('recipe-title').textContent = t.recipe_title;
    document.getElementById('brand-name').textContent = t.recipe_title;
    document.getElementById('nav-all-text').textContent = t.nav_all;
    document.getElementById('nav-plan-text').textContent = t.nav_plan;
    document.getElementById('subtitle').textContent = t.subtitle;
    document.getElementById('recipe-selector-title').textContent = t.recipe_selector_title;
    document.getElementById('instructions-title').textContent = t.instructions_title;
    document.getElementById('shopping-list-title').textContent = t.shopping_list_title;
    document.getElementById('print-text').textContent = t.print_text;
    document.getElementById('copy-clipboard-text').textContent = t.copy_clipboard_text;
    document.getElementById('reset-text').textContent = t.reset_text;

    const searchInput = document.getElementById('recipe-search');
    searchInput.placeholder = t.search_label;
    searchInput.setAttribute('aria-label', t.search_label);
    const manageBtn = document.getElementById('manage-recipes-btn');
    if (manageBtn) {
        manageBtn.title = t.manage_recipes;
        manageBtn.setAttribute('aria-label', t.manage_recipes);
    }

    // Update recipe selector
    updateRecipeSelector();

    // Update selected recipes, and rebuild a shown list in the new language
    renderSelectedRecipes();
    if (shoppingListGenerated) {
        updateShoppingList();
    }

    // Update all content
    updateAll();
}

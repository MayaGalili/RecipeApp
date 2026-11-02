// Index page: shared state and language switching.

let currentLanguage = 'he';

// API endpoints (URLs come from Flask url_for via APP_CONFIG, set in index.html)
const API_ENDPOINTS = {
    recipes: APP_CONFIG.recipes
};

let currentServings = 4;
let currentRecipe = null; // Will be set after recipes load
let searchQuery = ''; // Recipe name filter; kept across language switches

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
    updateAll();
}

// Language switching function
function switchLanguage(lang) {
    currentLanguage = lang;
   
    // Update language button states
    document.querySelectorAll('.language-btn').forEach(btn => {
        if (btn.dataset.lang === lang) {
            btn.className = 'language-btn px-4 py-2 rounded-md font-medium transition-all duration-200 bg-orange-500 text-white';
        } else {
            btn.className = 'language-btn px-4 py-2 rounded-md font-medium transition-all duration-200 text-gray-600 hover:bg-gray-100';
        }
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
   
    document.getElementById('recipe-title').textContent = t.recipe_title;
    document.getElementById('subtitle').textContent = t.subtitle;
    document.getElementById('recipe-selector-title').textContent = t.recipe_selector_title;
    document.getElementById('serving-selector-title').textContent = t.serving_selector_title;
    document.getElementById('serving-label').textContent = t.serving_label;
    document.getElementById('ingredients-title').textContent = t.ingredients_title;
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
        manageBtn.textContent = t.manage_recipes;
        manageBtn.title = currentLanguage === 'he' ? 'ניהול מתכונים' : 'Manage Recipes';
    }
   
    // Update preset buttons
    updatePresetButtons();
   
    // Update recipe selector
    updateRecipeSelector();
   
    // Update all content
    updateAll();
}

// Update preset buttons with current language
function updatePresetButtons() {
    const t = translations[currentLanguage];
    const presetButtons = document.querySelectorAll('.preset-btn');
    presetButtons.forEach(btn => {
        const servings = btn.dataset.servings;
        btn.textContent = `${servings} ${t.servings_text}`;
    });
}

// Manage page: shared state, API helper, language switching.

let currentLanguage = 'he';

// API endpoints (URLs come from Flask url_for via APP_CONFIG, set in manage.html)
const API_ENDPOINTS = {
    recipes: APP_CONFIG.recipes,
    addRecipe: APP_CONFIG.addRecipe,
    updateRecipe: APP_CONFIG.updateRecipe,
    deleteRecipe: APP_CONFIG.deleteRecipe
};

// fetch wrapper for admin API calls: adds the CSRF token and returns to login when the session expired
async function apiFetch(url, options = {}) {
    const headers = Object.assign({}, options.headers, {
        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
    });
    const response = await fetch(url, Object.assign({}, options, { headers }));
    if (response.status === 401) {
        window.location.href = APP_CONFIG.login;
    }
    return response;
}

// Track if we're editing a recipe
let editingRecipeKey = null;

let currentRecipe = null; // Will be set after recipes load

// Initialize the application after recipes are loaded
function initializeApp() {
    // Just create the recipe selector - no need to set current recipe in manage page
    createRecipeSelector();
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
    document.getElementById('back-to-home').textContent = t.back_to_home;
    document.getElementById('free-text-title').textContent = t.free_text_title;
    document.getElementById('free-text-desc').textContent = t.free_text_desc;
    document.getElementById('free-text-label').textContent = t.free_text_label;
    document.getElementById('free-text-recipe').placeholder = t.free_text_placeholder;
    document.getElementById('parse-btn-text').textContent = t.parse_btn;
    document.getElementById('parse-btn-loading').textContent = t.parse_loading;
    document.getElementById('toggle-form-btn').textContent = t.toggle_form_btn;
    document.getElementById('add-recipe-title').textContent = editingRecipeKey ? t.edit_recipe_title : (reviewingParsedRecipe ? t.review_recipe_title : t.add_recipe_title);
    document.getElementById('recipe-name-he-label').textContent = t.recipe_name_he;
    document.getElementById('recipe-name-en-label').textContent = t.recipe_name_en;
    document.getElementById('emoji-label').textContent = t.emoji_label;
    document.getElementById('emoji-select-option').textContent = t.emoji_select;
    document.getElementById('recipe-emoji-custom').placeholder = t.emoji_custom;
    document.getElementById('category-label').textContent = t.category_label;
    document.getElementById('ingredients-he-label').textContent = t.ingredients_he_label;
    document.getElementById('ingredients-he').placeholder = t.ingredients_he_placeholder;
    document.getElementById('ingredients-en-label').textContent = t.ingredients_en_label;
    document.getElementById('ingredients-en').placeholder = t.ingredients_en_placeholder;
    document.getElementById('instructions-he-label').textContent = t.instructions_he_label;
    document.getElementById('instructions-he').placeholder = t.instructions_he_placeholder;
    document.getElementById('instructions-en-label').textContent = t.instructions_en_label;
    document.getElementById('instructions-en').placeholder = t.instructions_en_placeholder;
    document.getElementById('save-recipe-btn').textContent = t.save_recipe;
    document.getElementById('cancel-form-btn').textContent = t.cancel;
   
    // Update category options
    const categorySelect = document.getElementById('recipe-category');
    if (categorySelect) {
        Array.from(categorySelect.options).forEach(option => {
            if (option.value && recipeCategories[currentLanguage][option.value]) {
                option.textContent = recipeCategories[currentLanguage][option.value];
            }
        });
    }
   
    // Update recipe selector
    updateRecipeSelector();
}

// True while the form holds an AI-parsed recipe the user is reviewing (affects the form title)
let reviewingParsedRecipe = false;

// Shared by the index and manage pages: recipe categories and recipe loading.

// Recipe categories
const recipeCategories = {
    he: {
        meat_fish: "בשר/דגים",
        pasta_sauces: "פסטה ורטבים",
        sides: "תוספות",
        salads: "סלטים",
        soups: "מרקים",
        desserts: "קינוחים",
        holidays: "חגים וחגיגות"
    },
    en: {
        meat_fish: "Meat/Fish",
        pasta_sauces: "Pasta & Sauces",
        sides: "Sides",
        salads: "Salads",
        soups: "Soups",
        desserts: "Desserts",
        holidays: "Holidays & Celebrations"
    }
};

// Recipe database with translations and categories
// Recipe data will be loaded from external JSON file
let recipes = {};
let recipeTranslations = {};
let recipeCategoryMap = {};

// Load recipes from external JSON file
async function loadRecipes() {
    try {
        const response = await fetch(API_ENDPOINTS.recipes);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        if (!data.recipes || !data.recipeTranslations || !data.recipeCategoryMap) {
            throw new Error('Invalid recipes.json structure');
        }
        
        recipes = data.recipes;
        recipeTranslations = data.recipeTranslations;
        recipeCategoryMap = data.recipeCategoryMap;
        
        // Initialize app after recipes are loaded
        initializeApp();
    } catch (error) {
        console.error('Error loading recipes:', error);
        // Show error message to user with more details
        const errorMsg = error.message || 'Unknown error';
        document.body.innerHTML = `
            <div class="p-8 text-center">
                <h1 class="text-2xl font-bold text-red-600 mb-4">Error loading recipes</h1>
                <p class="mt-4 text-gray-600 mb-2">Please make sure recipes.json file exists and is accessible.</p>
                <p class="text-sm text-gray-500">Error: ${errorMsg}</p>
                <p class="mt-4 text-sm text-gray-500">Make sure the Flask server is running on http://localhost:5001</p>
            </div>
        `;
    }
}

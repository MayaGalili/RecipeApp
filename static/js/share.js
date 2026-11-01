// Share page (single recipe view): servings, ingredients, shopping list, language.

// Recipe data from the server (JSON block in share.html)
const shareData = JSON.parse(document.getElementById('share-data').textContent);
const recipeData = shareData.recipe;
const recipeKey = shareData.recipeKey;
const translations = shareData.translations;

let currentLanguage = 'he';
let currentServings = 4;

// Language translations
const langTranslations = {
  he: {
    subtitle: "מתכון משותף",
    back_link: "← חזור לכל המתכונים",
    serving_selector_title: "בחר מספר מנות",
    serving_label: "מנות",
    ingredients_title: "מרכיבי המתכון",
    instructions_title: "הוראות הכנה",
    shopping_list_title: "רשימת קניות",
    print_text: "🖨️ הדפס רשימת קניות",
    reset_text: "🔄 איפוס סימונים",
    servings_text: "מנות",
    no_ingredients: "אין מרכיבים זמינים",
    no_instructions: "אין הוראות זמינות",
    no_shopping_items: "אין מרכיבים לרשימת קניות",
    mark_ingredients: "סמן מרכיבים כדי לראות אותם ברשימת הקניות",
    error_title: "מתכון לא נמצא",
    error_message: "המתכון שביקשת לא קיים או נמחק.",
    error_back: "חזור לדף הראשי"
  },
  en: {
    subtitle: "Shared Recipe",
    back_link: "← Back to All Recipes",
    serving_selector_title: "Choose Serving Size",
    serving_label: "servings",
    ingredients_title: "Recipe Ingredients",
    instructions_title: "Instructions",
    shopping_list_title: "Shopping List",
    print_text: "🖨️ Print Shopping List",
    reset_text: "🔄 Reset Selections",
    servings_text: "servings",
    no_ingredients: "No ingredients available",
    no_instructions: "No instructions available",
    no_shopping_items: "No items for shopping list",
    mark_ingredients: "Mark ingredients to see them in the shopping list",
    error_title: "Recipe Not Found",
    error_message: "The recipe you requested does not exist or has been deleted.",
    error_back: "Back to Home"
  }
};

// Update language texts
function updateLanguageTexts() {
  const lang = langTranslations[currentLanguage];
  const html = document.documentElement;
  
  // Update page direction
  if (currentLanguage === 'he') {
    html.setAttribute('dir', 'rtl');
    html.setAttribute('lang', 'he');
  } else {
    html.setAttribute('dir', 'ltr');
    html.setAttribute('lang', 'en');
  }
  
  // Update texts
  const subtitleEl = document.getElementById('subtitle');
  const backLinkEl = document.getElementById('back-link');
  if (subtitleEl) subtitleEl.textContent = lang.subtitle;
  if (backLinkEl) backLinkEl.textContent = lang.back_link;
  
  document.getElementById('serving-selector-title').textContent = lang.serving_selector_title;
  document.getElementById('serving-label').textContent = lang.serving_label;
  document.getElementById('ingredients-title').textContent = lang.ingredients_title;
  document.getElementById('instructions-title').textContent = lang.instructions_title;
  document.getElementById('shopping-list-title').textContent = lang.shopping_list_title;
  document.getElementById('print-text').textContent = lang.print_text;
  document.getElementById('reset-text').textContent = lang.reset_text;
  
  // Update preset buttons
  document.querySelectorAll('.preset-btn').forEach(btn => {
    const servings = btn.dataset.servings;
    btn.textContent = `${servings} ${lang.servings_text}`;
  });
  
  // Update recipe title
  document.getElementById('recipe-title').innerHTML = `${recipeData.emoji} ${translations[currentLanguage] || translations.he || translations.en}`;
  
  updateIngredients();
  updateInstructions();
  updateShoppingList();
}

// Language button handlers
document.querySelectorAll('.language-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    currentLanguage = btn.dataset.lang;
    document.querySelectorAll('.language-btn').forEach(b => {
      if (b.dataset.lang === currentLanguage) {
        b.classList.add('bg-orange-500', 'text-white');
        b.classList.remove('text-gray-600', 'hover:bg-gray-100');
      } else {
        b.classList.remove('bg-orange-500', 'text-white');
        b.classList.add('text-gray-600', 'hover:bg-gray-100');
      }
    });
    updateLanguageTexts();
  });
});

// Update ingredients display
function updateIngredients() {
  const ingredients = currentLanguage === 'he' ? (recipeData.ingredients?.he || recipeData.ingredientsHe) : (recipeData.ingredients?.en || recipeData.ingredientsEn);
  const container = document.getElementById('ingredients-list');
  container.innerHTML = '';
  
  if (!ingredients || ingredients.length === 0) {
    const lang = langTranslations[currentLanguage];
    container.innerHTML = `<p class="text-gray-500 text-center">${lang.no_ingredients}</p>`;
    return;
  }

  const defaultServings = recipeData.servings || 4;
  ingredients.forEach((ing, index) => {
    const adjustedAmount = (ing.amount * currentServings / defaultServings).toFixed(1);
    const item = document.createElement('div');
    item.className = 'ingredient-item bg-gray-50 rounded-lg p-4 flex items-center justify-between fade-in';
    item.innerHTML = `
      <div class="flex items-center gap-3">
        <input type="checkbox" class="ingredient-checkbox w-5 h-5 text-orange-500 rounded" data-ingredient="${index}" data-lang="${currentLanguage}">
        <span class="font-medium text-gray-800">${ing.name}</span>
      </div>
      <span class="text-gray-600">${adjustedAmount} ${ing.unit}</span>
    `;
    container.appendChild(item);
  });
}

// Update instructions display
function updateInstructions() {
  const instructions = currentLanguage === 'he' ? (recipeData.instructions?.he || recipeData.instructionsHe) : (recipeData.instructions?.en || recipeData.instructionsEn);
  const container = document.getElementById('instructions-list');
  container.innerHTML = '';
  
  if (!instructions || instructions.length === 0) {
    const lang = langTranslations[currentLanguage];
    container.innerHTML = `<p class="text-gray-500 text-center">${lang.no_instructions}</p>`;
    return;
  }

  instructions.forEach((instruction, index) => {
    const item = document.createElement('div');
    item.className = 'bg-gray-50 rounded-lg p-4 fade-in';
    item.innerHTML = `
      <div class="flex items-start gap-3">
        <span class="bg-orange-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">${index + 1}</span>
        <p class="text-gray-800 flex-1">${instruction}</p>
      </div>
    `;
    container.appendChild(item);
  });
}

// Update shopping list
function updateShoppingList() {
  const ingredients = currentLanguage === 'he' ? (recipeData.ingredients?.he || recipeData.ingredientsHe) : (recipeData.ingredients?.en || recipeData.ingredientsEn);
  const container = document.getElementById('shopping-list');
  container.innerHTML = '';
  
  const lang = langTranslations[currentLanguage];
  
  if (!ingredients || ingredients.length === 0) {
    container.innerHTML = `<p class="text-gray-500 text-center">${lang.no_shopping_items}</p>`;
    return;
  }

  const checkedItems = Array.from(document.querySelectorAll('.ingredient-checkbox:checked'))
    .map(cb => parseInt(cb.dataset.ingredient));

  if (checkedItems.length === 0) {
    container.innerHTML = `<p class="text-gray-500 text-center">${lang.mark_ingredients}</p>`;
    return;
  }

  checkedItems.forEach(index => {
    const ing = ingredients[index];
    if (!ing) return;
    
    const defaultServings = recipeData.servings || 4;
    const adjustedAmount = (ing.amount * currentServings / defaultServings).toFixed(1);
    const item = document.createElement('div');
    item.className = 'shopping-item bg-orange-50 border border-orange-200 rounded-lg p-3 flex items-center justify-between';
    item.innerHTML = `
      <span class="font-medium text-gray-800">${ing.name}</span>
      <span class="text-gray-600">${adjustedAmount} ${ing.unit}</span>
    `;
    container.appendChild(item);
  });
}

// Serving size controls
document.getElementById('increase-btn').addEventListener('click', () => {
  currentServings = Math.min(currentServings + 1, 20);
  document.getElementById('serving-count').textContent = currentServings;
  updateIngredients();
  updateShoppingList();
});

document.getElementById('decrease-btn').addEventListener('click', () => {
  currentServings = Math.max(currentServings - 1, 1);
  document.getElementById('serving-count').textContent = currentServings;
  updateIngredients();
  updateShoppingList();
});

// Preset buttons
document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    currentServings = parseInt(btn.dataset.servings);
    document.getElementById('serving-count').textContent = currentServings;
    updateIngredients();
    updateShoppingList();
  });
});

// Checkbox change handlers
document.addEventListener('change', (e) => {
  if (e.target.classList.contains('ingredient-checkbox')) {
    updateShoppingList();
  }
});

// Print button
document.getElementById('print-btn').addEventListener('click', () => {
  window.print();
});

// Reset button
document.getElementById('reset-btn').addEventListener('click', () => {
  document.querySelectorAll('.ingredient-checkbox').forEach(cb => cb.checked = false);
  updateShoppingList();
});

// Initialize
updateLanguageTexts();

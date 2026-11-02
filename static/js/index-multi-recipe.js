// Index page: multi-recipe selection, per-recipe servings and the combined shopping list.
// Ingredient scaling/combining lives in shopping-list-aggregate.js; rendering the list is
// updateShoppingList() in index-recipe-view.js.

const MIN_SERVINGS = 1;
const MAX_SERVINGS = 20;

// Add or remove a recipe from the selection (new recipes start at the default servings)
function toggleRecipeSelection(recipeKey) {
    if (selectedRecipes[recipeKey] !== undefined) {
        delete selectedRecipes[recipeKey];
    } else {
        selectedRecipes[recipeKey] = ShoppingListAggregate.DEFAULT_SERVINGS;
    }
    onSelectionChanged();
}

function setRecipeServings(recipeKey, servings) {
    if (selectedRecipes[recipeKey] === undefined) return;
    const value = parseInt(servings, 10);
    selectedRecipes[recipeKey] = Math.min(MAX_SERVINGS, Math.max(MIN_SERVINGS,
        Number.isFinite(value) ? value : ShoppingListAggregate.DEFAULT_SERVINGS));
    onSelectionChanged();
}

function clearRecipeSelection() {
    selectedRecipes = {};
    onSelectionChanged();
}

// Any change to the selection makes a generated list out of date, so hide it until
// the user generates again. Checkbox state of the cards is synced without a full rebuild.
function onSelectionChanged() {
    hideShoppingList();
    syncRecipeCheckboxes();
    renderSelectedRecipes();
    updateIngredients();
}

function syncRecipeCheckboxes() {
    document.querySelectorAll('#recipe-selector .recipe-card').forEach(card => {
        const checkbox = card.querySelector('.recipe-checkbox');
        checkbox.checked = selectedRecipes[card.dataset.recipe] !== undefined;
    });
}

// Build one "emoji name  [-] 4 [+]  ×" row
function createSelectedRecipeRow(recipeKey) {
    const t = translations[currentLanguage];
    const servings = selectedRecipes[recipeKey];

    const row = document.createElement('div');
    row.className = 'selected-recipe-item flex items-center justify-between gap-2 p-2 bg-orange-50 rounded-lg';

    const name = document.createElement('span');
    name.className = 'flex-1 font-medium text-gray-800 text-sm';
    name.textContent = `${recipes[recipeKey].emoji} ${recipeTranslations[currentLanguage][recipeKey]}`;

    const makeStepper = (text, label, delta) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'serving-button w-8 h-8 rounded-full text-white font-bold shadow ' + (delta < 0 ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600');
        btn.textContent = text;
        btn.setAttribute('aria-label', label);
        btn.disabled = servings + delta < MIN_SERVINGS || servings + delta > MAX_SERVINGS;
        btn.addEventListener('click', () => setRecipeServings(recipeKey, servings + delta));
        return btn;
    };

    const input = document.createElement('input');
    input.type = 'number';
    input.min = MIN_SERVINGS;
    input.max = MAX_SERVINGS;
    input.value = servings;
    input.className = 'recipe-servings w-14 px-1 py-1 border-2 border-gray-200 rounded text-center';
    input.setAttribute('aria-label', t.servings_text);
    input.addEventListener('change', () => setRecipeServings(recipeKey, input.value));

    const unit = document.createElement('span');
    unit.className = 'text-gray-600 text-sm';
    unit.textContent = t.servings_text;

    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'remove-recipe w-8 h-8 rounded-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold';
    remove.textContent = '×';
    remove.setAttribute('aria-label', t.remove_recipe);
    remove.title = t.remove_recipe;
    remove.addEventListener('click', () => toggleRecipeSelection(recipeKey));

    row.append(name, makeStepper('-', t.decrease_servings, -1), input, makeStepper('+', t.increase_servings, 1), unit, remove);
    return row;
}

// Render the selected-recipes summary and the enabled state of its buttons
function renderSelectedRecipes() {
    const t = translations[currentLanguage];
    const keys = Object.keys(selectedRecipes).filter(key => recipes[key]);

    document.getElementById('selected-recipes-title').textContent = t.selected_recipes_title;
    document.getElementById('generate-list-text').textContent = t.generate_list_text;
    document.getElementById('clear-selection-text').textContent = t.clear_selection_text;

    const empty = document.getElementById('selected-recipes-empty');
    empty.textContent = t.selected_empty;
    empty.style.display = keys.length ? 'none' : 'block';

    const list = document.getElementById('selected-recipes-list');
    list.innerHTML = '';
    keys.forEach(key => list.appendChild(createSelectedRecipeRow(key)));

    document.getElementById('generate-list-btn').disabled = keys.length === 0;
    document.getElementById('clear-selection-btn').disabled = keys.length === 0;
}

// "Recipe (4 servings), Recipe (6 servings)" for the print / copy headers
function selectedRecipesSummary() {
    const t = translations[currentLanguage];
    return Object.keys(selectedRecipes).filter(key => recipes[key])
        .map(key => `${recipeTranslations[currentLanguage][key]} (${selectedRecipes[key]} ${t.servings_text})`)
        .join(', ');
}

function hideShoppingList() {
    shoppingListGenerated = false;
    document.getElementById('shopping-list-card').style.display = 'none';
}

// Build and reveal the combined shopping list for the current selection
function generateShoppingList() {
    if (Object.keys(selectedRecipes).length === 0) return;
    shoppingListGenerated = true;
    updateShoppingList();
    const card = document.getElementById('shopping-list-card');
    card.style.display = 'block';
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

document.getElementById('generate-list-btn').addEventListener('click', generateShoppingList);
document.getElementById('clear-selection-btn').addEventListener('click', clearRecipeSelection);

// Index page: recipe selector, ingredients, instructions and shopping list.

// Calculate scaled amount (rounded for display)
function scaleAmount(baseAmount, servings) {
    return ShoppingListAggregate.roundAmount(ShoppingListAggregate.scaleExact(baseAmount, servings));
}

// Format amount for display
function formatAmount(amount) {
    if (amount % 1 === 0) {
        return amount.toString();
    } else if (amount % 0.5 === 0) {
        return amount.toString();
    } else if (amount % 0.25 === 0) {
        return amount.toString();
    } else {
        return amount.toFixed(1);
    }
}

// Trim, collapse whitespace and lower-case text for search matching
function normalizeSearchText(text) {
    return String(text || '').trim().replace(/\s+/g, ' ').toLowerCase();
}

// True if the recipe's Hebrew or English name contains the query (empty query matches all)
function recipeMatchesQuery(names, query) {
    const normalizedQuery = normalizeSearchText(query);
    if (!normalizedQuery) {
        return true;
    }
    return Object.values(names).some(name => normalizeSearchText(name).includes(normalizedQuery));
}

// Decorative sprout shown at the bottom of every recipe card
const LEAF_ICON = '<svg viewBox="0 0 40 16" fill="none" aria-hidden="true"><path d="M20 15V9" stroke="#6b9a2b" stroke-width="1.6" stroke-linecap="round"/><path d="M20 10C14 10 9 7 6 2c6-1 12 1 14 8z" fill="#8bb542"/><path d="M20 10c6 0 11-3 14-8-6-1-12 1-14 8z" fill="#6b9a2b"/></svg>';
const CHEVRON_ICON = '<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>';

// Create recipe selector buttons organized by categories
function createRecipeSelector() {
    const recipeSelector = document.getElementById('recipe-selector');
    recipeSelector.innerHTML = '';

    let matchCount = 0;
    const searching = normalizeSearchText(searchQuery) !== '';

    // Create categories in the display order of recipeCategories (the JSON feed may reorder keys),
    // followed by any category the feed has that the UI doesn't know about
    const knownKeys = Object.keys(recipeCategories[currentLanguage]);
    const categoryOrder = knownKeys.filter(key => recipeCategoryMap[key])
        .concat(Object.keys(recipeCategoryMap).filter(key => !knownKeys.includes(key)));
    categoryOrder.forEach(categoryKey => {
        const matchingKeys = recipeCategoryMap[categoryKey].filter(recipeKey =>
            recipeMatchesQuery({
                he: recipeTranslations.he[recipeKey],
                en: recipeTranslations.en[recipeKey]
            }, searchQuery)
        );
        if (matchingKeys.length === 0) {
            return;
        }
        matchCount += matchingKeys.length;

        // A search always shows its matches, even inside a folded category
        const collapsed = collapsedCategories.has(categoryKey) && !searching;

        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category-section' + (collapsed ? ' is-collapsed' : '');
        categoryDiv.dataset.category = categoryKey;

        // Category header: title, illustration and fold toggle
        const categoryHead = document.createElement('div');
        categoryHead.className = 'category-head';

        const categoryTitle = document.createElement('h3');
        categoryTitle.className = 'category-title';
        categoryTitle.textContent = recipeCategories[currentLanguage][categoryKey];

        const categoryArt = document.createElement('img');
        categoryArt.className = 'category-art';
        categoryArt.src = `${APP_CONFIG.categoryImages}${categoryKey}.png`;
        categoryArt.alt = '';
        categoryArt.loading = 'lazy';
        categoryArt.addEventListener('error', () => categoryArt.remove());

        const toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'category-toggle';
        toggle.innerHTML = CHEVRON_ICON;
        toggle.setAttribute('aria-expanded', String(!collapsed));
        toggle.setAttribute('aria-label', `${translations[currentLanguage].toggle_category}: ${categoryTitle.textContent}`);
        toggle.addEventListener('click', () => {
            const nowCollapsed = !categoryDiv.classList.contains('is-collapsed');
            categoryDiv.classList.toggle('is-collapsed', nowCollapsed);
            toggle.setAttribute('aria-expanded', String(!nowCollapsed));
            if (nowCollapsed) {
                collapsedCategories.add(categoryKey);
            } else {
                collapsedCategories.delete(categoryKey);
            }
        });

        categoryHead.append(categoryTitle, categoryArt, toggle);
        categoryDiv.appendChild(categoryHead);

        // Recipe cards grid
        const recipesGrid = document.createElement('div');
        recipesGrid.className = 'recipes-grid';

        matchingKeys.forEach(recipeKey => {
            const recipeName = recipeTranslations[currentLanguage][recipeKey];

            // Container for the recipe button, selection checkbox and share button
            const recipeContainer = document.createElement('div');
            recipeContainer.className = 'recipe-card group';
            recipeContainer.dataset.recipe = recipeKey;

            // Create checkbox for multi-recipe selection
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'recipe-checkbox';
            checkbox.checked = selectedRecipes[recipeKey] !== undefined;
            checkbox.setAttribute('aria-label', recipeName);
            checkbox.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleRecipeSelection(recipeKey);
            });

            const button = document.createElement('button');
            const isActive = recipeKey === currentRecipe;
            button.type = 'button';
            button.className = 'recipe-button' + (isActive ? ' active' : '');
            const nameSpan = document.createElement('span');
            nameSpan.className = 'recipe-name';
            nameSpan.textContent = recipeName;
            const leaf = document.createElement('span');
            leaf.className = 'recipe-leaf';
            leaf.innerHTML = LEAF_ICON;
            button.append(nameSpan, leaf);
            button.addEventListener('click', () => {
                currentRecipe = recipeKey;
                updateRecipeSelector();
                updateAll();
            });

            // Share button (top corner of the card, a sibling of the main button)
            const shareBtn = document.createElement('button');
            shareBtn.type = 'button';
            shareBtn.className = 'share-btn';
            shareBtn.innerHTML = '🔗';
            shareBtn.title = 'שתף מתכון';
            shareBtn.setAttribute('aria-label', 'שתף מתכון');
            shareBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                copyShareLink(recipeKey);
            });

            recipeContainer.append(checkbox, button, shareBtn);
            recipesGrid.appendChild(recipeContainer);
        });

        categoryDiv.appendChild(recipesGrid);
        recipeSelector.appendChild(categoryDiv);
    });

    if (matchCount === 0) {
        const noResults = document.createElement('p');
        noResults.className = 'no-results';
        noResults.textContent = translations[currentLanguage].no_results;
        recipeSelector.appendChild(noResults);
    }
}

// Update recipe selector active state
function updateRecipeSelector() {
    // Recreate the entire selector to update language
    createRecipeSelector();
}

// Servings used for a recipe: its selected servings, or the default
function servingsFor(recipeKey) {
    return selectedRecipes[recipeKey] || ShoppingListAggregate.DEFAULT_SERVINGS;
}

// Update ingredients display
function updateIngredients() {
    const ingredientsList = document.getElementById('ingredients-list');
    ingredientsList.innerHTML = '';

    const recipe = recipes[currentRecipe];
    const ingredients = recipe.ingredients[currentLanguage] || recipe.ingredients.he;
    const servings = servingsFor(currentRecipe);
    const t = translations[currentLanguage];
    document.getElementById('ingredients-title').textContent = `${t.ingredients_title} (${servings} ${t.servings_text})`;

    ingredients.forEach((ingredient, index) => {
        const scaledAmount = scaleAmount(ingredient.amount, servings);
        const ingredientDiv = document.createElement('div');
        ingredientDiv.className = 'ingredient-item flex justify-between items-center p-3 bg-gray-50 rounded-lg';
        ingredientDiv.innerHTML = `
            <span class="font-medium text-gray-800">${ingredient.name}</span>
            <span class="text-orange-600 font-semibold">${formatAmount(scaledAmount)} ${ingredient.unit}</span>
        `;
        ingredientDiv.classList.add('fade-in');
        ingredientsList.appendChild(ingredientDiv);
    });
}

// Update instructions display
function updateInstructions() {
    const instructionsList = document.getElementById('instructions-list');
    instructionsList.innerHTML = '';

    const recipe = recipes[currentRecipe];
    const instructions = recipe.instructions[currentLanguage] || recipe.instructions.he;
   
    instructions.forEach((instruction, index) => {
        const instructionDiv = document.createElement('div');
        instructionDiv.className = 'instruction-item flex items-start p-3 bg-blue-50 rounded-lg';
        const marginClass = (currentLanguage === 'he') ? 'mr-3' : 'ml-3';
        instructionDiv.innerHTML = `
            <span class="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold ${marginClass}">${index + 1}</span>
            <span class="text-gray-800 leading-relaxed">${instruction}</span>
        `;
        instructionDiv.classList.add('fade-in');
        instructionsList.appendChild(instructionDiv);
    });
}

// Render the combined shopping list for the selected recipes (only called from "Generate")
function updateShoppingList() {
    const shoppingList = document.getElementById('shopping-list');
    shoppingList.innerHTML = '';

    const categories = ShoppingListAggregate.aggregateIngredients(selectedRecipes, recipes, currentLanguage);

    // Display by categories
    categories.forEach(({ category, items }, categoryIndex) => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'mb-4';
       
        const categoryTitle = document.createElement('h3');
        categoryTitle.className = 'font-semibold text-gray-700 mb-2 text-lg border-b border-gray-200 pb-1';
        categoryTitle.textContent = category;
        categoryDiv.appendChild(categoryTitle);

        items.forEach((item, itemIndex) => {
            const itemId = `item-${categoryIndex}-${itemIndex}`;
            const itemDiv = document.createElement('div');
            itemDiv.className = 'shopping-item flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all duration-200';
            const checkboxMargin = (currentLanguage === 'he') ? 'ml-3' : 'mr-3';
            itemDiv.innerHTML = `
                <input type="checkbox" id="${itemId}" class="${checkboxMargin} w-5 h-5 text-green-600 bg-gray-100 border-gray-300 rounded focus:ring-green-500 focus:ring-2 cursor-pointer">
                <label for="${itemId}" class="flex-1 flex justify-between items-center cursor-pointer">
                    <span class="text-gray-800 font-medium">${item.name}</span>
                    <span class="text-orange-600 font-semibold">${formatAmount(item.amount)} ${item.unit}</span>
                </label>
            `;
           
            // Add checkbox functionality
            const checkbox = itemDiv.querySelector('input[type="checkbox"]');
            const label = itemDiv.querySelector('label');
           
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    label.style.textDecoration = 'line-through';
                    label.style.opacity = '0.6';
                    itemDiv.style.backgroundColor = '#f0fdf4';
                    itemDiv.style.borderColor = '#22c55e';
                } else {
                    label.style.textDecoration = 'none';
                    label.style.opacity = '1';
                    itemDiv.style.backgroundColor = '';
                    itemDiv.style.borderColor = '#d1d5db';
                }
            });
           
            categoryDiv.appendChild(itemDiv);
        });

        categoryDiv.classList.add('fade-in');
        shoppingList.appendChild(categoryDiv);
    });
}

// Update details (the shopping list is only rebuilt by the Generate button)
function updateAll() {
    updateIngredients();
    updateInstructions();
}

// Index page: recipe selector, ingredients, instructions and shopping list.

// Calculate scaled amount
function scaleAmount(baseAmount, servings) {
    const scaleFactor = servings / 4;
    const scaledAmount = baseAmount * scaleFactor;
   
    // Round to reasonable precision
    if (scaledAmount < 1) {
        return Math.round(scaledAmount * 10) / 10;
    } else if (scaledAmount < 10) {
        return Math.round(scaledAmount * 4) / 4;
    } else {
        return Math.round(scaledAmount * 2) / 2;
    }
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

// Create recipe selector buttons organized by categories
function createRecipeSelector() {
    const recipeSelector = document.getElementById('recipe-selector');
    recipeSelector.innerHTML = '';

    let matchCount = 0;

    // Create categories
    Object.keys(recipeCategoryMap).forEach(categoryKey => {
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

        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category-section';
       
        // Category title
        const categoryTitle = document.createElement('div');
        categoryTitle.className = 'category-title';
        categoryTitle.textContent = recipeCategories[currentLanguage][categoryKey];
        categoryDiv.appendChild(categoryTitle);
       
        // Recipe buttons grid
        const recipesGrid = document.createElement('div');
        recipesGrid.className = 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3';
       
        matchingKeys.forEach(recipeKey => {
            const recipe = recipes[recipeKey];
            
            // Create container for recipe button and share button
            const recipeContainer = document.createElement('div');
            recipeContainer.className = 'relative group';
            
            const button = document.createElement('button');
            const isActive = recipeKey === currentRecipe;
            button.className = `recipe-button w-full p-4 bg-white border-2 rounded-lg text-center shadow-md transition-all duration-200 ${isActive ? 'active border-orange-500 bg-orange-50' : 'border-gray-200 hover:border-orange-300 hover:shadow-lg'}`;
            button.style.position = 'relative';
            button.style.overflow = 'visible';
            button.innerHTML = `
                <div class="text-3xl mb-2">${recipe.emoji}</div>
                <div class="text-sm font-medium ${isActive ? 'text-white' : 'text-gray-700'}">${recipeTranslations[currentLanguage][recipeKey]}</div>
            `;
            button.addEventListener('click', () => {
                currentRecipe = recipeKey;
                updateRecipeSelector();
                updateAll();
            });
            
            // Create share button (top-right corner inside the button)
            const shareBtn = document.createElement('button');
            shareBtn.className = 'w-8 h-8 bg-blue-500 hover:bg-blue-600 text-white rounded-full flex items-center justify-center shadow-lg hover:shadow-xl opacity-0 group-hover:opacity-100 transition-all duration-200 transform hover:scale-110';
            shareBtn.style.position = 'absolute';
            shareBtn.style.top = '0.5rem';
            shareBtn.style.right = '0.5rem';
            shareBtn.style.left = 'auto';
            shareBtn.style.zIndex = '20';
            shareBtn.innerHTML = '🔗';
            shareBtn.title = 'שתף מתכון';
            shareBtn.style.fontSize = '0.875rem';
            shareBtn.style.lineHeight = '1';
            shareBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                copyShareLink(recipeKey);
            });
            
            button.appendChild(shareBtn);
            recipeContainer.appendChild(button);
            
            recipesGrid.appendChild(recipeContainer);
        });
       
        categoryDiv.appendChild(recipesGrid);
        recipeSelector.appendChild(categoryDiv);
    });

    if (matchCount === 0) {
        const noResults = document.createElement('p');
        noResults.className = 'text-center text-gray-600';
        noResults.textContent = translations[currentLanguage].no_results;
        recipeSelector.appendChild(noResults);
    }
}

// Update recipe selector active state
function updateRecipeSelector() {
    // Recreate the entire selector to update language
    createRecipeSelector();
}

// Update ingredients display
function updateIngredients() {
    const ingredientsList = document.getElementById('ingredients-list');
    ingredientsList.innerHTML = '';

    const recipe = recipes[currentRecipe];
    const ingredients = recipe.ingredients[currentLanguage] || recipe.ingredients.he;
   
    ingredients.forEach((ingredient, index) => {
        const scaledAmount = scaleAmount(ingredient.amount, currentServings);
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

// Update shopping list
function updateShoppingList() {
    const shoppingList = document.getElementById('shopping-list');
    shoppingList.innerHTML = '';

    const recipe = recipes[currentRecipe];
    const ingredients = recipe.ingredients[currentLanguage] || recipe.ingredients.he;
   
    // Group ingredients by category
    const categories = {};
    ingredients.forEach((ingredient, index) => {
        if (!categories[ingredient.category]) {
            categories[ingredient.category] = [];
        }
        const scaledAmount = scaleAmount(ingredient.amount, currentServings);
        categories[ingredient.category].push({
            name: ingredient.name,
            amount: scaledAmount,
            unit: ingredient.unit,
            id: `item-${currentRecipe}-${index}`
        });
    });

    // Display by categories
    Object.keys(categories).forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'mb-4';
       
        const categoryTitle = document.createElement('h3');
        categoryTitle.className = 'font-semibold text-gray-700 mb-2 text-lg border-b border-gray-200 pb-1';
        categoryTitle.textContent = category;
        categoryDiv.appendChild(categoryTitle);

        categories[category].forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'shopping-item flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all duration-200';
            const checkboxMargin = (currentLanguage === 'he') ? 'ml-3' : 'mr-3';
            itemDiv.innerHTML = `
                <input type="checkbox" id="${item.id}" class="${checkboxMargin} w-5 h-5 text-green-600 bg-gray-100 border-gray-300 rounded focus:ring-green-500 focus:ring-2 cursor-pointer">
                <label for="${item.id}" class="flex-1 flex justify-between items-center cursor-pointer">
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

// Update serving count display
function updateServingDisplay() {
    document.getElementById('serving-count').textContent = currentServings;
}

// Update all displays
function updateAll() {
    updateServingDisplay();
    updateIngredients();
    updateInstructions();
    updateShoppingList();
}

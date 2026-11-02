// Manage page: recipe list (grouped by category) and delete.

// Create recipe selector buttons organized by categories
function createRecipeSelector() {
    const recipeSelector = document.getElementById('recipe-selector');
    recipeSelector.innerHTML = '';

    // Create categories
    Object.keys(recipeCategoryMap).forEach(categoryKey => {
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
       
        recipeCategoryMap[categoryKey].forEach(recipeKey => {
            const recipe = recipes[recipeKey];
            
            // Create container for recipe button and delete button
            const container = document.createElement('div');
            container.className = 'relative group';
            container.style.position = 'relative';
            
            const button = document.createElement('button');
            button.className = `recipe-button w-full p-4 bg-white border-2 border-gray-200 rounded-lg text-center hover:border-orange-300 shadow-md hover:shadow-lg transition-all duration-200 ${recipeKey === currentRecipe ? 'border-orange-500 bg-orange-50' : ''}`;
            button.style.position = 'relative';
            button.style.overflow = 'visible';
            button.innerHTML = `
                <div class="text-3xl mb-2">${recipe.emoji}</div>
                <div class="text-sm font-medium text-gray-700">${recipeTranslations[currentLanguage][recipeKey]}</div>
            `;
            button.addEventListener('click', () => {
                // Edit recipe instead of selecting it
                editRecipe(recipeKey);
            });
            
            // Create delete button (top-right corner inside the button)
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center shadow-lg hover:shadow-xl opacity-70 group-hover:opacity-100 transition-all duration-200 transform hover:scale-110';
            deleteBtn.style.position = 'absolute';
            deleteBtn.style.top = '0.5rem';
            deleteBtn.style.right = '0.5rem';
            deleteBtn.style.left = 'auto';
            deleteBtn.style.zIndex = '20';
            deleteBtn.innerHTML = '🗑️';
            deleteBtn.title = translations[currentLanguage].delete_recipe_title;
            deleteBtn.style.fontSize = '0.875rem';
            deleteBtn.style.lineHeight = '1';
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent triggering the recipe button click
                deleteRecipe(recipeKey);
            });
            
            button.appendChild(deleteBtn);
            container.appendChild(button);
            recipesGrid.appendChild(container);
        });
       
        categoryDiv.appendChild(recipesGrid);
        recipeSelector.appendChild(categoryDiv);
    });
}

// Update recipe selector active state
function updateRecipeSelector() {
    // Recreate the entire selector to update language
    createRecipeSelector();
}

// Delete recipe function
async function deleteRecipe(recipeKey) {
    // Get recipe name for confirmation message
    const recipeName = recipeTranslations[currentLanguage][recipeKey] || recipeKey;
    
    // Confirm deletion
    const t = translations[currentLanguage];
    const confirmMessage = t.delete_confirm.replace('{name}', recipeName);
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        const response = await apiFetch(API_ENDPOINTS.deleteRecipe, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                recipeKey: recipeKey
            })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to delete recipe');
        }
        
        // Reload recipes from server
        await loadRecipes();
        
        // Update UI
        if (currentRecipe === recipeKey) {
            // If deleted recipe was the current one, select first available recipe
            const allRecipeKeys = Object.keys(recipes);
            if (allRecipeKeys.length > 0) {
                currentRecipe = allRecipeKeys[0];
            } else {
                currentRecipe = null;
            }
        }
        
        // Recreate recipe selector
        createRecipeSelector();
        
        // Show success message
        const t = translations[currentLanguage];
        const successMessage = t.delete_success.replace('{name}', recipeName);
        alert(successMessage);
        
    } catch (error) {
        console.error('Error deleting recipe:', error);
        const t = translations[currentLanguage];
        const errorMessage = t.delete_error.replace('{error}', error.message);
        alert(errorMessage);
    }
}

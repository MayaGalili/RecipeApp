// Manage page: AI free-text import (parse, then fill the editable form).

// Parse free text recipe using LLM

async function parseFreeTextRecipe() {
    const freeText = document.getElementById('free-text-recipe').value.trim();
    const parseBtn = document.getElementById('parse-recipe-btn');
    const parseBtnText = document.getElementById('parse-btn-text');
    const parseBtnLoading = document.getElementById('parse-btn-loading');
    const parseError = document.getElementById('parse-error');
    
    // Hide previous results
    parseError.classList.add('hidden');
    
    const t = translations[currentLanguage];
    
    if (!freeText) {
        parseError.textContent = t.parse_error_empty;
        parseError.classList.remove('hidden');
        return;
    }
    
    // Show loading state
    parseBtn.disabled = true;
    parseBtnText.classList.add('hidden');
    parseBtnLoading.classList.remove('hidden');
    
    try {
        const response = await apiFetch(APP_CONFIG.parseRecipe, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ freeText: freeText })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'שגיאה בפרסור המתכון');
        }
        
        // Open the editable form directly, pre-filled with the parsed recipe
        fillFormFromParsedRecipe(data.parsedRecipe);

    } catch (error) {
        const t = translations[currentLanguage];
        parseError.textContent = t.parse_error.replace('{error}', error.message);
        parseError.classList.remove('hidden');
    } finally {
        // Reset loading state
        parseBtn.disabled = false;
        parseBtnText.classList.remove('hidden');
        parseBtnLoading.classList.add('hidden');
    }
}

// Fill the form with a parsed recipe so the user can review and edit it before saving
function fillFormFromParsedRecipe(parsedRecipeData) {
    // A parsed recipe is always a new recipe: leave edit mode and clear stale field values
    editingRecipeKey = null;
    document.getElementById('recipe-form').reset();
    document.getElementById('form-message').classList.add('hidden');

    // Fill form fields
    document.getElementById('recipe-name-he').value = parsedRecipeData.nameHe || '';
    document.getElementById('recipe-name-en').value = parsedRecipeData.nameEn || '';
    setRecipeEmoji(parsedRecipeData.emoji || '🍳');
    document.getElementById('recipe-emoji-custom').value = '';
    document.getElementById('recipe-category').value = parsedRecipeData.category || 'meat_fish';
    
    // Fill ingredients
    if (parsedRecipeData.ingredientsHe && parsedRecipeData.ingredientsHe.length > 0) {
        const ingredientsHeText = parsedRecipeData.ingredientsHe.map(ing => 
            `${ing.name}, ${ing.amount}, ${ing.unit}, ${ing.category}`
        ).join('\n');
        document.getElementById('ingredients-he').value = ingredientsHeText;
    }
    
    if (parsedRecipeData.ingredientsEn && parsedRecipeData.ingredientsEn.length > 0) {
        const ingredientsEnText = parsedRecipeData.ingredientsEn.map(ing => 
            `${ing.name}, ${ing.amount}, ${ing.unit}, ${ing.category}`
        ).join('\n');
        document.getElementById('ingredients-en').value = ingredientsEnText;
    }
    
    // Fill instructions
    if (parsedRecipeData.instructionsHe && parsedRecipeData.instructionsHe.length > 0) {
        document.getElementById('instructions-he').value = parsedRecipeData.instructionsHe.join('\n');
    }
    
    if (parsedRecipeData.instructionsEn && parsedRecipeData.instructionsEn.length > 0) {
        document.getElementById('instructions-en').value = parsedRecipeData.instructionsEn.join('\n');
    }
    
    // Show the form with the review title
    reviewingParsedRecipe = true;
    document.getElementById('add-recipe-title').textContent = translations[currentLanguage].review_recipe_title;
    document.getElementById('add-recipe-form').classList.remove('hidden');
    document.getElementById('free-text-recipe').value = '';
    
    // Scroll to form
    document.getElementById('add-recipe-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

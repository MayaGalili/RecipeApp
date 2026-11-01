// Manage page: add/edit recipe form (parsing, validation, save, emoji picker, edit mode).

// Parse ingredients from textarea
function parseIngredients(text, lang) {
    if (!text.trim()) return [];
    const lines = text.split('\n').filter(line => line.trim());
    return lines.map(line => {
        const parts = line.split(',').map(p => p.trim());
        if (parts.length >= 4) {
            return {
                name: parts[0],
                amount: parseFloat(parts[1]),
                unit: parts[2],
                category: parts[3]
            };
        }
        return null;
    }).filter(item => item !== null);
}

// Parse instructions from textarea
function parseInstructions(text) {
    if (!text.trim()) return [];
    return text.split('\n').filter(line => line.trim());
}

// Generate recipe key from English name
function generateRecipeKey(recipeNameEn) {
    if (!recipeNameEn) return '';
    
    // Convert to lowercase, replace spaces and special chars with underscores
    let key = recipeNameEn
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9\s]/g, '') // Remove special characters
        .replace(/\s+/g, '_') // Replace spaces with underscores
        .replace(/_+/g, '_') // Replace multiple underscores with single
        .replace(/^_|_$/g, ''); // Remove leading/trailing underscores
    
    // If key is empty, use a default
    if (!key) {
        key = 'recipe';
    }
    
    // Check if key already exists, if so add a number suffix
    let finalKey = key;
    let counter = 1;
    while (recipes[finalKey]) {
        finalKey = `${key}_${counter}`;
        counter++;
    }
    
    return finalKey;
}

// Handle recipe form submission
async function handleRecipeSubmit(event) {
    event.preventDefault();
    
    const formMessage = document.getElementById('form-message');
    formMessage.classList.add('hidden');
    
    const recipeNameHe = document.getElementById('recipe-name-he').value.trim();
    const recipeNameEn = document.getElementById('recipe-name-en').value.trim();
    const emoji = document.getElementById('recipe-emoji').value.trim();
    const category = document.getElementById('recipe-category').value;
    const ingredientsHe = parseIngredients(document.getElementById('ingredients-he').value, 'he');
    const ingredientsEn = parseIngredients(document.getElementById('ingredients-en').value, 'en');
    const instructionsHe = parseInstructions(document.getElementById('instructions-he').value);
    const instructionsEn = parseInstructions(document.getElementById('instructions-en').value);

    // Validate
    if (!recipeNameHe || !recipeNameEn || !emoji || !category) {
        showFormMessage(translations[currentLanguage].validation_required, 'error');
        return;
    }

    // Generate recipe key automatically (only for new recipes)
    let recipeKey;
    if (editingRecipeKey) {
        recipeKey = editingRecipeKey;
    } else {
        recipeKey = generateRecipeKey(recipeNameEn);
    }

    if (ingredientsHe.length === 0 || ingredientsEn.length === 0) {
        showFormMessage(translations[currentLanguage].validation_ingredients, 'error');
        return;
    }

    // Create recipe object
    const newRecipe = {
        name: `${emoji} ${recipeNameHe}`,
        emoji: emoji,
        ingredients: {
            he: ingredientsHe,
            en: ingredientsEn
        },
        instructions: {
            he: instructionsHe,
            en: instructionsEn
        }
    };

    // Send to server
    try {
        const endpoint = editingRecipeKey ? API_ENDPOINTS.updateRecipe : API_ENDPOINTS.addRecipe;
        const method = editingRecipeKey ? 'PUT' : 'POST';
        
        const response = await apiFetch(endpoint, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                recipeKey: recipeKey,
                recipe: newRecipe,
                category: category,
                translations: {
                    he: recipeNameHe,
                    en: recipeNameEn
                }
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save recipe');
        }

        // Reload recipes and update UI
        await loadRecipes();
        
        // Show success message
        const recipeName = recipeNameHe;
        const isEdit = editingRecipeKey !== null;
        const t = translations[currentLanguage];
        const successMessage = isEdit 
            ? t.save_success_edit.replace('{name}', recipeName)
            : t.save_success_new.replace('{name}', recipeName);
        
        showFormMessage(successMessage, 'success');
        alert(successMessage);
        
        // Celebrate with food confetti only for new recipes
        if (!isEdit) {
        celebrateWithFoodConfetti();
        }
        
        // Reload recipes and update UI
        await loadRecipes();
        createRecipeSelector();
        
        // Reset editing state
        editingRecipeKey = null;
        
        // Update form title back to "Add Recipe"
        reviewingParsedRecipe = false;
        const formTitle = document.getElementById('add-recipe-title');
        formTitle.textContent = translations[currentLanguage].add_recipe_title;
        
        // Wait a bit before closing form so user can see the message
        setTimeout(() => {
            // Reset form
            document.getElementById('recipe-form').reset();
            document.getElementById('add-recipe-form').classList.add('hidden');
            document.getElementById('form-message').classList.add('hidden');
        }, 3000);
        
    } catch (error) {
        console.error('Error saving recipe:', error);
        const t = translations[currentLanguage];
        showFormMessage(t.save_error.replace('{error}', error.message), 'error');
    }
}

// Show form message
function showFormMessage(message, type) {
    const formMessage = document.getElementById('form-message');
    formMessage.textContent = message;
    formMessage.className = `mt-4 p-4 rounded-lg ${type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`;
    formMessage.classList.remove('hidden');
}

// Celebrate with food emoji confetti
function celebrateWithFoodConfetti() {
    // Food emojis
    const foodEmojis = ['🍳', '🥘', '🍲', '🍜', '🍝', '🍕', '🍔', '🌮', '🌯', '🥙', '🥗', '🍱', '🍣', '🍛', '🍙', '🍚', '🍞', '🥐', '🥖', '🥨', '🧀', '🥚', '🍳', '🥞', '🧇', '🥓', '🥩', '🍗', '🍖', '🌭', '🍟', '🍿', '🧂', '🥜', '🍪', '🍩', '🍰', '🎂', '🧁', '🍫', '🍬', '🍭', '🍮', '🍯', '🍼', '🥛', '☕', '🍵', '🧃', '🥤', '🍶', '🍺', '🍻', '🥂', '🍷', '🥃', '🍸', '🍹', '🧉', '🍾', '🧊', '🥟', '🥠', '🥡', '🦀', '🦞', '🦐', '🦑', '🦪', '🍤', '🍥', '🥮', '🍢', '🍡', '🍧', '🍨', '🍦', '🥧', '🍰', '🧁', '🍮', '🍭', '🍬', '🍫', '🍿', '🍩', '🍪', '🌰', '🥜', '🍯', '🥛', '🍼', '☕', '🍵', '🧃', '🥤', '🍶', '🍺', '🍻', '🥂', '🍷', '🥃', '🍸', '🍹', '🧉', '🍾', '🧊'];
    
    // Create falling emojis - more visible
    for (let i = 0; i < 60; i++) {
        setTimeout(() => {
            const emoji = document.createElement('div');
            emoji.className = 'falling-emoji';
            emoji.textContent = foodEmojis[Math.floor(Math.random() * foodEmojis.length)];
            emoji.style.left = Math.random() * 100 + '%';
            emoji.style.top = '-50px';
            emoji.style.animationDelay = '0s';
            emoji.style.animationDuration = (2.5 + Math.random() * 1.5) + 's';
            emoji.style.transform = `rotate(${Math.random() * 360}deg)`;
            document.body.appendChild(emoji);
            
            // Remove emoji after animation
            setTimeout(() => {
                if (emoji.parentNode) {
                    emoji.remove();
                }
            }, 5000);
        }, i * 25);
    }
    
    // Regular confetti bursts (colorful)
    if (typeof confetti !== 'undefined') {
        // Left burst
        confetti({
            particleCount: 100,
            angle: 60,
            spread: 55,
            origin: { x: 0 },
            colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        });
        
        // Right burst
        confetti({
            particleCount: 100,
            angle: 120,
            spread: 55,
            origin: { x: 1 },
            colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        });
        
        // Center burst
        setTimeout(() => {
            confetti({
                particleCount: 150,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
            });
        }, 250);
        
        // Additional bursts for more celebration
        setTimeout(() => {
            confetti({
                particleCount: 80,
                angle: 60,
                spread: 55,
                origin: { x: 0 },
                colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
            });
        }, 500);
        
        setTimeout(() => {
            confetti({
                particleCount: 80,
                angle: 120,
                spread: 55,
                origin: { x: 1 },
                colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
            });
        }, 750);
    }
}

// Select an emoji in the form. If it isn't one of the predefined options
// (e.g. an AI-chosen 🍅), add it as an option so it stays selected.
function setRecipeEmoji(emoji) {
    const select = document.getElementById('recipe-emoji');
    select.querySelectorAll('option[data-custom]').forEach(option => option.remove());
    if (emoji && !Array.from(select.options).some(option => option.value === emoji)) {
        const option = document.createElement('option');
        option.value = emoji;
        option.textContent = emoji;
        option.dataset.custom = 'true';
        select.appendChild(option);
    }
    select.value = emoji || '';
}

// Emoji-only text (pictographs, flags, skin tones, ZWJ/variation selectors), at most 10 characters (DB column size)
function isValidEmoji(text) {
    return text !== '' && Array.from(text).length <= 10 &&
        text.replace(/[\p{Extended_Pictographic}\p{Regional_Indicator}\p{Emoji_Modifier}‍️]/gu, '') === '';
}

// Toggle form visibility
function toggleForm() {
    editingRecipeKey = null;
    reviewingParsedRecipe = false;
    document.getElementById('add-recipe-title').textContent = translations[currentLanguage].add_recipe_title;
    const form = document.getElementById('add-recipe-form');
    form.classList.toggle('hidden');
    // Reset form when toggling
    if (form.classList.contains('hidden')) {
        document.getElementById('recipe-form').reset();
        setRecipeEmoji('');
        document.getElementById('form-message').classList.add('hidden');
    }
}

// Edit recipe function
function editRecipe(recipeKey) {
    editingRecipeKey = recipeKey;
    const recipe = recipes[recipeKey];
    const recipeNameHe = recipeTranslations['he'][recipeKey] || '';
    const recipeNameEn = recipeTranslations['en'][recipeKey] || '';
    
    // Fill form with recipe data
    document.getElementById('recipe-name-he').value = recipeNameHe;
    document.getElementById('recipe-name-en').value = recipeNameEn;
    setRecipeEmoji(recipe.emoji);
    document.getElementById('recipe-emoji-custom').value = '';
    
    // Find category
    let category = '';
    for (const cat in recipeCategoryMap) {
        if (recipeCategoryMap[cat].includes(recipeKey)) {
            category = cat;
            break;
        }
    }
    document.getElementById('recipe-category').value = category;
    
    // Fill ingredients
    const ingredientsHe = recipe.ingredients.he.map(ing => 
        `${ing.name}, ${ing.amount}, ${ing.unit}, ${ing.category}`
    ).join('\n');
    const ingredientsEn = recipe.ingredients.en.map(ing => 
        `${ing.name}, ${ing.amount}, ${ing.unit}, ${ing.category}`
    ).join('\n');
    document.getElementById('ingredients-he').value = ingredientsHe;
    document.getElementById('ingredients-en').value = ingredientsEn;
    
    // Fill instructions
    document.getElementById('instructions-he').value = recipe.instructions.he.join('\n');
    document.getElementById('instructions-en').value = recipe.instructions.en.join('\n');
    
    // Show form
    document.getElementById('add-recipe-form').classList.remove('hidden');
    document.getElementById('form-message').classList.add('hidden');
    
    // Update form title
    const formTitle = document.getElementById('add-recipe-title');
    formTitle.textContent = translations[currentLanguage].edit_recipe_title;
    
    // Scroll to form
    document.getElementById('add-recipe-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

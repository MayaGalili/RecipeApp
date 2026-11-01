// Index page: serving buttons, print, copy / reset shopping list.

// Event listeners
document.getElementById('decrease-btn').addEventListener('click', () => {
    if (currentServings > 1) {
        currentServings--;
        updateAll();
    }
});

document.getElementById('increase-btn').addEventListener('click', () => {
    if (currentServings < 20) {
        currentServings++;
        updateAll();
    }
});

// Preset buttons
document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        currentServings = parseInt(btn.dataset.servings);
        updateAll();
    });
});

// Print functionality
document.getElementById('print-btn').addEventListener('click', () => {
    const printWindow = window.open('', '_blank');
    const shoppingListContent = document.getElementById('shopping-list').innerHTML;
    const servingCount = document.getElementById('serving-count').textContent;
    const recipeName = recipeTranslations[currentLanguage][currentRecipe];
    const t = translations[currentLanguage];
    const direction = (currentLanguage === 'he') ? 'rtl' : 'ltr';
    const marginSide = (currentLanguage === 'he') ? 'margin-left' : 'margin-right';
   
    printWindow.document.write(`
        <html dir="${direction}">
        <head>
            <title>${t.shopping_list_title} - ${recipeName}</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { color: #333; border-bottom: 2px solid #ff6b35; }
                h3 { color: #666; margin-top: 20px; }
                .shopping-item { padding: 5px 0; border-bottom: 1px solid #eee; }
                input[type="checkbox"] { ${marginSide}: 10px; }
            </style>
        </head>
        <body>
            <h1>${recipeName} - ${servingCount} ${t.serving_label}</h1>
            <h2>${t.shopping_list_title}</h2>
            ${shoppingListContent}
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
});

// Copy shopping list to clipboard
document.getElementById('copy-clipboard-btn').addEventListener('click', async () => {
    const recipeName = recipeTranslations[currentLanguage][currentRecipe] || currentRecipe;
    const servingCount = document.getElementById('serving-count').textContent;
    const t = translations[currentLanguage];
    
    // Build the shopping list text with checkboxes
    let clipboardText = `${recipeName} - ${servingCount} ${t.serving_label}\n${t.shopping_list_title}\n\n`;
    
    // Get all shopping list items
    const shoppingList = document.getElementById('shopping-list');
    const categories = shoppingList.querySelectorAll('.mb-4');
    
    categories.forEach(categoryDiv => {
        const categoryTitle = categoryDiv.querySelector('h3').textContent;
        clipboardText += `${categoryTitle}:\n`;
        
        const items = categoryDiv.querySelectorAll('.shopping-item');
        items.forEach(itemDiv => {
            const checkbox = itemDiv.querySelector('input[type="checkbox"]');
            const label = itemDiv.querySelector('label');
            const itemName = label.querySelector('span:first-child').textContent;
            const itemAmount = label.querySelector('span:last-child').textContent;
            
            // Use ☐ for unchecked, ☑ for checked
            const checkboxSymbol = checkbox.checked ? '☑' : '☐';
            clipboardText += `${checkboxSymbol} ${itemName} - ${itemAmount}\n`;
        });
        
        clipboardText += '\n';
    });
    
    // Copy to clipboard
    if (navigator.clipboard && navigator.clipboard.writeText) {
        try {
            await navigator.clipboard.writeText(clipboardText);
            showCopyNotification('הרשימה הועתקה ללוח!');
        } catch (err) {
            fallbackCopyToClipboard(clipboardText);
        }
    } else {
        fallbackCopyToClipboard(clipboardText);
    }
});

// Fallback copy function
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showCopyNotification('הרשימה הועתקה ללוח!');
        } else {
            showCopyNotification('לא ניתן להעתיק. נסי להעתיק ידנית.', true);
        }
    } catch (err) {
        showCopyNotification('לא ניתן להעתיק. נסי להעתיק ידנית.', true);
    }
    
    document.body.removeChild(textArea);
}

// Show copy notification
function showCopyNotification(message, isError = false) {
    const existing = document.getElementById('copy-notification');
    if (existing) {
        existing.remove();
    }

    const notification = document.createElement('div');
    notification.id = 'copy-notification';
    notification.className = `fixed top-4 left-1/2 transform -translate-x-1/2 bg-${isError ? 'red' : 'green'}-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 fade-in text-center`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Reset checkboxes functionality
document.getElementById('reset-btn').addEventListener('click', () => {
    const checkboxes = document.querySelectorAll('#shopping-list input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        if (checkbox.checked) {
            checkbox.checked = false;
            checkbox.dispatchEvent(new Event('change'));
        }
    });
});

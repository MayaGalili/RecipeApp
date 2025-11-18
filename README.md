# RecipeApp

The application is used for many things, one of the main things is to quickly find the recipe.

## Features

- Browse recipes by category (Meat/Fish, Pasta & Sauces, Sides, Salads, Soups, Desserts, Holidays & Celebrations)
- Adjust serving sizes dynamically
- Generate shopping lists
- **Add new recipes** - Recipes are automatically added to the app and saved to `recipes.json`

## Running the Application

### Option 1: Flask Server (Recommended - Required for Adding Recipes)

The Flask server is required if you want to add new recipes through the web interface.

1. **Create and activate virtual environment (first time only):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   (If you encounter authentication issues, use: `pip install --index-url https://pypi.org/simple Flask flask-cors`)

3. **Activate virtual environment (if not already activated):**
   ```bash
   source venv/bin/activate
   ```

4. **Start the Flask server:**
   ```bash
   python3 server.py
   ```

5. **Open your browser:**
   Visit: http://localhost:5001

6. **To stop the server:**
   Press `Ctrl + C` in the terminal

**Note:** The server runs on port 5001 (instead of 5000) to avoid conflicts with macOS AirPlay Receiver service.

**Quick Start (after initial setup):**
```bash
source venv/bin/activate && python3 server.py
```

### Option 2: Simple Python HTTP Server (Read-Only)

If you only want to view recipes without adding new ones:

1. **Navigate to project directory:**
   ```bash
   cd /Users/maya/projects/RecipeApp
   ```

2. **Start the server:**
   ```bash
   python3 -m http.server 8000
   ```
   (You can use any port number like 3000, 8080, etc.)

3. **Open your browser:**
   Visit: http://localhost:8000/main.html

4. **To stop the server:**
   Press `Ctrl + C` in the terminal

## Adding New Recipes

1. Start the Flask server (Option 1 above)
2. Click the "הוסף מתכון חדש" (Add New Recipe) button
3. Fill in the form:
   - Recipe name in Hebrew and English
   - Emoji
   - Category (Meat/Fish, Pasta & Sauces, Sides, Salads, Soups, Desserts, Holidays & Celebrations)
   - Recipe key is automatically generated from the English recipe name
   - Ingredients (one per line, format: `name, amount, unit, category`)
   - Instructions (one step per line)
4. Click "שמור מתכון" (Save Recipe)
5. The recipe will be automatically added to `recipes.json` and appear in the app!

## Recipe Data Format

Recipes are stored in `recipes.json`. The structure includes:
- `recipes`: Recipe data with ingredients and instructions
- `recipeTranslations`: Recipe names in Hebrew and English
- `recipeCategoryMap`: Categories and their associated recipes
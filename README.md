# RecipeApp

The application is used for many things, one of the main things is to quickly find the recipe.

## Features

- Browse recipes by category (Meat/Fish, Pasta & Sauces, Sides, Salads, Soups, Desserts, Holidays & Celebrations)
- Adjust serving sizes dynamically
- Generate shopping lists
- **Add new recipes** - Recipes are automatically added to the app and saved to `recipes.json`
- Modern UI with Tailwind CSS

## Prerequisites

- Python 3.7+
- Node.js 14+ (for building Tailwind CSS)

## Running the Application

### Initial Setup (First Time Only)

1. **Create and activate Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   (If you encounter authentication issues, use: `pip install --index-url https://pypi.org/simple Flask flask-cors`)

3. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

4. **Build Tailwind CSS:**
   ```bash
   node node_modules/tailwindcss/lib/cli.js -i ./input.css -o ./static/css/tailwind.css
   ```

### Running the Flask Server (Recommended)

The Flask server is required if you want to add new recipes through the web interface.

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Start the Flask server:**
   ```bash
   python3 server.py
   ```

3. **Open your browser:**
   Visit: http://localhost:5001

4. **To stop the server:**
   Press `Ctrl + C` in the terminal

**Note:** The server runs on port 5001 (instead of 5000) to avoid conflicts with macOS AirPlay Receiver service.

**Quick Start (after initial setup):**
```bash
source venv/bin/activate && python3 server.py
```

### Rebuilding Tailwind CSS

If you modify the HTML templates and need to rebuild Tailwind CSS to include new classes:

```bash
node node_modules/tailwindcss/lib/cli.js -i ./input.css -o ./static/css/tailwind.css
```

Or for minified version:
```bash
node node_modules/tailwindcss/lib/cli.js -i ./input.css -o ./static/css/tailwind.css --minify
```

## Adding New Recipes

1. Start the Flask server (see above)
2. Click the "הוסף מתכון חדש" (Add New Recipe) button
3. Fill in the form:
   - Recipe name in Hebrew and English
   - Emoji (select from dropdown)
   - Category (Meat/Fish, Pasta & Sauces, Sides, Salads, Soups, Desserts, Holidays & Celebrations)
   - Recipe key is automatically generated from the English recipe name
   - Ingredients (one per line, format: `name, amount, unit, category`)
   - Instructions (one step per line)
4. Click "שמור מתכון" (Save Recipe)
5. The recipe will be automatically added to `recipes.json` and appear in the app!

## Project Structure

```
RecipeApp/
├── templates/          # HTML templates (Flask)
│   └── main.html      # Main application template
├── static/            # Static files (CSS, JS, images)
│   ├── css/
│   │   └── tailwind.css  # Compiled Tailwind CSS
│   └── js/
├── recipes.json       # Recipe data storage
├── server.py          # Flask server
├── input.css          # Tailwind CSS source file
├── tailwind.config.js # Tailwind configuration
├── package.json       # Node.js dependencies
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Recipe Data Format

Recipes are stored in `recipes.json`. The structure includes:
- `recipes`: Recipe data with ingredients and instructions
- `recipeTranslations`: Recipe names in Hebrew and English
- `recipeCategoryMap`: Categories and their associated recipes

## Development Notes

- The application uses Flask for the backend and serves static files from the `static/` folder
- Templates are stored in the `templates/` folder
- Tailwind CSS is built locally (not using CDN) for better reliability
- The app is fully decoupled - recipes are stored in `recipes.json` separate from the HTML
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
   python3 app.py
   ```

3. **Open your browser:**
   Visit: http://localhost:5001

4. **To stop the server:**
   Press `Ctrl + C` in the terminal

**Note:** The server runs on port 5001 (instead of 5000) to avoid conflicts with macOS AirPlay Receiver service.

**Quick Start (after initial setup):**
```bash
source venv/bin/activate && python3 app.py
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
├── data/              # Data directory (writable files)
│   └── recipes.json   # Recipe data storage
├── app.py             # Flask application (main entry point)
├── render.yaml        # Render deployment configuration
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
- The app is fully decoupled - recipes are stored in `data/recipes.json` separate from the HTML
- Recipe data is stored in the `data/` directory to allow write operations on Render

## Deployment to Render

This application is configured for deployment on Render.com.

### Prerequisites for Deployment

1. **Project Structure:**
   - Main entry point: `app.py` (Flask app object named `app`)
   - Static files: `static/` folder
   - Templates: `templates/` folder
   - Data directory: `data/` folder (for writable files)

2. **Configuration Files:**
   - `requirements.txt` - Python dependencies (includes gunicorn)
   - `render.yaml` - Render deployment configuration

### Deployment Steps

1. **Push to Git Repository:**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Deploy on Render:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your Git repository
   - Render will automatically detect `render.yaml` and configure the service
   - The service will be deployed automatically

3. **What Render Does:**
   - Installs dependencies from `requirements.txt`
   - Runs `gunicorn app:app` to start the production server
   - Creates the `data/` directory at runtime (if it doesn't exist)
   - Serves the application on a public URL

### Important Notes for Render

- **Data Persistence:** The `data/` directory is created at runtime. Initial `data/recipes.json` is included in the repository for the first deployment.
- **File Writes:** All write operations (adding/editing/deleting recipes) are saved to `data/recipes.json`
- **Static Files:** Tailwind CSS is pre-built and stored in `static/css/tailwind.css`
- **Production Server:** Uses gunicorn (configured in `render.yaml`), Flask dev server only for local development

### Local Development vs Production

- **Local:** Run `python3 app.py` (uses Flask dev server on port 5001)
- **Production (Render):** Uses `gunicorn app:app` (configured automatically via `render.yaml`)
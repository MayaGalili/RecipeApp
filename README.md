# RecipeApp

The application is used for many things, one of the main things is to quickly find the recipe.

## Features

- Browse recipes by category (Meat/Fish, Pasta & Sauces, Sides, Salads, Soups, Desserts, Holidays & Celebrations)
- Adjust serving sizes dynamically
- Generate shopping lists
- **Add new recipes** - Recipes are automatically added to the app and saved to `recipes.json`
- **AI-Powered Recipe Parser** - Paste a free-text recipe and the AI will automatically parse it into the structured format
- Modern UI with Tailwind CSS

## Prerequisites

- Python 3.7+
- Node.js 14+ (for building Tailwind CSS)
- OpenAI API key (for AI-powered recipe parsing) - Get one at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

## Running the Application Locally

**Note:** You can run the application locally even after deploying to Render. Local development and production deployment are independent.

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

**Troubleshooting:**
- If port 5001 is already in use, you can change the port in `app.py` (line 249)
- Make sure the virtual environment is activated (you should see `(venv)` in your terminal prompt)
- If you see "ModuleNotFoundError", make sure you've installed dependencies: `pip install -r requirements.txt`

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

### Method 1: AI-Powered Free Text Parsing (Recommended)

1. Start the Flask server (see above)
2. Make sure you have set the `OPENAI_API_KEY` environment variable (see Configuration below)
3. Go to the "ניהול מתכונים" (Manage Recipes) page
4. In the "הוסף מתכון מטקסט חופשי" section, paste or type your recipe in free text format
5. Click "פרסם מתכון" (Parse Recipe)
6. Review the parsed recipe preview
7. Click "אשר ומלא טופס" (Approve and Fill Form) to automatically fill the form
8. Review and adjust if needed, then click "שמור מתכון" (Save Recipe)

### Method 2: Manual Form Entry

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

## Configuration

### OpenAI API Key (for AI Recipe Parsing)

To use the AI-powered recipe parser, you need to set up an OpenAI API key:

1. **Get an API key:**
   - Sign up at [https://platform.openai.com](https://platform.openai.com)
   - Go to [API Keys](https://platform.openai.com/api-keys) and create a new key

2. **Set the environment variable:**
   
   **Local Development:**
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```
   
   Or create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```
   
   **Render Deployment:**
   - Go to your Render service dashboard
   - Navigate to "Environment" tab
   - Add environment variable: `OPENAI_API_KEY` with your API key value
   - Save and redeploy

**Note:** The AI parser uses `gpt-4o-mini` model which is cost-effective. Without the API key, you can still use the manual form entry method. The parser is limited to admins, 5000 characters per request and 10 requests per hour. Also set a monthly spend limit in your OpenAI account.

## Admin Login

Viewing recipes is public. The management page (`/manage`) and all write APIs require the admin password. Set these environment variables (locally in `.env`, on Render under "Environment"):

- `SECRET_KEY`: a random secret used to sign the session cookie.
  `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `ADMIN_PASSWORD_HASH`: a hash of your admin password (never store the plain password).
  `python3 -c "from werkzeug.security import generate_password_hash as g; print(g(input()))"`
  In `.env`, wrap the hash in single quotes.

If either is missing, admin login is disabled and the site stays read-only. Set `FLASK_DEBUG=1` for local runs over plain http (production uses a Secure cookie).

Run the tests with `pip install -r requirements-dev.txt` and `pytest`.

## Project Structure

```
RecipeApp/
├── templates/          # HTML templates (Flask)
│   ├── index.html     # Recipe browsing page
│   ├── manage.html    # Add / edit / delete recipes
│   └── share.html     # Shared single-recipe page
├── static/            # Static files (CSS, JS, images)
│   ├── css/
│   │   └── tailwind.css  # Compiled Tailwind CSS
│   └── js/
├── data/              # Seed data
│   └── recipes.json   # Initial recipes, imported by migrate_to_db.py
├── migrate_to_db.py   # One-time import of recipes.json into the database
├── DATABASE_SETUP.md  # Database setup guide
├── app.py             # Flask application (main entry point)
├── render.yaml        # Render deployment configuration
├── input.css          # Tailwind CSS source file
├── tailwind.config.js # Tailwind configuration
├── package.json       # Node.js dependencies
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Recipe Data Format

Recipes are stored in the database (PostgreSQL, or SQLite locally; see `DATABASE_SETUP.md`). `data/recipes.json` is only the seed file imported by `migrate_to_db.py`. Its structure includes:
- `recipes`: Recipe data with ingredients and instructions
- `recipeTranslations`: Recipe names in Hebrew and English
- `recipeCategoryMap`: Categories and their associated recipes

## Development Notes

- The application uses Flask for the backend and serves static files from the `static/` folder
- Templates are stored in the `templates/` folder
- Tailwind CSS is built locally (not using CDN) for better reliability
- The app is fully decoupled - recipes are stored in the database, separate from the HTML

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
- **OpenAI API Key:** Add `OPENAI_API_KEY` environment variable in Render dashboard for AI recipe parsing feature

### Local Development vs Production

- **Local Development:** 
  - Run `python3 app.py` (uses Flask dev server on port 5001)
  - Access at: http://localhost:5001
  - Works independently from the deployed version on Render
  - Changes are local only until you commit and push to Git
- **Production (Render):** 
  - Uses `gunicorn app:app` (configured automatically via `render.yaml`)
  - Deployed automatically when you push to Git
  - Accessible via public URL provided by Render
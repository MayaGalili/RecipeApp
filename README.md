# RecipeApp

A modern, bilingual (Hebrew/English) recipe browsing and management application. Quickly find recipes by category, adjust serving sizes, generate shopping lists, and add new recipes with an optional AI-powered parser.

## Features

- Browse recipes by category (Meat/Fish, Pasta & Sauces, Sides, Salads, Soups, Desserts, Holidays & Celebrations)
- Adjust serving sizes dynamically
- Generate shopping lists
- Add new recipes through the web interface (manual or AI-powered)
- AI-powered recipe parser (paste free-text recipes and the AI structures them)
- Bilingual interface (Hebrew/English)

## Prerequisites

- **Python 3.9+** (3.11+ recommended)
- **Node.js 18+** (only needed if you modify CSS)
- **OpenAI API key** (optional, for AI recipe parsing — get one at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys))

## Quick Start (5 steps)

### Step 1: Clone and set up the environment

```bash
git clone <your-repo-url>
cd RecipeApp
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
npm install
```

### Step 3: Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env` to fill in the required variables:

- **`SECRET_KEY`**: Generate a random secret key:
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```
  Copy the output to `.env`

- **`ADMIN_PASSWORD_HASH`**: Generate a hash of your admin password:
  ```bash
  python3 -c "from werkzeug.security import generate_password_hash as g; print(g(input()))"
  ```
  Type your password and copy the hash to `.env`

- **`OPENAI_API_KEY`** (optional): Paste your OpenAI API key if you want AI recipe parsing
- **`FLASK_DEBUG=1`**: Keep this as-is for local development

### Step 4: Load sample recipes into the database

```bash
python3 -m scripts.migrate_to_db
```

This imports the 7 sample recipes into a local SQLite database (`instance/recipes.db`). You'll see a summary and be asked to type `import` to confirm.

### Step 5: Start the application

```bash
python3 app.py
```

Open http://localhost:5001 in your browser. You should see the 7 sample recipes ready to browse.

---

## Using Your Own Recipes

### Option 1: Add recipes manually

1. Click **"Add New Recipe"** on the management page (`/manage`)
2. Fill in the recipe details (name, ingredients, instructions, etc.)
3. Click **"Save Recipe"** — it's immediately saved to the database

### Option 2: Use AI to parse free-text recipes

1. Go to the management page (`/manage`)
2. Paste a recipe in free-text format
3. Click **"Parse Recipe"** — the AI structures it for you
4. Review the parsed recipe and click **"Save Recipe"**

### Option 3: Batch-import from Word documents

1. Organize your recipes into category folders (e.g., `recipes_data/meat_fish/`, `recipes_data/desserts/`)
2. Place `.docx` files in each folder
3. Run:
   ```bash
   python3 -m scripts.build_recipes_json recipes_data --output data/recipes_import.json
   ```
4. Import the new recipes:
   ```bash
   python3 -m scripts.migrate_to_db --input data/recipes_import.json --append
   ```

---

## Configuration

All configuration is set via environment variables (loaded from `.env`):

| Variable | Required | Purpose |
|----------|----------|---------|
| `SECRET_KEY` | Yes | Random secret for session cookies |
| `ADMIN_PASSWORD_HASH` | Yes | Password hash for admin login (access `/manage`) |
| `OPENAI_API_KEY` | No | OpenAI API key for AI recipe parsing |
| `FLASK_DEBUG` | No | Set to `1` for local development (plain http) |
| `DATABASE_URL` | No | PostgreSQL URL (if not set, uses local SQLite) |

---

## Customizing the App

To adapt this app for your own recipe collection, these are the main files to edit:

**Categories** (Meat/Fish, Pasta & Sauces, Sides, etc.):
- `recipe_app/recipes_api.py` → `VALID_CATEGORIES`
- `recipe_app/ai_parser.py` → prompt text and ingredient categories
- `static/js/common.js` → Hebrew and English category labels
- `templates/manage.html` → `<select>` options
- `static/img/categories/` → add or replace `.png` files matching the category keys

**App title and branding**:
- `templates/index.html` → page title, brand name in `<h1>`
- `static/js/index-i18n.js` → "My Recipe Book" strings
- Other templates and `static/css/` files

**Languages**: The app is hard-coded for Hebrew and English. Adding a third language requires schema changes (contact the maintainers or see DATABASE_SETUP.md).

---

## Development

### Run tests

```bash
pip install -r requirements-dev.txt
pytest
npm test
```

### Rebuild Tailwind CSS (if you modify templates)

```bash
npm run build:css          # Development
npm run build:css:min      # Minified (production)
```

---

## Project Structure

```
RecipeApp/
├── app.py                  # Entry point
├── recipe_app/
│   ├── __init__.py         # Flask app factory
│   ├── models.py           # Database models
│   ├── auth.py             # Admin login & CSRF
│   ├── ai_parser.py        # OpenAI integration
│   ├── recipes_api.py      # Recipe API endpoints
│   ├── pages.py            # Page routes
│   ├── config.py           # Configuration
│   └── extensions.py       # SQLAlchemy setup
├── scripts/
│   ├── build_recipes_json.py   # Convert .docx → JSON
│   └── migrate_to_db.py        # Import JSON → database
├── templates/              # HTML templates
├── static/                 # CSS, JavaScript, images
├── data/recipes.json       # Sample recipes (seed file)
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Dev dependencies (tests)
├── package.json            # Node.js dependencies
└── DATABASE_SETUP.md       # Production deployment guide
```

---

## Deployment

For production deployment to Render or another hosting platform, see [DATABASE_SETUP.md](DATABASE_SETUP.md).

The database stores all recipes. Locally it uses SQLite (`instance/recipes.db`); on Render it uses PostgreSQL. Recipe data is **not** saved to `data/recipes.json` — that file is only used for the initial seed import.

---

## Troubleshooting

**"No recipes appear on the home page"**
- Make sure you've run `python3 -m scripts.migrate_to_db` to load the sample recipes
- Check that `instance/recipes.db` exists after running the migrate script
- If using PostgreSQL, verify the `DATABASE_URL` is correct and the database is reachable

**"ModuleNotFoundError: docx"**
- Run `pip install -r requirements.txt` (includes `python-docx`)

**"Port 5001 is already in use"**
- Edit `app.py` (line 21) to change the port, or kill the process using that port

**Admin page (`/manage`) shows "Service Unavailable"**
- Make sure `.env` has both `SECRET_KEY` and `ADMIN_PASSWORD_HASH` set
- With `FLASK_DEBUG=1`, you can access it over plain http://localhost:5001

---

## License

ISC

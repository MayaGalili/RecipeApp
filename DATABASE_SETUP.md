# Database Setup Guide

The RecipeApp stores recipes in a SQL database. By default, it uses **SQLite** for local development (`instance/recipes.db`). For production, you can deploy to **PostgreSQL** (recommended for Render).

---

## Local Development (SQLite)

SQLite requires no setup. The app automatically creates the database and tables when you start it.

### Loading sample recipes

The repo includes 7 sample recipes in `data/recipes.json`. To load them into your local database:

```bash
python3 -m scripts.migrate_to_db
```

You'll see a summary of what will be imported. Type `import` to confirm. The recipes are now in `instance/recipes.db`.

### Importing your own recipes

#### Option 1: Add manually through the web UI

1. Go to http://localhost:5001/manage
2. Click **"Add New Recipe"** or use the **AI Parser** to parse free-text recipes
3. Recipes are saved immediately to the database

#### Option 2: Batch-import from Word documents

1. Create a folder structure with category subfolders, each containing `.docx` files:
   ```
   my_recipes/
   ├── meat_fish/
   │   ├── beef_stew.docx
   │   └── grilled_salmon.docx
   ├── desserts/
   │   └── chocolate_cake.docx
   └── ...
   ```

2. Build a JSON file from the Word documents (uses OpenAI):
   ```bash
   python3 -m scripts.build_recipes_json my_recipes --output data/recipes_import.json
   ```
   This calls the OpenAI API for each file (set `OPENAI_API_KEY` first).

3. Import the JSON into your database:
   ```bash
   python3 -m scripts.migrate_to_db --input data/recipes_import.json --append
   ```
   The `--append` flag adds new recipes without overwriting existing ones.

#### Option 3: Import a pre-made JSON file

Prepare a JSON file with this structure:

```json
{
  "recipes": {
    "recipe_key": {
      "name": "Recipe Name",
      "emoji": "🍳",
      "ingredients": {
        "he": [{"name": "...", "amount": 1, "unit": "...", "category": "..."}],
        "en": [{"name": "...", "amount": 1, "unit": "...", "category": "..."}]
      },
      "instructions": {
        "he": ["שלב 1", "שלב 2"],
        "en": ["Step 1", "Step 2"]
      }
    }
  },
  "recipeTranslations": {
    "he": {"recipe_key": "שם בעברית"},
    "en": {"recipe_key": "Name in English"}
  },
  "recipeCategoryMap": {
    "meat_fish": ["recipe_key1"],
    "desserts": ["recipe_key2"]
  }
}
```

Then import:
```bash
python3 -m scripts.migrate_to_db --input my_recipes.json
```

### Resetting the local database

To start fresh and delete all recipes:

```bash
rm instance/recipes.db
```

The next time you start the app, it will create a new empty database. Then re-run `python3 -m scripts.migrate_to_db` to load the sample recipes.

### Import options

- **`--dry-run`**: Validate the JSON without writing to the database
- **`--append`**: Add new recipes without requiring empty tables (good for incremental imports)
- **`--input <file>`**: Import from a custom JSON file (default: `data/recipes.json`)

---

## Production Deployment (PostgreSQL on Render)

For a production app, you'll use PostgreSQL (Render, AWS, etc.) instead of SQLite.

### Step 1: Create a PostgreSQL database on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"PostgreSQL"**
3. Fill in the details:
   - **Name**: `recipeapp-db` (or any name)
   - **Database**: `recipeapp` (or any name)
   - **User**: `recipeapp_user` (or any name)
   - **Region**: Choose a region close to you (ideally same as your web service)
   - **Plan**: Free tier is available (check current terms for data persistence)
4. Click **"Create Database"**

### Step 2: Set environment variables on Render

1. In your Render Web Service settings:
2. Go to the **"Environment"** tab
3. Add these variables:
   - **`DATABASE_URL`**: Copy the **Internal Database URL** from your PostgreSQL service (looks like `postgres://user:pass@host:port/dbname`)
   - **`OPENAI_API_KEY`**: (optional) Your OpenAI API key for AI recipe parsing
   - **`SECRET_KEY`**: Generate one: `python3 -c "import secrets; print(secrets.token_hex(32))"`
   - **`ADMIN_PASSWORD_HASH`**: Generate one: `python3 -c "from werkzeug.security import generate_password_hash as g; print(g(input()))"`
   - **`FLASK_DEBUG`**: Leave unset or set to `0` (not `1`) for production

### Step 3: Import recipes (run from your machine)

Before deploying, populate the PostgreSQL database with your recipes:

1. Copy the **External Database URL** from your Render PostgreSQL service (different from the internal URL)
2. On your local machine:
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:port/dbname"
   python3 -m scripts.migrate_to_db --input data/recipes.json
   ```
3. Type `import` to confirm

(If you skip this step, the app will deploy with an empty recipe list. You can always import later.)

### Step 4: Deploy to Render

1. Push your code to Git:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. Go to [Render Dashboard](https://dashboard.render.com) and create a new **Web Service**:
   - Connect your Git repository
   - Render detects `render.yaml` and configures automatically
   - The service deploys automatically

3. Render will:
   - Install dependencies from `requirements.txt`
   - Run the app with `gunicorn app:app`
   - Create database tables automatically on first startup
   - Use the `DATABASE_URL` to connect to PostgreSQL

### Step 5: Verify the deployment

1. Open your app at the public URL provided by Render
2. You should see the recipes you imported
3. Test the admin page (`/manage`) with your password

---

## Important Notes

### Database security & backups

- **Backups**: Render's free tier does not include automatic backups. Consider using `pg_dump` to manually back up your database.
- **Admin authentication**: The API endpoints are protected by admin login (CSRF + password). Add additional authentication if deploying publicly.

### Schema changes

The app creates tables automatically on startup (`db.create_all()`). There is no migration tool (like Alembic). If you need to change the database schema later, you'll need to apply changes manually to existing deployments.

### Troubleshooting

**"Database connection error" or empty recipe list:**
- Verify `DATABASE_URL` is set and correct
- Check that the PostgreSQL service is running
- If using Render, check the logs in the dashboard
- Make sure `psycopg` (the Python PostgreSQL driver) is in `requirements.txt`

**"Import fails with validation errors":**
- Check the JSON structure against the example above
- Run `python3 -m scripts.migrate_to_db --dry-run --input your_file.json` to see detailed errors

**"Recipes don't appear after import":**
- Verify the import succeeded (you should see "Imported: ...")
- Check the database directly (e.g., with `psql` or Render's query tool) to confirm rows were inserted

---

## Migration from SQLite to PostgreSQL

If you have a working app on SQLite and want to move to PostgreSQL:

1. Export your recipes from SQLite (Option: use the API to download, or directly inspect `instance/recipes.db`)
2. Set up PostgreSQL on Render (see **Step 1** above)
3. Use `python3 -m scripts.migrate_to_db` to import your recipes into PostgreSQL (set `DATABASE_URL` to the Render PostgreSQL URL)
4. Switch your app to use the new database by updating `DATABASE_URL` in your production config

---

## File locations

- **Local SQLite database**: `instance/recipes.db` (created automatically, gitignored)
- **Seed recipes**: `data/recipes.json` (tracked in git, imported once)
- **Import script**: `scripts/migrate_to_db.py`
- **Build script** (Word → JSON): `scripts/build_recipes_json.py`

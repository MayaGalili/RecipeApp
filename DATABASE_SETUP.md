# Setting Up PostgreSQL on Render

The app stores recipes in a SQL database through Flask-SQLAlchemy. In production it uses PostgreSQL, selected by the `DATABASE_URL` environment variable. If `DATABASE_URL` is not set, it falls back to a local SQLite file (`instance/recipes.db`), which is intended for development only.

## Step 1: Create a PostgreSQL database on Render

1. Go to the Render Dashboard: https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Fill in the details:
   - **Name**: `recipeapp-db` (or any other name)
   - **Database**: `recipeapp` (or any other name)
   - **User**: `recipeapp_user` (or any other name)
   - **Region**: choose the region closest to you (ideally the same region as your web service)
   - **PostgreSQL Version**: keep the latest version
   - **Plan**: choose a suitable plan. A free tier is available, but free databases expire after a limited period, so check Render's current terms before storing data you care about.
4. Click **"Create Database"**

## Step 2: Add the database URL and API key to the Web Service

1. Go to your Web Service in Render
2. Open the **"Environment"** tab
3. Click **"Add Environment Variable"**
4. Add:
   - **Key**: `DATABASE_URL`
   - **Value**: the connection string from your PostgreSQL service
     - Open the PostgreSQL service you created
     - Under **"Connections"**, copy the **Internal Database URL** (it looks like `postgres://user:pass@host:port/dbname`). Use the internal URL for the web service, since both run inside Render.
5. Add a second variable, `OPENAI_API_KEY`, with your OpenAI API key. It is used for AI recipe parsing and is unrelated to the database, but the app needs it for that feature.
6. Click **"Save Changes"**

The app automatically rewrites a `postgres://` prefix to `postgresql://`, so you can paste the URL as-is.

## Step 3: Import existing recipes (one-time, manual)

If you have existing recipes in `data/recipes.json`, you must import them yourself. **This does not happen automatically when the server starts.** If you skip this step, the app will start with an empty recipe list.

The script `migrate_to_db.py` reads `data/recipes.json` and inserts the recipes, translations, and categories into the database. It is safe to run more than once, because it skips recipes whose key already exists.

**From your own machine** (recommended):

1. In the Render PostgreSQL service, copy the **External Database URL** (the internal URL only works from inside Render).
2. Run:
   ```bash
   pip install -r requirements.txt

   # Set DATABASE_URL in .env or as an environment variable
   export DATABASE_URL="postgresql://user:pass@host:port/dbname"

   # Run the migration script
   python3 migrate_to_db.py
   ```

**From Render Shell** (only if your plan includes Shell access):

```bash
python3 migrate_to_db.py
```

To import into a local SQLite database instead, run the script without setting `DATABASE_URL`.

## Step 4: Deploy

1. Make sure your code on GitHub includes all your changes.
2. Push your changes:
   ```bash
   git add .
   git commit -m "Migrate to PostgreSQL"
   git push
   ```
3. Render deploys automatically.
4. The tables are created automatically the first time the server starts. Only the tables are created. Recipe data is not imported (see Step 3).

## Verification

After deploying:

1. Open the app. If you ran the import, your recipes should appear.
2. Try adding a new recipe.
3. The recipe should be saved and still be there after the service restarts.

## Important notes

- **Tables are created automatically.** The code creates them on startup if they do not exist. There is no migration tool, so later schema changes need to be applied manually.
- **Cascade delete.** Deleting a recipe automatically deletes its translations and categories.
- **SQLite fallback.** If `DATABASE_URL` is not set, the app uses a local SQLite database (development only).
- **Backups.** Render's backup availability depends on your plan. Check your plan's details, and consider taking manual backups (for example with `pg_dump`) from time to time.
- **Access control.** The add, update, and delete endpoints currently have no authentication, so anyone who knows the site URL can modify recipes.

## Troubleshooting

If you run into errors:

1. Make sure `DATABASE_URL` is set correctly.
2. Make sure the PostgreSQL service is running.
3. Check the logs in the Render Dashboard.
4. Make sure `requirements.txt` includes all required packages (`flask-sqlalchemy` and `psycopg2-binary` in particular).
5. If the app shows no recipes and no error, the database may be unreachable or empty. The app currently hides database read errors and returns an empty list, so check the logs and confirm you ran the import in Step 3.

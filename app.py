#!/usr/bin/env python3
"""
Simple Flask server for Recipe App
Handles serving static files and API endpoints for adding recipes
"""

from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from datetime import timedelta
from functools import wraps
import hmac
import json
import os
import secrets
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# Admin authentication configuration (single admin, password only).
# Both values must be set, otherwise admin features stay disabled (fail closed).
app.secret_key = os.environ.get('SECRET_KEY')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH')
IS_PRODUCTION = bool(os.environ.get('DATABASE_URL')) and os.environ.get('FLASK_DEBUG') != '1'
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=IS_PRODUCTION,  # plain http://localhost must still work in development
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=1024 * 1024,
)

# Database configuration
# Use PostgreSQL from Render if available, otherwise fall back to SQLite for local development
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Render PostgreSQL URL format: postgresql://user:pass@host:port/dbname
    # SQLAlchemy needs postgresql:// (not postgres://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback to SQLite for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class Recipe(db.Model):
    __tablename__ = 'recipes'
    recipe_key = db.Column(db.String(255), primary_key=True)
    emoji = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    ingredients_he = db.Column(db.Text, nullable=False)  # JSON string
    ingredients_en = db.Column(db.Text, nullable=False)  # JSON string
    instructions_he = db.Column(db.Text, nullable=False)  # JSON string
    instructions_en = db.Column(db.Text, nullable=False)  # JSON string
    category = db.Column(db.String(50), nullable=False)
    
    def to_dict(self):
        return {
            'emoji': self.emoji,
            'name': self.name,
            'ingredients': {
                'he': json.loads(self.ingredients_he),
                'en': json.loads(self.ingredients_en)
            },
            'instructions': {
                'he': json.loads(self.instructions_he),
                'en': json.loads(self.instructions_en)
            }
        }

class RecipeTranslation(db.Model):
    __tablename__ = 'recipe_translations'
    id = db.Column(db.Integer, primary_key=True)
    recipe_key = db.Column(db.String(255), db.ForeignKey('recipes.recipe_key', ondelete='CASCADE'), nullable=False)
    language = db.Column(db.String(2), nullable=False)  # 'he' or 'en'
    translation = db.Column(db.String(255), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('recipe_key', 'language', name='unique_recipe_lang'),)

class RecipeCategory(db.Model):
    __tablename__ = 'recipe_categories'
    id = db.Column(db.Integer, primary_key=True)
    recipe_key = db.Column(db.String(255), db.ForeignKey('recipes.recipe_key', ondelete='CASCADE'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('recipe_key', 'category', name='unique_recipe_category'),)

# Initialize database tables
with app.app_context():
    db.create_all()

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    openai_client = None
    print("Warning: OPENAI_API_KEY not set. Recipe parsing will not work.")

# ---- Authentication helpers ----

_rate_hits = {}  # key -> list of timestamps (per process, best effort)

def rate_limited(key, limit, window_seconds, record=True):
    """Return True if `key` already made `limit` hits within the window; otherwise optionally record a hit."""
    now = time.time()
    hits = [t for t in _rate_hits.get(key, []) if now - t < window_seconds]
    if len(hits) >= limit:
        _rate_hits[key] = hits
        return True
    if record:
        hits.append(now)
    _rate_hits[key] = hits
    return False

def csrf_token():
    """Per-session CSRF token, created on first use."""
    if not app.secret_key:
        return ''  # sessions are unavailable when admin login is not configured
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    return session['csrf']

def csrf_valid(submitted):
    expected = session.get('csrf')
    return bool(expected and submitted) and hmac.compare_digest(expected, submitted)

@app.context_processor
def inject_csrf_token():
    return {'csrf_token': csrf_token}

def admin_required(view):
    """Allow only the logged-in admin: JSON 401 for API calls, redirect to /login for pages."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin'):
            if request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped

@app.before_request
def check_csrf():
    """State-changing API calls and logout must carry the session's CSRF token."""
    if request.method in ('POST', 'PUT', 'DELETE') and (request.path.startswith('/api/') or request.path == '/logout'):
        if not session.get('admin'):
            return None  # admin_required answers 401 for the API; logout of an anonymous user is harmless
        submitted = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not csrf_valid(submitted):
            return jsonify({"error": "Invalid CSRF token"}), 403
    return None

def load_recipes():
    """Load recipes from database"""
    try:
        recipes = {}
        recipe_translations = {"he": {}, "en": {}}
        recipe_category_map = {
            "meat_fish": [],
            "pasta_sauces": [],
            "sides": [],
            "salads": [],
            "soups": [],
            "desserts": [],
            "holidays": []
        }
        
        # Load all recipes
        all_recipes = Recipe.query.all()
        for recipe in all_recipes:
            recipes[recipe.recipe_key] = recipe.to_dict()
        
        # Load translations
        all_translations = RecipeTranslation.query.all()
        for trans in all_translations:
            if trans.language in recipe_translations:
                recipe_translations[trans.language][trans.recipe_key] = trans.translation
        
        # Load categories
        all_categories = RecipeCategory.query.all()
        for cat in all_categories:
            if cat.category in recipe_category_map:
                if cat.recipe_key not in recipe_category_map[cat.category]:
                    recipe_category_map[cat.category].append(cat.recipe_key)
        
        return {
            "recipes": recipes,
            "recipeTranslations": recipe_translations,
            "recipeCategoryMap": recipe_category_map
        }
    except Exception as e:
        print(f"Error loading recipes from database: {e}")
        # Return empty structure if database error
        return {
            "recipes": {},
            "recipeTranslations": {"he": {}, "en": {}},
            "recipeCategoryMap": {
                "meat_fish": [],
                "pasta_sauces": [],
                "sides": [],
                "salads": [],
                "soups": [],
                "desserts": [],
                "holidays": []
            }
        }

@app.route('/')
def index():
    """Serve index.html as main page"""
    return render_template('index.html')

def client_ip():
    # Behind Render's proxy the last X-Forwarded-For entry is the one the proxy added (client-supplied entries come first)
    forwarded = request.headers.get('X-Forwarded-For', '')
    return forwarded.split(',')[-1].strip() or request.remote_addr or 'unknown'

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Single-admin password login"""
    if not app.secret_key or not ADMIN_PASSWORD_HASH:
        return render_template('login.html', error='Admin login is not configured'), 503
    if request.method == 'GET':
        return render_template('login.html', error=None)

    if not csrf_valid(request.form.get('csrf_token')):
        return render_template('login.html', error='Session expired, please try again'), 403
    attempts_key = f'login:{client_ip()}'
    if rate_limited(attempts_key, 5, 15 * 60, record=False):
        return render_template('login.html', error='Too many attempts, try again later'), 429
    if not check_password_hash(ADMIN_PASSWORD_HASH, request.form.get('password', '')):
        rate_limited(attempts_key, 5, 15 * 60)  # count the failure
        return render_template('login.html', error='Invalid password'), 401

    session.clear()  # drop any pre-login session state
    session['admin'] = True
    session.permanent = True
    return redirect(url_for('manage'))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/manage')
@admin_required
def manage():
    """Serve manage.html for recipe management"""
    return render_template('manage.html')

@app.route('/recipe/<recipe_key>')
def share_recipe(recipe_key):
    """Serve a shareable page for a specific recipe"""
    recipes_data = load_recipes()
    
    # Check if recipe exists
    if recipe_key not in recipes_data.get('recipes', {}):
        return render_template('share.html', error=True, recipe_key=recipe_key), 404
    
    # Get recipe data
    recipe = recipes_data['recipes'][recipe_key]
    translations = {
        'he': recipes_data.get('recipeTranslations', {}).get('he', {}).get(recipe_key, ''),
        'en': recipes_data.get('recipeTranslations', {}).get('en', {}).get(recipe_key, '')
    }
    
    return render_template('share.html', 
                         recipe_key=recipe_key,
                         recipe=recipe,
                         translations=translations,
                         error=False)

@app.route('/recipes.json')
def serve_recipes():
    """Serve recipes as JSON from database"""
    recipes_data = load_recipes()
    return jsonify(recipes_data)

@app.route('/api/add-recipe', methods=['POST'])
@admin_required
def add_recipe():
    """Add a new recipe to the database"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        recipe_key = data.get('recipeKey')
        recipe = data.get('recipe')
        category = data.get('category')
        translations = data.get('translations', {})
        
        if not recipe_key or not recipe or not category:
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if recipe key already exists
        if Recipe.query.get(recipe_key):
            return jsonify({"error": f"Recipe with key '{recipe_key}' already exists"}), 400
        
        # Validate category
        valid_categories = ['meat_fish', 'pasta_sauces', 'sides', 'salads', 'soups', 'desserts', 'holidays']
        if category not in valid_categories:
            return jsonify({"error": "Invalid category"}), 400
        
        # Create recipe record
        new_recipe = Recipe(
            recipe_key=recipe_key,
            emoji=recipe.get('emoji', '🍳'),
            name=recipe.get('name', ''),
            ingredients_he=json.dumps(recipe.get('ingredients', {}).get('he', []), ensure_ascii=False),
            ingredients_en=json.dumps(recipe.get('ingredients', {}).get('en', []), ensure_ascii=False),
            instructions_he=json.dumps(recipe.get('instructions', {}).get('he', []), ensure_ascii=False),
            instructions_en=json.dumps(recipe.get('instructions', {}).get('en', []), ensure_ascii=False),
            category=category
        )
        db.session.add(new_recipe)
        
        # Add translations
        if 'he' in translations:
            trans_he = RecipeTranslation(recipe_key=recipe_key, language='he', translation=translations['he'])
            db.session.add(trans_he)
        if 'en' in translations:
            trans_en = RecipeTranslation(recipe_key=recipe_key, language='en', translation=translations['en'])
            db.session.add(trans_en)
        
        # Add to category
        recipe_category = RecipeCategory(recipe_key=recipe_key, category=category)
        db.session.add(recipe_category)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Recipe added successfully",
            "recipeKey": recipe_key
        }), 200
        
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.exception("Recipe API error")
        return jsonify({"error": "Server error"}), 500

@app.route('/api/update-recipe', methods=['PUT'])
@admin_required
def update_recipe():
    """Update an existing recipe in the database"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        recipe_key = data.get('recipeKey')
        recipe = data.get('recipe')
        category = data.get('category')
        translations = data.get('translations', {})
        
        if not recipe_key or not recipe or not category:
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if recipe exists
        existing_recipe = Recipe.query.get(recipe_key)
        if not existing_recipe:
            return jsonify({"error": f"Recipe with key '{recipe_key}' not found"}), 404
        
        # Validate category
        valid_categories = ['meat_fish', 'pasta_sauces', 'sides', 'salads', 'soups', 'desserts', 'holidays']
        if category not in valid_categories:
            return jsonify({"error": "Invalid category"}), 400
        
        # Update recipe
        existing_recipe.emoji = recipe.get('emoji', '🍳')
        existing_recipe.name = recipe.get('name', '')
        existing_recipe.ingredients_he = json.dumps(recipe.get('ingredients', {}).get('he', []), ensure_ascii=False)
        existing_recipe.ingredients_en = json.dumps(recipe.get('ingredients', {}).get('en', []), ensure_ascii=False)
        existing_recipe.instructions_he = json.dumps(recipe.get('instructions', {}).get('he', []), ensure_ascii=False)
        existing_recipe.instructions_en = json.dumps(recipe.get('instructions', {}).get('en', []), ensure_ascii=False)
        existing_recipe.category = category
        
        # Update translations
        if 'he' in translations:
            trans_he = RecipeTranslation.query.filter_by(recipe_key=recipe_key, language='he').first()
            if trans_he:
                trans_he.translation = translations['he']
            else:
                trans_he = RecipeTranslation(recipe_key=recipe_key, language='he', translation=translations['he'])
                db.session.add(trans_he)
        
        if 'en' in translations:
            trans_en = RecipeTranslation.query.filter_by(recipe_key=recipe_key, language='en').first()
            if trans_en:
                trans_en.translation = translations['en']
            else:
                trans_en = RecipeTranslation(recipe_key=recipe_key, language='en', translation=translations['en'])
                db.session.add(trans_en)
        
        # Update category
        old_category = RecipeCategory.query.filter_by(recipe_key=recipe_key).first()
        if old_category:
            if old_category.category != category:
                old_category.category = category
        else:
            recipe_category = RecipeCategory(recipe_key=recipe_key, category=category)
            db.session.add(recipe_category)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Recipe updated successfully",
            "recipeKey": recipe_key
        }), 200
        
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.exception("Recipe API error")
        return jsonify({"error": "Server error"}), 500

@app.route('/api/delete-recipe', methods=['DELETE'])
@admin_required
def delete_recipe():
    """Delete a recipe from the database"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        recipe_key = data.get('recipeKey')
        
        if not recipe_key:
            return jsonify({"error": "Missing recipe key"}), 400
        
        # Check if recipe exists
        recipe = Recipe.query.get(recipe_key)
        if not recipe:
            return jsonify({"error": f"Recipe with key '{recipe_key}' not found"}), 404
        
        # Delete recipe (cascades will delete translations and categories)
        db.session.delete(recipe)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Recipe deleted successfully"
        }), 200
        
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.exception("Recipe API error")
        return jsonify({"error": "Server error"}), 500

@app.route('/api/parse-recipe', methods=['POST'])
@admin_required
def parse_recipe():
    """Parse free text recipe using OpenAI API"""
    try:
        if not openai_client:
            return jsonify({"error": "OpenAI API key not configured"}), 500
        
        data = request.json
        if not data or 'freeText' not in data:
            return jsonify({"error": "No recipe text provided"}), 400
        
        free_text = data['freeText']
        if not isinstance(free_text, str) or not free_text.strip():
            return jsonify({"error": "Recipe text is empty"}), 400
        if len(free_text) > 5000:
            return jsonify({"error": "Recipe text is too long (max 5000 characters)"}), 400
        if rate_limited('parse-recipe', 10, 3600):
            return jsonify({"error": "Too many parse requests, try again later"}), 429
        
        # Load existing recipes to understand the structure
        recipes_data = load_recipes()
        
        # Create a prompt for OpenAI
        prompt = f"""אתה מומחה בפרסור מתכונים. המטרה שלך היא לקחת מתכון שכתוב בשפה חופשית ולהמיר אותו למבנה JSON מובנה.

המתכון שצריך לפרסר:
{free_text}

המבנה הנדרש:
{{
  "nameHe": "שם המתכון בעברית",
  "nameEn": "Recipe name in English",
  "emoji": "אימוג'י מתאים (רק אחד)",
  "category": "קטגוריה מהרשימה: meat_fish, pasta_sauces, sides, salads, soups, desserts, holidays",
  "ingredientsHe": [
    {{"name": "שם המרכיב", "amount": מספר, "unit": "יחידה", "category": "קטגוריית מרכיב"}}
  ],
  "ingredientsEn": [
    {{"name": "Ingredient name", "amount": number, "unit": "unit", "category": "Ingredient category"}}
  ],
  "instructionsHe": ["שלב 1", "שלב 2", ...],
  "instructionsEn": ["Step 1", "Step 2", ...]
}}

קטגוריות המרכיבים בעברית: בשר ודגים, ירקות, פירות, דגנים ופחמימות, מוצרי חלב, רטבים ותבלינים, אגוזים וזרעים, משקאות
קטגוריות המרכיבים באנגלית: Meat & Fish, Vegetables, Fruits, Grains & Carbs, Dairy Products, Sauces & Seasonings, Nuts & Seeds, Beverages

חשוב:
1. אם המתכון כתוב רק בעברית, תתרגם גם לאנגלית
2. אם המתכון כתוב רק באנגלית, תתרגם גם לעברית
3. בחר אימוג'י מתאים לפי סוג המנה
4. בחר קטגוריה מתאימה מהרשימה
5. פרסר את כל המרכיבים עם כמות, יחידה וקטגוריה
6. פרסר את ההוראות לשלבים נפרדים
7. אם יש כמות לא ברורה, נסה להעריך או לכתוב "לפי הטעם"

החזר רק JSON, ללא טקסט נוסף."""

        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Using cheaper model
            messages=[
                {"role": "system", "content": "אתה מומחה בפרסור מתכונים. אתה מחזיר רק JSON תקני ללא טקסט נוסף."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
            timeout=30,
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        parsed_json = json.loads(response.choices[0].message.content)
        
        # Validate and structure the response
        parsed_recipe = {
            "nameHe": parsed_json.get("nameHe", ""),
            "nameEn": parsed_json.get("nameEn", ""),
            "emoji": parsed_json.get("emoji", "🍳"),
            "category": parsed_json.get("category", "meat_fish"),
            "ingredientsHe": parsed_json.get("ingredientsHe", []),
            "ingredientsEn": parsed_json.get("ingredientsEn", []),
            "instructionsHe": parsed_json.get("instructionsHe", []),
            "instructionsEn": parsed_json.get("instructionsEn", [])
        }
        
        # Validate category
        valid_categories = ['meat_fish', 'pasta_sauces', 'sides', 'salads', 'soups', 'desserts', 'holidays']
        if parsed_recipe['category'] not in valid_categories:
            parsed_recipe['category'] = 'meat_fish'  # Default
        
        return jsonify({
            "success": True,
            "parsedRecipe": parsed_recipe
        }), 200
        
    except json.JSONDecodeError:
        app.logger.exception("Failed to parse AI response")
        return jsonify({"error": "Failed to parse AI response"}), 500
    except Exception:
        app.logger.exception("Error parsing recipe")
        return jsonify({"error": "Error parsing recipe"}), 500

if __name__ == '__main__':
    # Only use Flask's development server for local development
    print("Starting Recipe App server...")
    print("Server will be available at http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    print("Note: For production, use gunicorn: gunicorn app:app")
    app.run(host='127.0.0.1', port=5001, debug=os.environ.get('FLASK_DEBUG') == '1')


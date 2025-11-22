#!/usr/bin/env python3
"""
Simple Flask server for Recipe App
Handles serving static files and API endpoints for adding recipes
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for all routes

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

@app.route('/manage')
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/update-recipe', methods=['PUT'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/delete-recipe', methods=['DELETE'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/parse-recipe', methods=['POST'])
def parse_recipe():
    """Parse free text recipe using OpenAI API"""
    try:
        if not openai_client:
            return jsonify({"error": "OpenAI API key not configured"}), 500
        
        data = request.json
        if not data or 'freeText' not in data:
            return jsonify({"error": "No recipe text provided"}), 400
        
        free_text = data['freeText']
        if not free_text.strip():
            return jsonify({"error": "Recipe text is empty"}), 400
        
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
        
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Failed to parse AI response: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error parsing recipe: {str(e)}"}), 500

if __name__ == '__main__':
    # Only use Flask's development server for local development
    print("Starting Recipe App server...")
    print("Server will be available at http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    print("Note: For production, use gunicorn: gunicorn app:app")
    app.run(host='0.0.0.0', port=5001, debug=True)


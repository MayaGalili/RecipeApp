#!/usr/bin/env python3
"""
Simple Flask server for Recipe App
Handles serving static files and API endpoints for adding recipes
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for all routes

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    openai_client = None
    print("Warning: OPENAI_API_KEY not set. Recipe parsing will not work.")

# Create data directory if it doesn't exist
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# Path to recipes.json in data directory
RECIPES_FILE = os.path.join(DATA_DIR, 'recipes.json')

def load_recipes():
    """Load recipes from JSON file"""
    if os.path.exists(RECIPES_FILE):
        with open(RECIPES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
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

def save_recipes(data):
    """Save recipes to JSON file"""
    with open(RECIPES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    """Serve index.html as main page"""
    return render_template('index.html')

@app.route('/manage')
def manage():
    """Serve manage.html for recipe management"""
    return render_template('manage.html')

@app.route('/recipes.json')
def serve_recipes():
    """Serve recipes.json file"""
    return send_from_directory(DATA_DIR, 'recipes.json')

@app.route('/api/add-recipe', methods=['POST'])
def add_recipe():
    """Add a new recipe to the recipes.json file"""
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
        
        # Load existing recipes
        recipes_data = load_recipes()
        
        # Check if recipe key already exists
        if recipe_key in recipes_data['recipes']:
            return jsonify({"error": f"Recipe with key '{recipe_key}' already exists"}), 400
        
        # Validate category
        valid_categories = ['meat_fish', 'pasta_sauces', 'sides', 'salads', 'soups', 'desserts', 'holidays']
        if category not in valid_categories:
            return jsonify({"error": "Invalid category"}), 400
        
        # Add recipe
        recipes_data['recipes'][recipe_key] = recipe
        
        # Add translations
        if 'he' in translations:
            recipes_data['recipeTranslations']['he'][recipe_key] = translations['he']
        if 'en' in translations:
            recipes_data['recipeTranslations']['en'][recipe_key] = translations['en']
        
        # Add to category
        if category not in recipes_data['recipeCategoryMap']:
            recipes_data['recipeCategoryMap'][category] = []
        recipes_data['recipeCategoryMap'][category].append(recipe_key)
        
        # Save to file
        save_recipes(recipes_data)
        
        return jsonify({
            "success": True,
            "message": "Recipe added successfully",
            "recipeKey": recipe_key
        }), 200
        
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/update-recipe', methods=['PUT'])
def update_recipe():
    """Update an existing recipe in the recipes.json file"""
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
        
        # Load existing recipes
        recipes_data = load_recipes()
        
        # Check if recipe exists
        if recipe_key not in recipes_data['recipes']:
            return jsonify({"error": f"Recipe with key '{recipe_key}' not found"}), 404
        
        # Validate category
        valid_categories = ['meat_fish', 'pasta_sauces', 'sides', 'salads', 'soups', 'desserts', 'holidays']
        if category not in valid_categories:
            return jsonify({"error": "Invalid category"}), 400
        
        # Get old category to remove from
        old_category = None
        for cat in recipes_data['recipeCategoryMap']:
            if recipe_key in recipes_data['recipeCategoryMap'][cat]:
                old_category = cat
                break
        
        # Update recipe
        recipes_data['recipes'][recipe_key] = recipe
        
        # Update translations
        if 'he' in translations:
            recipes_data['recipeTranslations']['he'][recipe_key] = translations['he']
        if 'en' in translations:
            recipes_data['recipeTranslations']['en'][recipe_key] = translations['en']
        
        # Update category if changed
        if old_category and old_category != category:
            # Remove from old category
            if recipe_key in recipes_data['recipeCategoryMap'][old_category]:
                recipes_data['recipeCategoryMap'][old_category].remove(recipe_key)
            # Add to new category
            if category not in recipes_data['recipeCategoryMap']:
                recipes_data['recipeCategoryMap'][category] = []
            if recipe_key not in recipes_data['recipeCategoryMap'][category]:
                recipes_data['recipeCategoryMap'][category].append(recipe_key)
        elif not old_category:
            # Recipe wasn't in any category, add it
            if category not in recipes_data['recipeCategoryMap']:
                recipes_data['recipeCategoryMap'][category] = []
            if recipe_key not in recipes_data['recipeCategoryMap'][category]:
                recipes_data['recipeCategoryMap'][category].append(recipe_key)
        
        # Save to file
        save_recipes(recipes_data)
        
        return jsonify({
            "success": True,
            "message": "Recipe updated successfully",
            "recipeKey": recipe_key
        }), 200
        
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/delete-recipe', methods=['DELETE'])
def delete_recipe():
    """Delete a recipe from the recipes.json file"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        recipe_key = data.get('recipeKey')
        
        if not recipe_key:
            return jsonify({"error": "Missing recipe key"}), 400
        
        # Load existing recipes
        recipes_data = load_recipes()
        
        # Check if recipe exists
        if recipe_key not in recipes_data['recipes']:
            return jsonify({"error": f"Recipe with key '{recipe_key}' not found"}), 404
        
        # Remove recipe from recipes
        del recipes_data['recipes'][recipe_key]
        
        # Remove translations
        if recipe_key in recipes_data['recipeTranslations']['he']:
            del recipes_data['recipeTranslations']['he'][recipe_key]
        if recipe_key in recipes_data['recipeTranslations']['en']:
            del recipes_data['recipeTranslations']['en'][recipe_key]
        
        # Remove from category map
        for category in recipes_data['recipeCategoryMap']:
            if recipe_key in recipes_data['recipeCategoryMap'][category]:
                recipes_data['recipeCategoryMap'][category].remove(recipe_key)
                break
        
        # Save to file
        save_recipes(recipes_data)
        
        return jsonify({
            "success": True,
            "message": "Recipe deleted successfully"
        }), 200
        
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400
    except Exception as e:
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


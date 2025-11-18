#!/usr/bin/env python3
"""
Simple Flask server for Recipe App
Handles serving static files and API endpoints for adding recipes
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for all routes

RECIPES_FILE = 'recipes.json'

def load_recipes():
    """Load recipes from JSON file"""
    if os.path.exists(RECIPES_FILE):
        with open(RECIPES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "recipes": {},
        "recipeTranslations": {"he": {}, "en": {}},
        "recipeCategoryMap": {"breakfast": [], "lunch": [], "dinner": []}
    }

def save_recipes(data):
    """Save recipes to JSON file"""
    with open(RECIPES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    """Serve main.html as index"""
    return send_from_directory('.', 'main.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

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
        if category not in ['breakfast', 'lunch', 'dinner']:
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

if __name__ == '__main__':
    print("Starting Recipe App server...")
    print("Server will be available at http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    app.run(host='0.0.0.0', port=5001, debug=True)


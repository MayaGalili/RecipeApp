"""Recipe loading and the admin recipe API (add / update / delete)."""

import json

from flask import current_app, jsonify, request

from .auth import admin_required
from .extensions import db
from .models import Recipe, RecipeTranslation, RecipeCategory

VALID_CATEGORIES = ['meat_fish', 'pasta_sauces', 'sides', 'salads', 'soups', 'desserts', 'holidays']


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
        if category not in VALID_CATEGORIES:
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
        current_app.logger.exception("Recipe API error")
        return jsonify({"error": "Server error"}), 500

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
        if category not in VALID_CATEGORIES:
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
        current_app.logger.exception("Recipe API error")
        return jsonify({"error": "Server error"}), 500

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
        current_app.logger.exception("Recipe API error")
        return jsonify({"error": "Server error"}), 500

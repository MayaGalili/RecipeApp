"""Public and admin HTML pages, plus the recipes JSON feed."""

from flask import jsonify, render_template

from .auth import admin_required
from .recipes_api import load_recipes


def index():
    """Serve index.html as main page"""
    return render_template('index.html')

@admin_required
def manage():
    """Serve manage.html for recipe management"""
    return render_template('manage.html')

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

def serve_recipes():
    """Serve recipes as JSON from database"""
    recipes_data = load_recipes()
    return jsonify(recipes_data)


def account():
    """Serve Firebase phone sign-in and account status page."""
    return render_template('account.html')

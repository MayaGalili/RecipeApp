#!/usr/bin/env python3
"""
Script to migrate recipes from JSON file to PostgreSQL database
Run this once after setting up PostgreSQL to import existing recipes
"""

import json
import os
from app import app, db, Recipe, RecipeTranslation, RecipeCategory

def migrate_recipes():
    """Migrate recipes from JSON file to database"""
    json_file = os.path.join('data', 'recipes.json')
    
    if not os.path.exists(json_file):
        print(f"File {json_file} not found. Nothing to migrate.")
        return
    
    with app.app_context():
        # Load recipes from JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        recipes = data.get('recipes', {})
        translations = data.get('recipeTranslations', {})
        categories = data.get('recipeCategoryMap', {})
        
        migrated_count = 0
        
        for recipe_key, recipe in recipes.items():
            # Check if recipe already exists
            if Recipe.query.get(recipe_key):
                print(f"Recipe {recipe_key} already exists, skipping...")
                continue
            
            # Create recipe
            new_recipe = Recipe(
                recipe_key=recipe_key,
                emoji=recipe.get('emoji', '🍳'),
                name=recipe.get('name', ''),
                ingredients_he=json.dumps(recipe.get('ingredients', {}).get('he', []), ensure_ascii=False),
                ingredients_en=json.dumps(recipe.get('ingredients', {}).get('en', []), ensure_ascii=False),
                instructions_he=json.dumps(recipe.get('instructions', {}).get('he', []), ensure_ascii=False),
                instructions_en=json.dumps(recipe.get('instructions', {}).get('en', []), ensure_ascii=False),
                category='meat_fish'  # Default, will be updated from category map
            )
            db.session.add(new_recipe)
            
            # Add translations
            if recipe_key in translations.get('he', {}):
                trans_he = RecipeTranslation(
                    recipe_key=recipe_key,
                    language='he',
                    translation=translations['he'][recipe_key]
                )
                db.session.add(trans_he)
            
            if recipe_key in translations.get('en', {}):
                trans_en = RecipeTranslation(
                    recipe_key=recipe_key,
                    language='en',
                    translation=translations['en'][recipe_key]
                )
                db.session.add(trans_en)
            
            # Add category
            recipe_category = None
            for cat, recipe_keys in categories.items():
                if recipe_key in recipe_keys:
                    recipe_category = cat
                    break
            
            if recipe_category:
                new_recipe.category = recipe_category
                cat_record = RecipeCategory(recipe_key=recipe_key, category=recipe_category)
                db.session.add(cat_record)
            
            migrated_count += 1
        
        try:
            db.session.commit()
            print(f"Successfully migrated {migrated_count} recipes to database!")
        except Exception as e:
            db.session.rollback()
            print(f"Error migrating recipes: {e}")

if __name__ == '__main__':
    migrate_recipes()


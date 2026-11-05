#!/usr/bin/env python3
"""
Import data/recipes.json into an empty database (SQLite or PostgreSQL).

    python3 -m scripts.migrate_to_db --dry-run   # validate and count, write nothing
    python3 -m scripts.migrate_to_db             # real import (asks for confirmation)
    python3 -m scripts.migrate_to_db --input recipes_import.json  # import custom file
    python3 -m scripts.migrate_to_db --append    # add new recipes to existing DB

The import aborts unless all three destination tables are empty (unless --append).
It runs in a single transaction.
"""

import argparse
import json
import os
import sys
from app import app, db, Recipe, RecipeTranslation, RecipeCategory

# Resolve to <repo>/data/recipes.json (one level up from scripts/)
JSON_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'recipes.json')
VALID_CATEGORIES = ['meat_fish', 'pasta_sauces', 'sides', 'salads', 'soups', 'desserts', 'holidays']
LANGUAGES = ('he', 'en')
TABLES = (('recipes', Recipe), ('recipe_translations', RecipeTranslation), ('recipe_categories', RecipeCategory))


def load_and_validate(path):
    """Return (recipes, translations, categories, errors). Nothing touches the database."""
    errors = []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    recipes_in = data.get('recipes')
    translations_in = data.get('recipeTranslations')
    category_map = data.get('recipeCategoryMap')
    if not isinstance(recipes_in, dict) or not isinstance(translations_in, dict) or not isinstance(category_map, dict):
        return [], [], [], ["JSON must contain 'recipes', 'recipeTranslations' and 'recipeCategoryMap' objects"]

    # category per recipe, from the category map (recipes.category is NOT NULL)
    category_of = {}
    for category, keys in category_map.items():
        if category not in VALID_CATEGORIES:
            errors.append(f"unknown category '{category}'")
        for key in keys:
            if key not in recipes_in:
                errors.append(f"category '{category}' lists unknown recipe '{key}'")
            elif key in category_of:
                errors.append(f"recipe '{key}' is in more than one category")
            category_of.setdefault(key, category)

    recipes, translations, categories = [], [], []
    for key, recipe in recipes_in.items():
        if len(key) > 255:
            errors.append(f"{key[:30]}...: key longer than 255")
        if key not in category_of:
            errors.append(f"{key}: not in any category")
        for field, limit in (('name', 255), ('emoji', 10)):
            value = recipe.get(field)
            if not isinstance(value, str) or not value or len(value) > limit:
                errors.append(f"{key}: '{field}' must be a non-empty string up to {limit} chars")
        for section in ('ingredients', 'instructions'):
            for lang in LANGUAGES:
                if not isinstance(recipe.get(section, {}).get(lang), list):
                    errors.append(f"{key}: '{section}.{lang}' must be a list")
        if errors:
            continue
        recipes.append(Recipe(
            recipe_key=key,
            emoji=recipe['emoji'],
            name=recipe['name'],
            ingredients_he=json.dumps(recipe['ingredients']['he'], ensure_ascii=False),
            ingredients_en=json.dumps(recipe['ingredients']['en'], ensure_ascii=False),
            instructions_he=json.dumps(recipe['instructions']['he'], ensure_ascii=False),
            instructions_en=json.dumps(recipe['instructions']['en'], ensure_ascii=False),
            category=category_of[key],
        ))
        categories.append(RecipeCategory(recipe_key=key, category=category_of[key]))

    for lang, by_key in translations_in.items():
        if lang not in LANGUAGES:
            errors.append(f"unknown translation language '{lang}'")
            continue
        for key, text in by_key.items():
            if key not in recipes_in:
                errors.append(f"{lang} translation for unknown recipe '{key}'")
            elif not isinstance(text, str) or not text or len(text) > 255:
                errors.append(f"{key}: {lang} translation must be a non-empty string up to 255 chars")
            else:
                translations.append(RecipeTranslation(recipe_key=key, language=lang, translation=text))

    return recipes, translations, categories, errors


def select_new(recipes, translations, categories, existing_keys):
    """Filter recipes/translations/categories to only those not already in the DB (by recipe key).

    Args:
        recipes, translations, categories: lists of SQLAlchemy model instances.
        existing_keys: set of recipe keys already in the Recipe table.

    Returns:
        (recipes_new, translations_new, categories_new) filtered lists.
    """
    recipes_new = [r for r in recipes if r.recipe_key not in existing_keys]
    recipe_keys_new = {r.recipe_key for r in recipes_new}
    translations_new = [t for t in translations if t.recipe_key in recipe_keys_new]
    categories_new = [c for c in categories if c.recipe_key in recipe_keys_new]
    return recipes_new, translations_new, categories_new


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument('--input', default=None, help='Input JSON file (default: data/recipes.json)')
    parser.add_argument('--dry-run', action='store_true', help='validate and count, write nothing')
    parser.add_argument('--append', action='store_true', help='append mode: skip existing recipes and insert only new ones')
    args = parser.parse_args()

    json_file = args.input if args.input else JSON_FILE
    if not os.path.exists(json_file):
        sys.exit(f"File not found: {json_file}")

    recipes, translations, categories, errors = load_and_validate(json_file)
    if errors:
        print("Validation failed, nothing written:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    try:
        with app.app_context():
            # Never print the URL, host or credentials: only the dialect name.
            dialect = db.engine.dialect.name
            print(f"Target database: {dialect}")

            existing = {name: db.session.query(model).count() for name, model in TABLES}

            # Determine what to import
            if args.append:
                # In append mode, filter to only new recipes
                existing_keys = {r.recipe_key for r in db.session.query(Recipe).all()}
                recipes, translations, categories = select_new(recipes, translations, categories, existing_keys)
                if not recipes:
                    print(f"No new recipes to import (all keys already in database).")
                    sys.exit(0)
                planned = {'recipes': len(recipes), 'recipe_translations': len(translations), 'recipe_categories': len(categories)}
                print(f"Append mode: will insert {planned['recipes']} new recipe{'s' if planned['recipes'] != 1 else ''}")
            else:
                # First-time mode: require empty tables
                if any(existing.values()):
                    print(f"Existing rows: {existing}")
                    sys.exit("Destination tables are not empty; this is a first-time import only. Aborting.")
                planned = {'recipes': len(recipes), 'recipe_translations': len(translations), 'recipe_categories': len(categories)}

            print(f"Validated from JSON: {planned}")
            if args.dry_run:
                db.session.rollback()
                print("Dry run: would insert the rows above. Nothing was written.")
                return

            if input("Type 'import' to insert these rows into the database above: ").strip() != 'import':
                sys.exit("Not confirmed; nothing written.")

            try:
                db.session.add_all(recipes + translations + categories)
                db.session.commit()
            except BaseException:
                db.session.rollback()
                raise
            print(f"Imported: {planned}")
    except EOFError:
        sys.exit("No confirmation received; nothing written.")
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        # Class name only: driver messages can contain host/user details.
        sys.exit(f"Import failed and was rolled back ({type(e).__name__}).")


if __name__ == '__main__':
    main()

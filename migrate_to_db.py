#!/usr/bin/env python3
"""
One-time import of data/recipes.json into an empty PostgreSQL database.

    python3 migrate_to_db.py --dry-run   # validate and count, write nothing
    python3 migrate_to_db.py             # real import (asks for confirmation)

The import aborts unless the target is PostgreSQL and all three destination
tables are empty. It runs in a single transaction. Delete this file afterwards.
"""

import argparse
import json
import os
import sys
from app import app, db, Recipe, RecipeTranslation, RecipeCategory

JSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'recipes.json')
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


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument('--dry-run', action='store_true', help='validate and count, write nothing')
    args = parser.parse_args()

    if not os.environ.get('DATABASE_URL'):
        sys.exit("DATABASE_URL is not set; refusing to fall back to local SQLite.")
    if not os.path.exists(JSON_FILE):
        sys.exit(f"{JSON_FILE} not found.")

    recipes, translations, categories, errors = load_and_validate(JSON_FILE)
    if errors:
        print("Validation failed, nothing written:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    planned = {'recipes': len(recipes), 'recipe_translations': len(translations), 'recipe_categories': len(categories)}

    try:
        with app.app_context():
            # Never print the URL, host or credentials: only the dialect name.
            dialect = db.engine.dialect.name
            print(f"Target database: {dialect}")
            if dialect != 'postgresql':
                sys.exit("Target is not PostgreSQL; aborting.")

            existing = {name: db.session.query(model).count() for name, model in TABLES}
            if any(existing.values()):
                print(f"Existing rows: {existing}")
                sys.exit("Destination tables are not empty; this is a first-time import only. Aborting.")

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

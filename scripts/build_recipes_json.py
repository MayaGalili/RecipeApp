#!/usr/bin/env python3
"""Build migrate-ready recipes.json from a folder of text files organized by category.

Usage:
    python3 build_recipes_json.py FOLDER [--output data/recipes_import.json] [--map "folder=key"]... [--dry-run] [--allow-partial] [--force]

Each subfolder should contain recipe text files (.txt or .md).  Folder names are mapped to category keys via
Hebrew labels or fuzzy matching. The output is validated with migrate_to_db.load_and_validate() before writing.
"""

import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from recipe_app.ai_parser import create_openai_client
from recipe_app.recipes_api import VALID_CATEGORIES
from recipe_app.ai_parser import parse_recipe_text
from docx import Document

def load_and_validate(data):
    """Validate the JSON structure matches what migrate_to_db expects. Returns errors list."""
    errors = []
    recipes_in = data.get('recipes', {})
    translations_in = data.get('recipeTranslations', {})
    category_map = data.get('recipeCategoryMap', {})

    if not isinstance(recipes_in, dict):
        errors.append("'recipes' must be a dict")
    if not isinstance(translations_in, dict):
        errors.append("'recipeTranslations' must be a dict")
    if not isinstance(category_map, dict):
        errors.append("'recipeCategoryMap' must be a dict")

    if errors:
        return errors

    for category in VALID_CATEGORIES:
        if category not in category_map:
            errors.append(f"missing category '{category}' in recipeCategoryMap")
        elif not isinstance(category_map[category], list):
            errors.append(f"recipeCategoryMap['{category}'] must be a list")

    for key, recipe in recipes_in.items():
        if len(key) > 255:
            errors.append(f"recipe key '{key[:30]}...' exceeds 255 chars")
        for field in ('name', 'emoji'):
            if not isinstance(recipe.get(field), str) or not recipe.get(field):
                errors.append(f"recipe '{key}': '{field}' must be a non-empty string")
            elif field == 'emoji' and len(recipe[field]) > 10:
                errors.append(f"recipe '{key}': emoji exceeds 10 chars")
            elif field == 'name' and len(recipe[field]) > 255:
                errors.append(f"recipe '{key}': name exceeds 255 chars")
        for section in ('ingredients', 'instructions'):
            for lang in ('he', 'en'):
                if not isinstance(recipe.get(section, {}).get(lang), list):
                    errors.append(f"recipe '{key}': '{section}.{lang}' must be a list")

    # Check translations
    for lang in ('he', 'en'):
        if lang not in translations_in:
            errors.append(f"missing '{lang}' in recipeTranslations")
        else:
            for key, text in translations_in[lang].items():
                if key not in recipes_in:
                    errors.append(f"{lang} translation for unknown recipe '{key}'")
                elif not isinstance(text, str) or not text or len(text) > 255:
                    errors.append(f"recipe '{key}': {lang} translation must be non-empty, <= 255 chars")

    # Check categories
    for category, keys in category_map.items():
        if category not in VALID_CATEGORIES:
            errors.append(f"unknown category '{category}'")
        for key in keys:
            if key not in recipes_in:
                errors.append(f"category '{category}' lists unknown recipe '{key}'")

    return errors

def extract_text(file_path):
    doc = Document(file_path)

    return "\n".join(
        paragraph.text
        for paragraph in doc.paragraphs
        if paragraph.text.strip()
    )

def build_from_folder(folder_path, openai_client, overrides=None, dry_run=False, allow_partial=False):
    """Scan folder and build recipes.json content. Returns (data, errors) tuple."""
    translations = {'he':{}, 'en': {}}
    recipe_category_map = {title: [] for title in VALID_CATEGORIES}
    recipes = {}

    # Parse recipe files
    for subfolder in Path(folder_path).iterdir():
        if not subfolder.is_dir():
            continue

        for file_path in subfolder.iterdir():
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() != ".docx":
                continue

            txt = extract_text(file_path)            
            parsed = parse_recipe_text(openai_client, txt)

            # Generate recipe key
            key = parsed['nameEn']
            if key in recipes:
                counter = 1
                original_key = key
                while f"{original_key}_{counter}" in recipes:
                    counter += 1
                key = f"{original_key}_{counter}"

            recipes[key] = {
                "name": f"{parsed['emoji']} {parsed['nameHe']}",
                "emoji": parsed['emoji'],
                "ingredients": {"he": parsed['ingredientsHe'], "en": parsed['ingredientsEn']},
                "instructions": {"he": parsed['instructionsHe'], "en": parsed['instructionsEn']}
            }
            translations['he'][key] = parsed['nameHe']
            translations['en'][key] = parsed['nameEn']
            recipe_category_map[parsed["category"]].append(key)


    return {
        "recipes": recipes,
        "recipeTranslations": translations,
        "recipeCategoryMap": recipe_category_map
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build migrate-ready recipes.json from a folder of recipe text files organized by category."
    )
    parser.add_argument('folder', help='Path to folder containing category subfolders')
    parser.add_argument('--output', default='data/recipes_import.json', help='Output file path (default: data/recipes_import.json)')
    parser.add_argument('--map', dest='mappings', action='append', default=[], help='Override folder->category mapping (e.g. --map "my_folder=soups")')
    parser.add_argument('--dry-run', action='store_true', help='Validate and show summary without writing output')
    parser.add_argument('--allow-partial', action='store_true', help='Write successful recipes even if some files failed')
    parser.add_argument('--force', action='store_true', help='Overwrite existing output file')

    args = parser.parse_args()

    # Parse --map arguments
    overrides = {}
    for mapping in args.mappings:
        if '=' not in mapping:
            print(f"ERROR: Invalid --map format: '{mapping}' (expected 'folder=key')")
            sys.exit(1)
        folder, cat = mapping.split('=', 1)
        if cat not in VALID_CATEGORIES:
            print(f"ERROR: Unknown category '{cat}' in --map")
            sys.exit(1)
        overrides[folder] = cat



    load_dotenv()
    openai_client = create_openai_client()
    if not openai_client and not args.dry_run:
        sys.exit("ERROR: OPENAI_API_KEY not set and not in dry-run mode")

    # Build recipes
    data = build_from_folder(args.folder, openai_client, overrides, args.dry_run, args.allow_partial)

    if args.dry_run:
        sys.exit(0)

    # Validate output
    val_errors = load_and_validate(data)
    if val_errors:
        print("Validation failed:")
        for error in val_errors:
            print(f"  - {error}")
        sys.exit(1)

    # Check for existing output
    output_path = Path(args.output)
    if output_path.exists() and not args.force:
        print(f"ERROR: Output file exists: {args.output} (use --force to overwrite)")
        sys.exit(1)

    # Write atomically
    tmp_path = Path(str(output_path) + '.tmp')
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp_path.replace(output_path)

    # Summary
    total_recipes = len(data['recipes'])
    print(f"✓ Built {total_recipes} recipe{'s' if total_recipes != 1 else ''}")
    print(f"✓ Written to {args.output}")


if __name__ == '__main__':
    main()

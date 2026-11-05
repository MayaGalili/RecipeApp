"""AI free-text recipe parsing (OpenAI)."""

import json
import os

from flask import current_app, jsonify, request
from openai import OpenAI

from .auth import admin_required, rate_limited
from .recipes_api import VALID_CATEGORIES, load_recipes


def create_openai_client():
    """Return an OpenAI client, or None (with a warning) when OPENAI_API_KEY is not set."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        return OpenAI(api_key=api_key)
    print("Warning: OPENAI_API_KEY not set. Recipe parsing will not work.")
    return None


def parse_recipe_text(openai_client, free_text):
    """Parse free-text recipe using OpenAI API. Returns the parsed recipe dict or raises an exception.

    Args:
        openai_client: OpenAI client instance (can be None, will raise).
        free_text: Recipe text (must be non-empty and <= 5000 chars).

    Returns:
        {"nameHe", "nameEn", "emoji", "category", "ingredientsHe", "ingredientsEn", "instructionsHe", "instructionsEn"}
        where category is validated against VALID_CATEGORIES and defaults to 'meat_fish' if unknown.

    Raises:
        ValueError: for missing client, empty text, or text too long.
        json.JSONDecodeError: if OpenAI returns invalid JSON.
        Exception: on network or API errors.
    """
    if not openai_client:
        raise ValueError("OpenAI client is not configured")
    if not isinstance(free_text, str) or not free_text.strip():
        raise ValueError("Recipe text is empty")
    if len(free_text) > 5000:
        raise ValueError("Recipe text is too long (max 5000 characters)")

    # Create the parsing prompt
    prompt = f"""You are an expert in recipe parsing. Your goal is to take a recipe written in free-form text and convert it into a structured JSON format.

The recipe to parse:
{free_text}

Required structure:
{{
  "nameHe": "Recipe name in Hebrew",
  "nameEn": "Recipe name in English",
  "emoji": "Appropriate emoji (only one)",
  "category": "Category from the list: meat_fish, pasta_sauces, sides, salads, soups, desserts, holidays",
  "ingredientsHe": [
    {{"name": "Ingredient name in Hebrew", "amount": number, "unit": "unit", "category": "Ingredient category"}}
  ],
  "ingredientsEn": [
    {{"name": "Ingredient name", "amount": number, "unit": "unit", "category": "Ingredient category"}}
  ],
  "instructionsHe": ["שלב 1", "שלב 2", ...],
  "instructionsEn": ["Step 1", "Step 2", ...]
}}

Ingredient categories in Hebrew: בשר ודגים, ירקות, פירות, דגנים ופחמימות, מוצרי חלב, רטבים ותבלינים, אגוזים וזרעים, משקאות
Ingredient categories in English: Meat & Fish, Vegetables, Fruits, Grains & Carbs, Dairy Products, Sauces & Seasonings, Nuts & Seeds, Beverages

Important:
1. If the recipe is written only in Hebrew, translate it into English as well.
2. If the recipe is written only in English, translate it into Hebrew as well.
3. Choose an appropriate emoji based on the type of dish.
4. Choose an appropriate category from the list.
5. Parse all ingredients, including quantity, unit, and category.
6. Parse the instructions into separate steps.
7. If a quantity is unclear, try to estimate it or write "to taste".

Return only JSON, with no additional text."""
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "You are an expert in recipe parsing. You return only valid JSON with no additional text."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2000,
        timeout=30,
        response_format={"type": "json_object"}
    )

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
    if parsed_recipe['category'] not in VALID_CATEGORIES:
        parsed_recipe['category'] = 'meat_fish'

    return parsed_recipe


@admin_required
def parse_recipe():
    """Parse free text recipe using OpenAI API"""
    try:
        openai_client = current_app.config['OPENAI_CLIENT']

        data = request.json
        if not data or 'freeText' not in data:
            return jsonify({"error": "No recipe text provided"}), 400

        free_text = data['freeText']

        # Rate limit the parse endpoint
        if rate_limited('parse-recipe', 10, 3600):
            return jsonify({"error": "Too many parse requests, try again later"}), 429

        # Parse the recipe using the shared function
        parsed_recipe = parse_recipe_text(openai_client, free_text)

        return jsonify({
            "success": True,
            "parsedRecipe": parsed_recipe
        }), 200

    except ValueError as e:
        if "not configured" in str(e):
            return jsonify({"error": "OpenAI API key not configured"}), 500
        return jsonify({"error": str(e)}), 400
    except json.JSONDecodeError:
        current_app.logger.exception("Failed to parse AI response")
        return jsonify({"error": "Failed to parse AI response"}), 500
    except Exception:
        current_app.logger.exception("Error parsing recipe")
        return jsonify({"error": "Error parsing recipe"}), 500

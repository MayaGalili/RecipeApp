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


@admin_required
def parse_recipe():
    """Parse free text recipe using OpenAI API"""
    try:
        openai_client = current_app.config['OPENAI_CLIENT']
        if not openai_client:
            return jsonify({"error": "OpenAI API key not configured"}), 500
        
        data = request.json
        if not data or 'freeText' not in data:
            return jsonify({"error": "No recipe text provided"}), 400
        
        free_text = data['freeText']
        if not isinstance(free_text, str) or not free_text.strip():
            return jsonify({"error": "Recipe text is empty"}), 400
        if len(free_text) > 5000:
            return jsonify({"error": "Recipe text is too long (max 5000 characters)"}), 400
        if rate_limited('parse-recipe', 10, 3600):
            return jsonify({"error": "Too many parse requests, try again later"}), 429
        
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
            max_tokens=2000,
            timeout=30,
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
        if parsed_recipe['category'] not in VALID_CATEGORIES:
            parsed_recipe['category'] = 'meat_fish'  # Default
        
        return jsonify({
            "success": True,
            "parsedRecipe": parsed_recipe
        }), 200
        
    except json.JSONDecodeError:
        current_app.logger.exception("Failed to parse AI response")
        return jsonify({"error": "Failed to parse AI response"}), 500
    except Exception:
        current_app.logger.exception("Error parsing recipe")
        return jsonify({"error": "Error parsing recipe"}), 500

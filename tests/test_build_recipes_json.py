from scripts.build_recipes_json import load_and_validate, build_from_folder
from scripts.migrate_to_db import select_new
from recipe_app.models import Recipe, RecipeTranslation, RecipeCategory


class TestLoadAndValidate:
    """Test JSON validation."""

    def test_valid_structure(self):
        data = {
            "recipes": {"soup1": {"name": "🍲 סופ", "emoji": "🍲", "ingredients": {"he": [], "en": []}, "instructions": {"he": [], "en": []}}},
            "recipeTranslations": {"he": {"soup1": "סופ"}, "en": {"soup1": "Soup"}},
            "recipeCategoryMap": {"meat_fish": [], "pasta_sauces": [], "sides": [], "salads": [], "soups": ["soup1"], "desserts": [], "holidays": []}
        }
        errors = load_and_validate(data)
        assert len(errors) == 0

    def test_missing_category(self):
        data = {
            "recipes": {},
            "recipeTranslations": {"he": {}, "en": {}},
            "recipeCategoryMap": {"soups": []}  # missing other categories
        }
        errors = load_and_validate(data)
        assert any("missing category" in e for e in errors)

    def test_invalid_recipe_name_type(self):
        data = {
            "recipes": {"bad": {"name": 123, "emoji": "🍲", "ingredients": {"he": [], "en": []}, "instructions": {"he": [], "en": []}}},
            "recipeTranslations": {"he": {}, "en": {}},
            "recipeCategoryMap": {c: [] for c in ["meat_fish", "pasta_sauces", "sides", "salads", "soups", "desserts", "holidays"]}
        }
        errors = load_and_validate(data)
        assert any("must be a non-empty string" in e for e in errors)

    def test_build_from_folder(self):
        p = ""


class TestSelectNewFunction:
    """Test the select_new filtering function used by migrate_to_db."""

    def test_filter_existing_recipes(self):
        # Create mock model instances
        r1 = Recipe(recipe_key="existing", emoji="🍲", name="🍲 Existing", category="soups")
        r2 = Recipe(recipe_key="new", emoji="🍲", name="🍲 New", category="soups")
        t1 = RecipeTranslation(recipe_key="existing", language="en", translation="Existing")
        t2 = RecipeTranslation(recipe_key="new", language="en", translation="New")
        c1 = RecipeCategory(recipe_key="existing", category="soups")
        c2 = RecipeCategory(recipe_key="new", category="soups")

        existing_keys = {"existing"}

        r_new, t_new, c_new = select_new([r1, r2], [t1, t2], [c1, c2], existing_keys)

        assert len(r_new) == 1
        assert r_new[0].recipe_key == "new"
        assert len(t_new) == 1
        assert t_new[0].recipe_key == "new"
        assert len(c_new) == 1
        assert c_new[0].recipe_key == "new"

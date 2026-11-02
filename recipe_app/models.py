"""Database models."""

import json

from .extensions import db

class Recipe(db.Model):
    __tablename__ = 'recipes'
    recipe_key = db.Column(db.String(255), primary_key=True)
    emoji = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    ingredients_he = db.Column(db.Text, nullable=False)  # JSON string
    ingredients_en = db.Column(db.Text, nullable=False)  # JSON string
    instructions_he = db.Column(db.Text, nullable=False)  # JSON string
    instructions_en = db.Column(db.Text, nullable=False)  # JSON string
    category = db.Column(db.String(50), nullable=False)
    
    def to_dict(self):
        return {
            'emoji': self.emoji,
            'name': self.name,
            'ingredients': {
                'he': json.loads(self.ingredients_he),
                'en': json.loads(self.ingredients_en)
            },
            'instructions': {
                'he': json.loads(self.instructions_he),
                'en': json.loads(self.instructions_en)
            }
        }

class RecipeTranslation(db.Model):
    __tablename__ = 'recipe_translations'
    id = db.Column(db.Integer, primary_key=True)
    recipe_key = db.Column(db.String(255), db.ForeignKey('recipes.recipe_key', ondelete='CASCADE'), nullable=False)
    language = db.Column(db.String(2), nullable=False)  # 'he' or 'en'
    translation = db.Column(db.String(255), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('recipe_key', 'language', name='unique_recipe_lang'),)

class RecipeCategory(db.Model):
    __tablename__ = 'recipe_categories'
    id = db.Column(db.Integer, primary_key=True)
    recipe_key = db.Column(db.String(255), db.ForeignKey('recipes.recipe_key', ondelete='CASCADE'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('recipe_key', 'category', name='unique_recipe_category'),)

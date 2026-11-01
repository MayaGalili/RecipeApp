#!/usr/bin/env python3
"""
Entry point for the Recipe App: `gunicorn app:app` (production) or `python3 app.py` (development).
The application code lives in the recipe_app package.
"""

import os

from recipe_app import create_app
from recipe_app.extensions import db  # noqa: F401  (re-exported for migrate_to_db.py)
from recipe_app.models import Recipe, RecipeTranslation, RecipeCategory  # noqa: F401

app = create_app()

if __name__ == '__main__':
    # Only use Flask's development server for local development
    print("Starting Recipe App server...")
    print("Server will be available at http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    print("Note: For production, use gunicorn: gunicorn app:app")
    app.run(host='127.0.0.1', port=5001, debug=os.environ.get('FLASK_DEBUG') == '1')

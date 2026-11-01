"""Recipe App: application factory."""

import os

from dotenv import load_dotenv
from flask import Flask

from . import ai_parser, auth, pages, recipes_api
from .config import load_config
from .extensions import db

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app():
    load_dotenv()

    # root_path is the project folder, so 'static' and 'templates' resolve as before
    app = Flask('app', root_path=ROOT_PATH, static_folder='static', template_folder='templates')
    app.config.update(load_config())
    app.extensions['rate_hits'] = {}  # per-app login / parse rate limiting state
    app.config['OPENAI_CLIENT'] = ai_parser.create_openai_client()

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.context_processor(auth.inject_csrf_token)
    app.before_request(auth.check_csrf)

    # Endpoint names equal the view function names (templates use url_for('login'), ...)
    app.add_url_rule('/', view_func=pages.index)
    app.add_url_rule('/login', view_func=auth.login, methods=['GET', 'POST'])
    app.add_url_rule('/logout', view_func=auth.logout, methods=['POST'])
    app.add_url_rule('/manage', view_func=pages.manage)
    app.add_url_rule('/recipe/<recipe_key>', view_func=pages.share_recipe)
    app.add_url_rule('/recipes.json', view_func=pages.serve_recipes)
    app.add_url_rule('/api/add-recipe', view_func=recipes_api.add_recipe, methods=['POST'])
    app.add_url_rule('/api/update-recipe', view_func=recipes_api.update_recipe, methods=['PUT'])
    app.add_url_rule('/api/delete-recipe', view_func=recipes_api.delete_recipe, methods=['DELETE'])
    app.add_url_rule('/api/parse-recipe', view_func=ai_parser.parse_recipe, methods=['POST'])
    return app

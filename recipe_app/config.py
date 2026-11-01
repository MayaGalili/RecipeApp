"""Configuration read from environment variables (and .env, loaded by create_app)."""

import os
from datetime import timedelta


def load_config():
    """Return the Flask config dict. Admin features stay disabled unless both
    SECRET_KEY and ADMIN_PASSWORD_HASH are set (fail closed)."""
    # Use PostgreSQL if DATABASE_URL is set, otherwise fall back to SQLite for local development
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # SQLAlchemy needs postgresql:// (not postgres://)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
    else:
        database_url = 'sqlite:///recipes.db'

    is_production = bool(os.environ.get('DATABASE_URL')) and os.environ.get('FLASK_DEBUG') != '1'
    return {
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'ADMIN_PASSWORD_HASH': os.environ.get('ADMIN_PASSWORD_HASH'),
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'SESSION_COOKIE_SECURE': is_production,  # plain http://localhost must still work in development
        'PERMANENT_SESSION_LIFETIME': timedelta(hours=8),
        'MAX_CONTENT_LENGTH': 1024 * 1024,
        'SQLALCHEMY_DATABASE_URI': database_url,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    }

import importlib
import re
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASSWORD = 'test-password'
RECIPE = {
    'recipeKey': 'test_recipe',
    'recipe': {'emoji': '🍳', 'name': 'Test', 'ingredients': {'he': [], 'en': []}, 'instructions': {'he': [], 'en': []}},
    'category': 'sides',
    'translations': {'he': 'בדיקה', 'en': 'Test'},
}


def load_app(monkeypatch, configured=True):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
    monkeypatch.setenv('FLASK_DEBUG', '1')  # non-secure cookies so the http test client keeps them
    monkeypatch.setenv('OPENAI_API_KEY', '')
    if configured:
        monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
        monkeypatch.setenv('ADMIN_PASSWORD_HASH', generate_password_hash(PASSWORD))
    else:
        monkeypatch.delenv('SECRET_KEY', raising=False)
        monkeypatch.delenv('ADMIN_PASSWORD_HASH', raising=False)
    sys.modules.pop('app', None)
    module = importlib.import_module('app')
    module.app.config['TESTING'] = True
    return module


@pytest.fixture
def app_module(monkeypatch):
    return load_app(monkeypatch)


@pytest.fixture
def client(app_module):
    return app_module.app.test_client()


def csrf_from(response):
    html = response.get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def login(client, password=PASSWORD):
    token = csrf_from(client.get('/login'))
    return client.post('/login', data={'password': password, 'csrf_token': token})


@pytest.fixture
def admin(client):
    assert login(client).status_code == 302
    token = re.search(r'name="csrf-token" content="([^"]+)"', client.get('/manage').get_data(as_text=True)).group(1)
    client.csrf = {'X-CSRF-Token': token}
    return client


def test_anonymous_cannot_use_write_endpoints(client):
    assert client.post('/api/add-recipe', json=RECIPE).status_code == 401
    assert client.put('/api/update-recipe', json=RECIPE).status_code == 401
    assert client.delete('/api/delete-recipe', json={'recipeKey': 'x'}).status_code == 401
    assert client.post('/api/parse-recipe', json={'freeText': 'soup'}).status_code == 401


def test_anonymous_manage_redirects_to_login(client):
    response = client.get('/manage')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login')


def test_public_pages_stay_public(client):
    assert client.get('/').status_code == 200
    assert client.get('/recipes.json').status_code == 200
    assert client.get('/recipe/does_not_exist').status_code == 404


def test_wrong_password_rejected(client):
    assert login(client, 'wrong').status_code == 401
    assert client.get('/manage').status_code == 302


def test_correct_password_grants_access(client):
    assert login(client).status_code == 302
    assert client.get('/manage').status_code == 200


def test_login_requires_csrf_token(client):
    client.get('/login')
    assert client.post('/login', data={'password': PASSWORD}).status_code == 403


def test_login_throttled_after_repeated_failures(client):
    for _ in range(5):
        assert login(client, 'wrong').status_code == 401
    assert login(client, 'wrong').status_code == 429
    assert login(client).status_code == 429  # even the right password waits out the lockout


def test_write_requires_csrf_token(admin):
    assert admin.post('/api/add-recipe', json=RECIPE).status_code == 403
    assert admin.post('/api/add-recipe', json=RECIPE, headers={'X-CSRF-Token': 'wrong'}).status_code == 403


def test_admin_can_add_and_delete_recipe(admin):
    assert admin.post('/api/add-recipe', json=RECIPE, headers=admin.csrf).status_code == 200
    assert 'test_recipe' in admin.get('/recipes.json').get_json()['recipes']
    assert admin.delete('/api/delete-recipe', json={'recipeKey': 'test_recipe'}, headers=admin.csrf).status_code == 200


def test_logout_ends_session(admin):
    assert admin.post('/logout', data={'csrf_token': admin.csrf['X-CSRF-Token']}).status_code == 302
    assert admin.get('/manage').status_code == 302


def test_parse_recipe_never_calls_openai_when_anonymous(client, app_module):
    class Boom:
        def __getattr__(self, name):
            raise AssertionError('OpenAI must not be called')
    app_module.openai_client = Boom()
    assert client.post('/api/parse-recipe', json={'freeText': 'soup'}).status_code == 401


def test_parse_recipe_limits(admin, app_module):
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            raise RuntimeError('stop here')  # past the guards, enough to count the call

    class FakeClient:
        chat = type('Chat', (), {'completions': FakeCompletions()})()

    app_module.openai_client = FakeClient()
    too_long = admin.post('/api/parse-recipe', json={'freeText': 'x' * 5001}, headers=admin.csrf)
    assert too_long.status_code == 400 and not calls
    for _ in range(10):
        assert admin.post('/api/parse-recipe', json={'freeText': 'soup'}, headers=admin.csrf).status_code == 500
    assert admin.post('/api/parse-recipe', json={'freeText': 'soup'}, headers=admin.csrf).status_code == 429
    assert len(calls) == 10 and calls[0]['max_tokens'] and calls[0]['timeout']


def test_session_cookie_flags(client):
    cookie = client.get('/login').headers['Set-Cookie']
    assert 'HttpOnly' in cookie and 'SameSite=Lax' in cookie


def test_login_disabled_when_not_configured(monkeypatch):
    module = load_app(monkeypatch, configured=False)
    client = module.app.test_client()
    assert client.get('/login').status_code == 503
    assert client.post('/login', data={'password': PASSWORD}).status_code == 503
    assert client.post('/api/add-recipe', json=RECIPE).status_code == 401
    assert client.get('/').status_code == 200

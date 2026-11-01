import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv('OPENAI_API_KEY', '')
    sys.modules.pop('app', None)
    module = importlib.import_module('app')
    # This branch stores recipes in a JSON file: point it at a temp file so real data is never touched
    monkeypatch.setattr(module, 'DATA_DIR', str(tmp_path))
    monkeypatch.setattr(module, 'RECIPES_FILE', str(tmp_path / 'recipes.json'))
    module.app.config['TESTING'] = True
    return module.app.test_client()


def payload(emoji, name='Tomato Soup', ingredient='Tomato'):
    return {
        'recipeKey': 'tomato_soup',
        'recipe': {
            'emoji': emoji,
            'name': f'{emoji} {name}',
            'ingredients': {'he': [], 'en': [{'name': ingredient, 'amount': 1, 'unit': 'kg', 'category': 'Vegetables'}]},
            'instructions': {'he': [], 'en': ['Cook']},
        },
        'category': 'soups',
        'translations': {'he': 'מרק עגבניות', 'en': name},
    }


def stored_emoji(client):
    return client.get('/recipes.json').get_json()['recipes']['tomato_soup']['emoji']


def test_emoji_outside_predefined_list_is_saved_and_reloaded(client):
    assert client.post('/api/add-recipe', json=payload('🍅')).status_code == 200
    assert stored_emoji(client) == '🍅'


def test_editing_other_fields_keeps_emoji(client):
    client.post('/api/add-recipe', json=payload('🍅'))
    edited = payload('🍅', name='Spicy Tomato Soup', ingredient='Chili')
    assert client.put('/api/update-recipe', json=edited).status_code == 200
    assert stored_emoji(client) == '🍅'


def test_emoji_can_be_replaced(client):
    client.post('/api/add-recipe', json=payload('🍅'))
    assert client.put('/api/update-recipe', json=payload('🥣')).status_code == 200
    assert stored_emoji(client) == '🥣'


def test_multi_codepoint_emoji_fits_column(client):
    family = '👨‍👩‍👧‍👦'
    assert client.post('/api/add-recipe', json=payload(family)).status_code == 200
    assert stored_emoji(client) == family

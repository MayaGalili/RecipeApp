from test_auth import admin, app_module, client  # noqa: F401  (fixtures: in-memory DB, logged-in admin with CSRF header)


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


def add(admin, emoji):
    return admin.post('/api/add-recipe', json=payload(emoji), headers=admin.csrf)


def update(admin, **kwargs):
    return admin.put('/api/update-recipe', json=payload(**kwargs), headers=admin.csrf)


def stored_emoji(admin):
    return admin.get('/recipes.json').get_json()['recipes']['tomato_soup']['emoji']


def test_emoji_outside_predefined_list_is_saved_and_reloaded(admin):
    assert add(admin, '🍅').status_code == 200
    assert stored_emoji(admin) == '🍅'


def test_editing_other_fields_keeps_emoji(admin):
    add(admin, '🍅')
    assert update(admin, emoji='🍅', name='Spicy Tomato Soup', ingredient='Chili').status_code == 200
    assert stored_emoji(admin) == '🍅'


def test_emoji_can_be_replaced(admin):
    add(admin, '🍅')
    assert update(admin, emoji='🥣').status_code == 200
    assert stored_emoji(admin) == '🥣'


def test_multi_codepoint_emoji_fits_column(admin):
    family = '👨‍👩‍👧‍👦'
    assert add(admin, family).status_code == 200
    assert stored_emoji(admin) == family

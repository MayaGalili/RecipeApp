const test = require('node:test');
const assert = require('node:assert/strict');
const { aggregateIngredients, scaleExact, roundAmount, resolveUnit } =
    require('../../static/js/shopping-list-aggregate.js');

const ing = (name, amount, unit, category = 'Veg') => ({ name, amount, unit, category });
const mk = (en, he = en) => ({ ingredients: { en, he } });
const flat = result => result.flatMap(c => c.items.map(i => [c.category, i.name, i.amount, i.unit]));

test('scaleExact scales from 4 base servings without rounding', () => {
    assert.equal(scaleExact(100, 4), 100);
    assert.equal(scaleExact(100, 2), 50);
    assert.equal(scaleExact(1, 6), 1.5);
    assert.equal(scaleExact(1, 1), 0.25);
});

test('roundAmount keeps the existing display precision', () => {
    assert.equal(roundAmount(0.26), 0.3);
    assert.equal(roundAmount(2.4), 2.5);
    assert.equal(roundAmount(12.3), 12.5);
});

test('each recipe is scaled by its own servings before combining', () => {
    const recipes = { a: mk([ing('Onion', 2, 'pieces')]), b: mk([ing('Onion', 2, 'pieces')]) };
    const out = aggregateIngredients({ a: 4, b: 8 }, recipes, 'en');
    assert.deepEqual(flat(out), [['Veg', 'Onion', 6, 'pieces']]);
});

test('rounding happens once on the total, not per recipe', () => {
    // 0.25 + 0.25 + 0.25 per recipe at 1 serving = 0.75; per-recipe rounding would give 0.3 * 3
    const r = () => mk([ing('Salt', 1, 'tsp')]);
    const out = aggregateIngredients({ a: 1, b: 1, c: 1 }, { a: r(), b: r(), c: r() }, 'en');
    assert.equal(out[0].items[0].amount, 0.8);
});

test('names match ignoring case and surrounding whitespace', () => {
    const recipes = { a: mk([ing('Garlic', 1, 'cloves')]), b: mk([ing(' garlic ', 2, 'cloves')]) };
    const out = aggregateIngredients({ a: 4, b: 4 }, recipes, 'en');
    assert.deepEqual(flat(out), [['Veg', 'Garlic', 3, 'cloves']]);
});

test('singular and plural spellings of one unit combine', () => {
    const recipes = { a: mk([ing('Sugar', 1, 'cup')]), b: mk([ing('Sugar', 1, 'cups')]) };
    assert.deepEqual(flat(aggregateIngredients({ a: 4, b: 4 }, recipes, 'en')), [['Veg', 'Sugar', 2, 'cups']]);
    const he = { a: mk([ing('סוכר', 1, 'כוס')]), b: mk([ing('סוכר', 1, 'כוסות')]) };
    assert.deepEqual(flat(aggregateIngredients({ a: 4, b: 4 }, he, 'he')), [['Veg', 'סוכר', 2, 'כוסות']]);
});

test('g and kg combine through conversion', () => {
    const recipes = { a: mk([ing('Flour', 500, 'g')]), b: mk([ing('Flour', 1, 'kg')]) };
    assert.deepEqual(flat(aggregateIngredients({ a: 4, b: 4 }, recipes, 'en')), [['Veg', 'Flour', 1.5, 'kg']]);
});

test('mixed g/kg staying under 1000 g is shown in g', () => {
    const recipes = { a: mk([ing('Flour', 200, 'g')]), b: mk([ing('Flour', 0.3, 'kg')]) };
    assert.deepEqual(flat(aggregateIngredients({ a: 4, b: 4 }, recipes, 'en')), [['Veg', 'Flour', 500, 'g']]);
});

test('ml and l combine; mass and volume never mix', () => {
    const recipes = { a: mk([ing('Milk', 250, 'ml')]), b: mk([ing('Milk', 1, 'l')]), c: mk([ing('Milk', 100, 'g')]) };
    const out = flat(aggregateIngredients({ a: 4, b: 4, c: 4 }, recipes, 'en'));
    assert.deepEqual(out, [['Veg', 'Milk', 1.25, 'l'], ['Veg', 'Milk', 100, 'g']]);
});

test('incompatible units for the same ingredient stay separate', () => {
    const recipes = {
        a: mk([ing('Butter', 2, 'tbsp'), ing('Butter', 1, 'cup')]),
        b: mk([ing('Butter', 100, 'g'), ing('Butter', 1, 'pack')])
    };
    const out = flat(aggregateIngredients({ a: 4, b: 4 }, recipes, 'en'));
    assert.deepEqual(out, [
        ['Veg', 'Butter', 2, 'tbsp'], ['Veg', 'Butter', 1, 'cup'],
        ['Veg', 'Butter', 100, 'g'], ['Veg', 'Butter', 1, 'pack']
    ]);
});

test('variants such as "level tbsp" or "large pieces" are not merged into the plain unit', () => {
    const recipes = {
        a: mk([ing('Salt', 1, 'tbsp'), ing('Egg', 2, 'pieces')]),
        b: mk([ing('Salt', 1, 'level tbsp'), ing('Egg', 1, 'large pieces')])
    };
    assert.equal(flat(aggregateIngredients({ a: 4, b: 4 }, recipes, 'en')).length, 4);
});

test('unknown units merge only when the text is identical', () => {
    const recipes = { a: mk([ing('Basil', 1, 'bunch')]), b: mk([ing('Basil', 1, 'Bunch')]), c: mk([ing('Basil', 1, 'handful')]) };
    assert.deepEqual(flat(aggregateIngredients({ a: 4, b: 4, c: 4 }, recipes, 'en')),
        [['Veg', 'Basil', 2, 'bunch'], ['Veg', 'Basil', 1, 'handful']]);
});

test('ingredients are grouped by category in first-seen order', () => {
    const recipes = {
        a: mk([ing('Beef', 1, 'kg', 'Meat'), ing('Onion', 1, 'pieces', 'Veg')]),
        b: mk([ing('Carrot', 1, 'pieces', 'Veg'), ing('Rice', 1, 'cup', 'Pantry')])
    };
    const out = aggregateIngredients({ a: 4, b: 4 }, recipes, 'en');
    assert.deepEqual(out.map(c => [c.category, c.items.map(i => i.name)]),
        [['Meat', ['Beef']], ['Veg', ['Onion', 'Carrot']], ['Pantry', ['Rice']]]);
});

test('uses the requested language and falls back to Hebrew when it is empty', () => {
    const recipes = { a: { ingredients: { he: [ing('בצל', 1, 'יחידה')], en: [ing('Onion', 1, 'piece')] } },
                      b: { ingredients: { he: [ing('שום', 1, 'שן')], en: [] } } };
    assert.deepEqual(flat(aggregateIngredients({ a: 4, b: 4 }, recipes, 'en')),
        [['Veg', 'Onion', 1, 'piece'], ['Veg', 'שום', 1, 'שן']]);
});

test('unknown recipes, invalid servings and non-numeric amounts are skipped', () => {
    const recipes = { a: mk([ing('Onion', 'a pinch', 'pieces'), ing('Salt', 1, 'tsp')]) };
    assert.deepEqual(flat(aggregateIngredients({ a: 4, missing: 4 }, recipes, 'en')), [['Veg', 'Salt', 1, 'tsp']]);
    assert.deepEqual(aggregateIngredients({ a: 0 }, recipes, 'en'), []);
    assert.deepEqual(aggregateIngredients({}, recipes, 'en'), []);
});

test('resolveUnit groups convertible units and isolates the rest', () => {
    assert.equal(resolveUnit('g').groupKey, resolveUnit('kg').groupKey);
    assert.equal(resolveUnit('גרם').groupKey, resolveUnit('ק"ג').groupKey);
    assert.notEqual(resolveUnit('g').groupKey, resolveUnit('ml').groupKey);
    assert.notEqual(resolveUnit('cup').groupKey, resolveUnit('tbsp').groupKey);
});

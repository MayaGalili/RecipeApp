// Pure ingredient scaling and combining for the multi-recipe shopping list.
// No DOM access: usable from the browser (window.ShoppingListAggregate) and from node tests.
(function (root, factory) {
    if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.ShoppingListAggregate = factory();
    }
})(typeof self !== 'undefined' ? self : this, function () {
    const BASE_SERVINGS = 4;
    const DEFAULT_SERVINGS = 4;

    // Units that may be merged. Each entry maps every spelling (he / en, singular / plural)
    // to a unit `key`. Units sharing a `family` are convertible through `factor` (to the
    // family's base unit). Anything not listed here only merges with the exact same text,
    // so e.g. "cup" never merges with "tbsp" and "pieces" never merges with "large pieces".
    const UNIT_DEFS = [
        { key: 'g',    family: 'mass',   factor: 1,    forms: ['g', 'gr', 'gram', 'grams', 'גרם', 'גר׳'] },
        { key: 'kg',   family: 'mass',   factor: 1000, forms: ['kg', 'kilogram', 'kilograms', 'ק"ג', 'קג', 'קילו'] },
        { key: 'ml',   family: 'volume', factor: 1,    forms: ['ml', 'milliliter', 'milliliters', 'מ"ל', 'מל'] },
        { key: 'l',    family: 'volume', factor: 1000, forms: ['l', 'liter', 'liters', 'ליטר', 'ל׳'] },
        { key: 'cup',  forms: ['cup', 'cups', 'כוס', 'כוסות'], singular: ['cup', 'כוס'], plural: ['cups', 'כוסות'] },
        { key: 'tbsp', forms: ['tbsp', 'כף', 'כפות'], singular: ['tbsp', 'כף'], plural: ['tbsp', 'כפות'] },
        { key: 'tsp',  forms: ['tsp', 'כפית', 'כפיות'], singular: ['tsp', 'כפית'], plural: ['tsp', 'כפיות'] },
        { key: 'piece', forms: ['piece', 'pieces', 'יחידה', 'יחידות'], singular: ['piece', 'יחידה'], plural: ['pieces', 'יחידות'] }
    ];

    const UNIT_LOOKUP = {};
    UNIT_DEFS.forEach(def => def.forms.forEach(form => { UNIT_LOOKUP[normalizeText(form)] = def; }));

    function normalizeText(text) {
        return String(text == null ? '' : text).trim().replace(/\s+/g, ' ').toLowerCase();
    }

    // Exact scaling from the recipe's base servings, no rounding.
    function scaleExact(baseAmount, servings) {
        return baseAmount * (servings / BASE_SERVINGS);
    }

    // Round to a reasonable precision for display.
    function roundAmount(amount) {
        if (amount < 1) {
            return Math.round(amount * 10) / 10;
        } else if (amount < 10) {
            return Math.round(amount * 4) / 4;
        }
        return Math.round(amount * 2) / 2;
    }

    // Resolve a unit string to { groupKey, factor, def, label }.
    // Units with the same groupKey can be added together after multiplying by factor.
    function resolveUnit(unit) {
        const label = String(unit == null ? '' : unit).trim();
        const def = UNIT_LOOKUP[normalizeText(label)];
        if (def && def.family) {
            return { groupKey: `family:${def.family}`, factor: def.factor, def, label };
        }
        if (def) {
            return { groupKey: `unit:${def.key}`, factor: 1, def, label };
        }
        return { groupKey: `text:${normalizeText(label)}`, factor: 1, def: null, label };
    }

    // Pick the unit label to display for a merged total.
    function displayUnit(group) {
        const { def, labels, totalBase } = group;
        if (def && def.family) {
            // Convertible family: keep a single original unit as-is, otherwise show the
            // largest unit that keeps the number >= 1 (g -> kg, ml -> l).
            if (group.unitKeys.size === 1) {
                const only = UNIT_DEFS.find(d => d.key === [...group.unitKeys][0]);
                return { amount: totalBase / only.factor, unit: labels[0] };
            }
            const base = UNIT_DEFS.find(d => d.family === def.family && d.factor === 1);
            const big = UNIT_DEFS.find(d => d.family === def.family && d.factor === 1000);
            if (totalBase >= 1000) {
                return { amount: totalBase / 1000, unit: pickLabel(big, labels, false) };
            }
            return { amount: totalBase, unit: pickLabel(base, labels, false) };
        }
        if (def && labels.length > 1) {
            // Same unit spelled differently (cup / cups): choose by the total
            const plural = totalBase !== 1;
            return { amount: totalBase, unit: pickLabel(def, labels, plural) };
        }
        return { amount: totalBase, unit: labels[0] };
    }

    // Choose the spelling of `def` in the same language as the labels that were merged.
    function pickLabel(def, labels, plural) {
        const seen = labels.map(normalizeText);
        const pool = plural && def.plural ? def.plural : (def.singular || def.forms);
        const sameLanguage = pool.find(form => isHebrew(form) === isHebrew(seen[0]));
        return sameLanguage || pool[0];
    }

    function isHebrew(text) {
        return /[֐-׿]/.test(text);
    }

    // Scale each selected recipe by its own servings and combine identical ingredients.
    //   selection: { recipeKey: servings }
    //   recipes:   the recipes object ({ key: { ingredients: { he: [...], en: [...] } } })
    //   language:  'he' | 'en' (falls back to 'he' when a recipe lacks that language)
    // Returns [{ category, items: [{ name, amount, unit }] }] in first-seen order.
    // Amounts are summed unrounded and rounded once at the end.
    function aggregateIngredients(selection, recipes, language) {
        const categories = [];       // preserves first-seen category order
        const categoryIndex = {};
        const groups = {};           // `${name}||${groupKey}` -> group

        Object.keys(selection).forEach(recipeKey => {
            const recipe = recipes[recipeKey];
            const servings = Number(selection[recipeKey]);
            if (!recipe || !(servings > 0)) return;

            const ingredients = (recipe.ingredients[language] && recipe.ingredients[language].length)
                ? recipe.ingredients[language]
                : recipe.ingredients.he || [];

            ingredients.forEach(ingredient => {
                const amount = Number(ingredient.amount);
                if (!Number.isFinite(amount)) return;

                const unit = resolveUnit(ingredient.unit);
                const id = `${normalizeText(ingredient.name)}||${unit.groupKey}`;
                let group = groups[id];
                if (!group) {
                    group = groups[id] = {
                        name: String(ingredient.name).trim(),
                        category: ingredient.category,
                        def: unit.def,
                        totalBase: 0,
                        labels: [],
                        unitKeys: new Set()
                    };
                    if (!(ingredient.category in categoryIndex)) {
                        categoryIndex[ingredient.category] = categories.length;
                        categories.push({ category: ingredient.category, groups: [] });
                    }
                    categories[categoryIndex[ingredient.category]].groups.push(group);
                }
                group.totalBase += scaleExact(amount, servings) * unit.factor;
                if (!group.labels.includes(unit.label)) group.labels.push(unit.label);
                group.unitKeys.add(unit.def ? unit.def.key : unit.groupKey);
            });
        });

        return categories.map(({ category, groups: categoryGroups }) => ({
            category,
            items: categoryGroups.map(group => {
                const shown = displayUnit(group);
                return { name: group.name, amount: roundAmount(shown.amount), unit: shown.unit };
            })
        }));
    }

    return {
        BASE_SERVINGS,
        DEFAULT_SERVINGS,
        scaleExact,
        roundAmount,
        resolveUnit,
        aggregateIngredients
    };
});

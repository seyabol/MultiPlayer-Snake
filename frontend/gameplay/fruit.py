import random

FOOD_POOL = [
    {'emoji': '🍎', 'value': 10, 'weight': 6},
    {'emoji': '🍓', 'value': 10, 'weight': 6},
    {'emoji': '🍇', 'value': 15, 'weight': 4},
    {'emoji': '🍒', 'value': 15, 'weight': 4},
    {'emoji': '🍌', 'value': 20, 'weight': 3},
    {'emoji': '🍍', 'value': 25, 'weight': 2},
    {'emoji': '🍉', 'value': 25, 'weight': 2},
    {'emoji': '🥝', 'value': 30, 'weight': 1},
    {'emoji': '🍔', 'value': 40, 'weight': 1},
]


def pick_food():
    total = sum(x['weight'] for x in FOOD_POOL)
    r = random.randint(1, total)
    acc = 0
    for item in FOOD_POOL:
        acc += item['weight']
        if r <= acc:
            return dict(item)
    return dict(FOOD_POOL[0])

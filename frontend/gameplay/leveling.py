LEVELS = [
    (1, 0, 230),
    (2, 50, 215),
    (3, 120, 200),
    (4, 200, 185),
    (5, 290, 170),
    (6, 390, 158),
    (7, 500, 148),
    (8, 650, 140),
]


def get_level(score: int) -> int:
    level = 1
    for lvl, min_score, _ in LEVELS:
        if score >= min_score:
            level = lvl
    return level


def move_interval_ms(score: int) -> int:
    interval = LEVELS[0][2]
    for _, min_score, ms in LEVELS:
        if score >= min_score:
            interval = ms
    return interval

import pygame


def get_emoji_font(size: int):
    candidates = [
        'Segoe UI Emoji',
        'Apple Color Emoji',
        'Noto Color Emoji',
        'Noto Emoji',
        'Twitter Color Emoji',
    ]

    for name in candidates:
        try:
            f = pygame.font.SysFont(name, size)
            if f:
                return f
        except Exception:
            continue

    return pygame.font.Font(None, size)

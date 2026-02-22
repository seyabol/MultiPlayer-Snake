import pygame
from . import theme


def draw_panel(surface, rect, *, border_radius=14, border=2):
    pygame.draw.rect(surface, theme.PANEL_BG, rect, border_radius=border_radius)
    pygame.draw.rect(surface, theme.PANEL_BORDER, rect, border, border_radius=border_radius)


def draw_title(surface, font, text, center):
    s = font.render(text, True, theme.TEXT)
    r = s.get_rect(center=center)
    surface.blit(s, r)


def draw_text(surface, font, text, pos, color=theme.TEXT):
    s = font.render(text, True, color)
    surface.blit(s, pos)


def draw_badge(surface, font, text, rect, *, bg, fg=theme.TEXT, border_radius=10):
    pygame.draw.rect(surface, bg, rect, border_radius=border_radius)
    s = font.render(text, True, fg)
    r = s.get_rect(center=rect.center)
    surface.blit(s, r)


def draw_list_item(surface, font, text_left, text_right, rect, *, selected=False):
    bg = (45, 45, 62) if not selected else (55, 60, 85)
    border = theme.PANEL_BORDER if not selected else theme.PRIMARY

    pygame.draw.rect(surface, bg, rect, border_radius=10)
    pygame.draw.rect(surface, border, rect, 2, border_radius=10)

    left = font.render(text_left, True, theme.TEXT)
    surface.blit(left, (rect.x + 12, rect.y + (rect.height - left.get_height()) // 2))

    if text_right:
        right = font.render(text_right, True, theme.MUTED)
        surface.blit(right, (rect.right - 12 - right.get_width(), rect.y + (rect.height - right.get_height()) // 2))


def draw_hint(surface, font, text, center):
    s = font.render(text, True, theme.MUTED)
    r = s.get_rect(center=center)
    surface.blit(s, r)

import pygame
import requests

import consts
from ui.widgets import draw_panel, draw_title, draw_text, draw_list_item, draw_hint
from ui import theme


class UIManager:
    def __init__(self, screen, title_font, font, small_font):
        self.screen = screen
        self.title_font = title_font
        self.font = font
        self.small_font = small_font
        self.back_requested = False

    def _handle_back(self, events):
        self.back_requested = False
        for e in events:
            if e.type == pygame.KEYDOWN and (e.key == pygame.K_ESCAPE or e.key == pygame.K_BACKSPACE):
                self.back_requested = True
                return

    def draw_stats(self, user_id, server_url, events):
        self._handle_back(events)
        self.screen.fill(consts.back_color)

        draw_title(self.screen, self.title_font, "Your Stats", (consts.width // 2, 80))

        panel = pygame.Rect(60, 150, consts.width - 120, consts.height - 220)
        draw_panel(self.screen, panel)

        stats = {}
        recent_games = []
        err = None

        try:
            r = requests.get(f"{server_url}/api/stats/{user_id}", timeout=5)
            if r.status_code == 200:
                data = r.json()
                stats = data.get('stats', {}) or {}
                recent_games = data.get('recentGames', []) or []
            else:
                err = f"Failed to load stats ({r.status_code})"
        except Exception:
            err = "Failed to load stats"

        x = panel.x + 26
        y = panel.y + 24

        lines = [
            ("Games played", str(stats.get('gamesPlayed', 0))),
            ("Wins", str(stats.get('wins', 0))),
            ("Total score", str(stats.get('totalScore', 0))),
        ]

        for label, value in lines:
            draw_text(self.screen, self.font, label, (x, y), theme.MUTED)
            draw_text(self.screen, self.font, value, (x + 240, y), theme.TEXT)
            y += 38

        y += 18
        draw_text(self.screen, self.small_font, "Recent games", (x, y), theme.WARNING)
        y += 16

        box = pygame.Rect(panel.x + 20, y + 18, panel.width - 40, panel.height - (y - panel.y) - 40)

        if err:
            draw_hint(self.screen, self.small_font, err, (panel.centerx, panel.centery))
        elif not recent_games:
            draw_hint(self.screen, self.small_font, "No games yet", (panel.centerx, panel.centery))
        else:
            max_rows = 10
            item_h = 48
            for i, g in enumerate(recent_games[:max_rows]):
                left = f"{i + 1}. Winner: {g.get('winner') or '-'}"
                right = f"You: {g.get('score', 0)}"
                r = pygame.Rect(box.x, box.y + i * (item_h + 8), box.width, item_h)
                draw_list_item(self.screen, self.small_font, left, right, r, selected=False)

        draw_hint(self.screen, self.small_font, "ESC to go back", (consts.width // 2, consts.height - 40))
        pygame.display.flip()

    def draw_leaderboard(self, server_url, events):
        self._handle_back(events)
        self.screen.fill(consts.back_color)

        draw_title(self.screen, self.title_font, "Leaderboard", (consts.width // 2, 80))

        panel = pygame.Rect(60, 150, consts.width - 120, consts.height - 220)
        draw_panel(self.screen, panel)

        leaderboard = []
        err = None

        try:
            r = requests.get(f"{server_url}/api/leaderboard?limit=10", timeout=5)
            if r.status_code == 200:
                leaderboard = r.json().get('leaderboard', []) or []
            else:
                err = f"Failed to load leaderboard ({r.status_code})"
        except Exception:
            err = "Failed to load leaderboard"

        if err:
            draw_hint(self.screen, self.small_font, err, (panel.centerx, panel.centery))
        elif not leaderboard:
            draw_hint(self.screen, self.small_font, "No data yet", (panel.centerx, panel.centery))
        else:
            y = panel.y + 30
            item_h = 52
            for i, row in enumerate(leaderboard):
                name = row.get('username') or row.get('id', 'Player')
                score = row.get('totalScore', 0)
                left = f"{i + 1}. {name}"
                right = str(score)
                r = pygame.Rect(panel.x + 24, y + i * (item_h + 10), panel.width - 48, item_h)
                draw_list_item(self.screen, self.small_font, left, right, r, selected=(i == 0))

        draw_hint(self.screen, self.small_font, "ESC to go back", (consts.width // 2, consts.height - 40))
        pygame.display.flip()

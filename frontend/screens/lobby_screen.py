import pygame
import time

import consts
from ui.widgets import draw_panel, draw_title, draw_text, draw_list_item, draw_hint, draw_badge
from ui import theme


class LobbyScreen:
    def __init__(self):
        self.selection = 0
        self.last_refresh = 0.0

    def _ensure_selection(self, rooms):
        if not rooms:
            self.selection = 0
            return
        self.selection = max(0, min(self.selection, len(rooms) - 1))

    def tick(self, game):
        if not game.network_manager:
            return

        now = time.time()
        if now - self.last_refresh > 3.0:
            game.network_manager.refresh_rooms()
            self.last_refresh = now

    def handle_event(self, game, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            game.state = "menu"
            return

        if not game.network_manager:
            return

        rooms = game.network_manager.get_rooms()
        self._ensure_selection(rooms)

        if event.key == pygame.K_UP and rooms:
            self.selection = (self.selection - 1) % len(rooms)
        elif event.key == pygame.K_DOWN and rooms:
            self.selection = (self.selection + 1) % len(rooms)
        elif event.key == pygame.K_r:
            game.network_manager.refresh_rooms()
            self.last_refresh = time.time()
        elif event.key == pygame.K_c:
            game.create_room()
        elif event.key == pygame.K_RETURN:
            if rooms:
                rid = rooms[self.selection].get('id')
                if rid:
                    game.join_room(rid)
        elif event.key == pygame.K_s:
            game.state = "stats"
        elif event.key == pygame.K_l:
            game.state = "leaderboard"
        elif event.key == pygame.K_o:
            if game.network_manager:
                game.network_manager.disconnect()
                game.network_manager = None
            game.auth_manager.logout()
            game.state = 'menu'

    def draw(self, game):
        game.screen.fill(consts.back_color)

        username = game.auth_manager.current_user.get('username', 'Player') if game.auth_manager.current_user else 'Player'
        draw_title(game.screen, game.title_font, f"Lobby", (consts.width // 2, 70))
        draw_text(game.screen, game.small_font, f"Signed in as {username}", (60, 110), theme.MUTED)

        side_w = 180
        rooms_panel = pygame.Rect(60, 140, consts.width - 60 - side_w - 30, consts.height - 220)
        side_panel = pygame.Rect(rooms_panel.right + 30, 140, side_w, rooms_panel.height)

        draw_panel(game.screen, rooms_panel)
        draw_panel(game.screen, side_panel)

        draw_text(game.screen, game.small_font, "Available rooms", (rooms_panel.x + 20, rooms_panel.y + 18), theme.WARNING)

        rooms = game.network_manager.get_rooms() if game.network_manager else []
        self._ensure_selection(rooms)

        if not rooms:
            draw_hint(game.screen, game.small_font, "No rooms yet. Press C to create one.", (rooms_panel.centerx, rooms_panel.centery))
        else:
            start_y = rooms_panel.y + 60
            item_h = 56
            visible = int((rooms_panel.height - 90) / item_h)
            visible = max(6, min(11, visible))

            offset = 0
            if self.selection >= visible:
                offset = self.selection - visible + 1

            for i in range(offset, min(len(rooms), offset + visible)):
                r = rooms[i]
                title = r.get('title') or r.get('host', {}).get('username', 'Room')
                host = r.get('host', {}).get('username', 'Host')
                left = f"{title}"
                right = f"{r.get('playerCount', 0)}/{r.get('maxPlayers', 4)}"

                item_rect = pygame.Rect(rooms_panel.x + 18, start_y + (i - offset) * item_h, rooms_panel.width - 36, 48)
                draw_list_item(game.screen, game.font, left, right, item_rect, selected=(i == self.selection))

                badge = pygame.Rect(item_rect.right - 96, item_rect.y + 10, 82, 28)
                draw_badge(game.screen, game.small_font, host[:12], badge, bg=(60, 60, 78), fg=theme.MUTED)

        help_lines = [
            ("ENTER", "Join"),
            ("C", "Create"),
            ("R", "Refresh"),
            ("S", "Stats"),
            ("L", "Top"),
            ("O", "Sign out"),
            ("ESC", "Back"),
        ]

        y = side_panel.y + 24
        for key, label in help_lines:
            draw_text(game.screen, game.small_font, key, (side_panel.x + 22, y), theme.WARNING)
            draw_text(game.screen, game.small_font, label, (side_panel.x + 78, y), theme.MUTED)
            y += 40

        if game.network_manager and game.network_manager.last_error:
            err = game.network_manager.last_error
            msg = game.small_font.render(err, True, theme.ERROR)
            game.screen.blit(msg, (60, consts.height - 60))
        elif game.success_message:
            msg = game.small_font.render(game.success_message, True, theme.SUCCESS)
            game.screen.blit(msg, (60, consts.height - 60))

        pygame.display.flip()

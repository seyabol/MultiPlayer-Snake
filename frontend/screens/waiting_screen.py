import pygame

import consts
from ui.widgets import draw_panel, draw_title, draw_text, draw_badge, draw_hint
from ui import theme


class WaitingScreen:
    def handle_event(self, game, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            if game.room_id and game.network_manager:
                game.network_manager.leave_room(game.room_id)
            game.room_id = None
            game.is_host = False
            game.state = "lobby"
            return

        if event.key == pygame.K_s and game.is_host:
            if len(game.players) >= 2 and game.network_manager:
                game.network_manager.start_game(game.room_id)
                game.start_game()
            else:
                game.error_message = "Need at least 2 players"

    def draw(self, game):
        game.screen.fill(consts.back_color)

        draw_title(game.screen, game.title_font, "Waiting Room", (consts.width // 2, 70))

        top = pygame.Rect(60, 140, consts.width - 120, 90)
        draw_panel(game.screen, top)

        draw_text(game.screen, game.small_font, "Room", (top.x + 20, top.y + 16), theme.MUTED)
        draw_text(game.screen, game.font, game.room_id or "-", (top.x + 20, top.y + 44), theme.TEXT)

        if game.is_host:
            badge = pygame.Rect(top.right - 150, top.y + 28, 120, 34)
            draw_badge(game.screen, game.small_font, "HOST", badge, bg=theme.PRIMARY)

        panel = pygame.Rect(60, 250, consts.width - 120, consts.height - 360)
        draw_panel(game.screen, panel)

        draw_text(game.screen, game.small_font, "Players", (panel.x + 20, panel.y + 18), theme.WARNING)

        y = panel.y + 60
        host_id = game.network_manager.get_host_id() if game.network_manager else None

        for i, p in enumerate(game.players):
            name = p.get('username', 'Player')
            line = f"{i + 1}. {name}"

            text = game.font.render(line, True, theme.TEXT)
            game.screen.blit(text, (panel.x + 26, y))

            if host_id and p.get('id') == host_id:
                badge = pygame.Rect(panel.right - 140, y + 6, 110, 30)
                draw_badge(game.screen, game.small_font, "host", badge, bg=(60, 60, 78), fg=theme.MUTED)

            y += 52

        footer = pygame.Rect(60, consts.height - 90, consts.width - 120, 70)
        draw_panel(game.screen, footer)

        if game.is_host:
            msg = "Press S to start (2+ players)"
        else:
            msg = "Waiting for host to start..."

        draw_text(game.screen, game.font, msg, (footer.x + 20, footer.y + 18), theme.TEXT)
        draw_text(game.screen, game.small_font, "ESC  Leave room", (footer.right - 190, footer.y + 26), theme.MUTED)

        if game.error_message:
            draw_hint(game.screen, game.small_font, game.error_message, (consts.width // 2, footer.y - 18))

        pygame.display.flip()

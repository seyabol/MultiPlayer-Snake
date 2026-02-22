import pygame

import consts
from ui.widgets import draw_panel, draw_title, draw_text, draw_hint
from ui import theme


class GameOverScreen:
    def handle_event(self, game, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            game.state = "lobby"
            if game.room_id and game.network_manager:
                game.network_manager.leave_room(game.room_id)
            game.game_manager = None
            game.room_id = None
            game.local_snake = None
            game.network_manager.winner_info = None

    def draw(self, game):
        game.screen.fill(consts.back_color)

        card = pygame.Rect(consts.width // 2 - 320, 190, 640, 380)
        draw_panel(game.screen, card)

        draw_title(game.screen, game.title_font, "Game Over", (consts.width // 2, card.y + 80))

        winner_id = game.network_manager.get_winner_info() if game.network_manager else None
        players = game.network_manager.get_players() if game.network_manager else []

        winner_name = "-"
        for p in players:
            if p.get('id') == winner_id:
                winner_name = p.get('username', '-')
                break

        draw_text(game.screen, game.font, f"Winner: {winner_name}", (card.x + 48, card.y + 170), theme.WARNING)
        draw_text(game.screen, game.font, f"Your score: {game.last_score}", (card.x + 48, card.y + 215), theme.TEXT)

        draw_hint(game.screen, game.small_font, "Press ENTER to return to lobby", (consts.width // 2, card.bottom - 55))

        pygame.display.flip()

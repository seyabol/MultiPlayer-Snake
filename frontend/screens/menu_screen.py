import pygame

import consts
from ui.widgets import draw_panel, draw_title, draw_list_item, draw_hint


class MenuScreen:
    def __init__(self):
        self.selection = 0

    def _options(self, game):
        if game.auth_manager.mode == 'local' and not game.auth_manager.has_any_user():
            return ["Create account", "Quit"]
        return ["Sign in", "Create account", "Quit"]

    def handle_event(self, game, event):
        if event.type != pygame.KEYDOWN:
            return

        options = self._options(game)

        if event.key == pygame.K_UP:
            self.selection = (self.selection - 1) % len(options)
        elif event.key == pygame.K_DOWN:
            self.selection = (self.selection + 1) % len(options)
        elif event.key == pygame.K_RETURN:
            choice = options[self.selection]
            if choice == "Sign in":
                game.state = "login"
            elif choice == "Create account":
                game.state = "register"
            else:
                game.running = False

    def draw(self, game):
        game.screen.fill(consts.back_color)

        draw_title(game.screen, game.title_font, "Multiplayer Snake", (consts.width // 2, 120))

        panel = pygame.Rect(consts.width // 2 - 240, 220, 480, 260)
        draw_panel(game.screen, panel)

        options = self._options(game)
        self.selection = max(0, min(self.selection, len(options) - 1))

        y = panel.y + 50
        for i, opt in enumerate(options):
            item = pygame.Rect(panel.x + 32, y + i * 64, panel.width - 64, 50)
            draw_list_item(game.screen, game.font, opt, "", item, selected=(i == self.selection))

        if game.auth_manager.mode == 'local' and not game.auth_manager.has_any_user():
            draw_hint(game.screen, game.small_font, "Create an account to start playing", (consts.width // 2, panel.bottom + 60))
        else:
            draw_hint(game.screen, game.small_font, "Tip: you can reuse the same account on this machine", (consts.width // 2, panel.bottom + 60))

        if game.error_message:
            msg = game.small_font.render(game.error_message, True, (255, 90, 90))
            game.screen.blit(msg, msg.get_rect(center=(consts.width // 2, panel.bottom + 95)))
        elif game.success_message:
            msg = game.small_font.render(game.success_message, True, (90, 255, 140))
            game.screen.blit(msg, msg.get_rect(center=(consts.width // 2, panel.bottom + 95)))

        pygame.display.flip()

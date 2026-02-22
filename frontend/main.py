import pygame
import argparse

import consts
from game_manager import GameManager
from snake import Snake
from network_manager import NetworkManager
from auth_manager import AuthManager
from ui_manager import UIManager

from screens.menu_screen import MenuScreen
from screens.auth_screen import AuthScreen
from screens.lobby_screen import LobbyScreen
from screens.waiting_screen import WaitingScreen
from screens.game_over_screen import GameOverScreen

from ui.emoji import get_emoji_font
from gameplay.leveling import get_level, move_interval_ms
from ui.widgets import draw_panel, draw_text
from ui import theme


class Game:
    def __init__(self, debug=False):
        pygame.init()
        self.debug = debug

        flags = pygame.SCALED
        self.screen = pygame.display.set_mode((consts.width, consts.height), flags)
        pygame.display.set_caption("Multiplayer Snake")

        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.Font(None, 62)
        self.font = pygame.font.Font(None, 34)
        self.small_font = pygame.font.Font(None, 24)
        self.emoji_font = get_emoji_font(int(consts.cell_size * 0.72))

        self.auth_manager = AuthManager()
        self.network_manager = None

        self.ui_manager = UIManager(self.screen, self.title_font, self.font, self.small_font)

        self.menu_screen = MenuScreen()
        self.auth_screen = AuthScreen()
        self.lobby_screen = LobbyScreen()
        self.waiting_screen = WaitingScreen()
        self.game_over_screen = GameOverScreen()

        self.state = "menu"
        self.running = True

        self.game_manager = None
        self.local_snake = None
        self.room_id = None
        self.is_host = False
        self.players = []
        self.should_start_game = False

        self.error_message = ""
        self.success_message = ""

        self.last_score = 0

        self._last_step_ms = 0

        if self.auth_manager.mode == 'local' and not self.auth_manager.has_any_user() and not self.auth_manager.is_authenticated():
            self.state = 'register'

    def init_network(self):
        if self.network_manager:
            return

        self.network_manager = NetworkManager(consts.server_url)
        self.network_manager.on_game_start = self.on_network_game_started

    def on_network_game_started(self):
        self.should_start_game = True

    def authenticate_user(self):
        if not self.auth_manager.current_user:
            return False

        self.init_network()

        token = self.auth_manager.get_id_token()
        user_id = self.auth_manager.get_user_id()
        username = self.auth_manager.current_user.get('username', 'Player')

        if self.network_manager.authenticate(token, username, user_id=user_id):
            self.state = "lobby"
            self.network_manager.refresh_rooms()
            return True

        self.error_message = self.network_manager.last_error or "Network authentication failed"
        return False

    def create_room(self):
        if not self.network_manager:
            return

        self.error_message = ""
        self.success_message = ""

        room_id = self.network_manager.create_room({
            'table_size': consts.table_size,
            'cell_size': consts.cell_size,
        })

        if room_id:
            self.room_id = room_id
            self.state = "waiting"
            self.success_message = "Room created"
            self.is_host = True
        else:
            self.error_message = self.network_manager.last_error or "Failed to create room"

    def join_room(self, room_id):
        if not self.network_manager:
            return

        self.error_message = ""
        self.success_message = ""

        if self.network_manager.join_room(room_id):
            self.room_id = room_id
            self.state = "waiting"
            self.success_message = "Joined room"
        else:
            self.error_message = self.network_manager.last_error or "Failed to join room"

    def start_game(self):
        sx, sy = consts.grid_origin()

        self.game_manager = GameManager(
            consts.table_size,
            self.screen,
            sx,
            sy,
            consts.block_cells,
            self.network_manager,
            emoji_font=self.emoji_font,
        )

        snake_config = consts.snakes[0] if self.is_host else consts.snakes[1]

        self.local_snake = Snake(
            consts.DEFAULT_CONTROLS,
            self.game_manager,
            (snake_config['sx'], snake_config['sy']),
            tuple(snake_config['color']),
            snake_config['direction'],
            is_local=True,
        )

        self.game_manager.add_local_snake(self.local_snake)
        self.state = "playing"
        self._last_step_ms = pygame.time.get_ticks()

    def _draw_play_hud(self):
        if not self.game_manager:
            return

        hud = self.game_manager.hud_rect()
        pygame.draw.rect(self.screen, consts.back_color, hud)

        panel = pygame.Rect(40, 20, consts.width - 80, hud.height - 30)
        draw_panel(self.screen, panel)

        score = self.local_snake.score if self.local_snake else 0
        lvl = get_level(score)
        speed = move_interval_ms(score)

        food = self.game_manager.fruit or {}
        food_label = f"Food: {food.get('emoji', '')} +{food.get('value', '')}" if food else ""

        left = f"Room: {self.room_id or '-'}"
        mid = f"Score: {score}   Level: {lvl}"
        right = f"Speed: {speed}ms"

        draw_text(self.screen, self.font, left, (panel.x + 18, panel.y + 18), theme.MUTED)
        draw_text(self.screen, self.font, mid, (panel.centerx - self.font.size(mid)[0] // 2, panel.y + 18), theme.TEXT)
        draw_text(self.screen, self.font, right, (panel.right - 18 - self.font.size(right)[0], panel.y + 18), theme.WARNING)

        help_txt = "Arrows / WASD to move • ESC to leave"
        draw_text(self.screen, self.small_font, help_txt, (panel.x + 18, panel.y + 50), theme.MUTED)

        if food_label:
            draw_text(self.screen, self.small_font, food_label, (panel.right - 18 - self.small_font.size(food_label)[0], panel.y + 50), theme.MUTED)

        pygame.display.update(hud)

    def update_game(self):
        if self.state != "playing" or not self.game_manager:
            return

        now = pygame.time.get_ticks()
        score = self.local_snake.score if self.local_snake else self.last_score
        self.last_score = score
        interval = move_interval_ms(score)

        game_state = self.network_manager.get_game_state() if self.network_manager else None
        if game_state and (now - self._last_step_ms) > 15:
            self.game_manager.update_from_network(game_state)

        if now - self._last_step_ms < interval:
            self._draw_play_hud()
            return

        self._last_step_ms = now

        self.game_manager.update()

        if self.local_snake and self.local_snake.alive:
            snake_data = {
                'cells': self.local_snake.cells,
                'direction': self.local_snake.direction,
                'alive': self.local_snake.alive,
            }
            self.network_manager.send_game_update(self.room_id, snake_data, self.local_snake.score)

        if self.local_snake and not self.local_snake.alive:
            self.network_manager.send_player_died(self.room_id)
            self.local_snake = None

        if self.network_manager.get_winner_info() is not None:
            self.state = "game_over"

        self._draw_play_hud()

    def sync_waiting_state(self):
        if not self.network_manager:
            return

        self.players = self.network_manager.get_players() or []

        host_id = self.network_manager.get_host_id()
        my_id = self.auth_manager.get_user_id()
        self.is_host = bool(host_id and my_id and host_id == my_id)

    def run(self):
        if self.auth_manager.is_authenticated():
            self.authenticate_user()

        while self.running:
            self.clock.tick(60)

            if self.should_start_game and self.state == "waiting":
                self.should_start_game = False
                self.start_game()

            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                if self.state == "menu":
                    self.menu_screen.handle_event(self, event)

                elif self.state in ("login", "register"):
                    pass

                elif self.state == "lobby":
                    self.lobby_screen.handle_event(self, event)

                elif self.state == "waiting":
                    self.waiting_screen.handle_event(self, event)

                elif self.state == "playing":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = 'lobby'
                            if self.room_id and self.network_manager:
                                self.network_manager.leave_room(self.room_id)
                                self.room_id = None
                            self.game_manager = None
                            self.local_snake = None
                            break
                        self.game_manager.handle(event.key)

                elif self.state == "game_over":
                    self.game_over_screen.handle_event(self, event)

            if self.state == "playing":
                self.update_game()

            if self.state == "lobby":
                self.lobby_screen.tick(self)

            if self.state == "waiting":
                self.sync_waiting_state()

            if self.state == "menu":
                self.menu_screen.draw(self)

            elif self.state in ("login", "register"):
                result = self.auth_screen.handle_events(self, self.state, self.auth_manager, events)
                if result == 'lobby':
                    self.authenticate_user()
                elif result == 'menu':
                    self.state = 'menu'
                self.auth_screen.draw(self, self.state, self.auth_manager)

            elif self.state == "lobby":
                self.lobby_screen.draw(self)

            elif self.state == "waiting":
                self.waiting_screen.draw(self)

            elif self.state == "game_over":
                self.game_over_screen.draw(self)

            elif self.state == "stats":
                uid = self.auth_manager.current_user['uid']
                self.ui_manager.draw_stats(uid, consts.server_url, events)
                if self.ui_manager.back_requested:
                    self.state = "lobby"

            elif self.state == "leaderboard":
                self.ui_manager.draw_leaderboard(consts.server_url, events)
                if self.ui_manager.back_requested:
                    self.state = "lobby"

        if self.network_manager:
            if self.room_id:
                self.network_manager.leave_room(self.room_id)
            self.network_manager.disconnect()

        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description='Multiplayer Snake Game')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    Game(debug=args.debug).run()


if __name__ == '__main__':
    main()

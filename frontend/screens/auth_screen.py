import pygame

import consts
from ui.widgets import draw_panel, draw_title, draw_text, draw_hint
from ui import theme


class AuthScreen:
    def __init__(self):
        self.reset()

    def reset(self):
        self.field_index = 0
        self.values = {'email': '', 'username': '', 'password': ''}
        self.error = ''
        self._blink = 0

    def _fields_for(self, mode):
        if mode == 'login':
            return ['email', 'password']
        return ['email', 'username', 'password']

    def _label(self, key):
        return {'email': 'Email', 'username': 'Username', 'password': 'Password'}.get(key, key)

    def _validate(self, mode):
        email = self.values['email'].strip()
        password = self.values['password']
        username = self.values['username'].strip()

        if '@' not in email or '.' not in email:
            return False, 'Enter a valid email'

        if mode == 'register' and not username:
            return False, 'Pick a username'

        if len(password) < 6:
            return False, 'Password must be at least 6 characters'

        return True, ''

    def handle_events(self, game, mode, auth_manager, events):
        require_first = (mode == 'register' and auth_manager.mode == 'local' and not auth_manager.has_any_user())
        fields = self._fields_for(mode)

        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                if require_first:
                    game.running = False
                    return None
                self.reset()
                return 'menu'

            if event.key == pygame.K_TAB:
                self.field_index = (self.field_index + 1) % len(fields)
                continue

            if event.key == pygame.K_RETURN:
                if self.field_index < len(fields) - 1:
                    self.field_index += 1
                    continue

                ok, msg = self._validate(mode)
                if not ok:
                    self.error = msg
                    continue

                email = self.values['email'].strip()
                password = self.values['password']

                if mode == 'login':
                    success, message = auth_manager.login(email, password)
                else:
                    username = self.values['username'].strip()
                    success, message = auth_manager.register(email, password, username)

                if success:
                    self.reset()
                    game.success_message = message
                    game.error_message = ''
                    return 'lobby'

                self.error = message
                continue

            if event.key == pygame.K_BACKSPACE:
                k = fields[self.field_index]
                self.values[k] = self.values[k][:-1]
                continue

            if event.unicode:
                k = fields[self.field_index]
                if len(self.values[k]) < 40:
                    self.values[k] += event.unicode

        return None

    def draw(self, game, mode, auth_manager):
        game.screen.fill(consts.back_color)

        title = 'Sign in' if mode == 'login' else 'Create account'
        draw_title(game.screen, game.title_font, title, (consts.width // 2, 90))

        panel = pygame.Rect(consts.width // 2 - 320, 170, 640, 430)
        draw_panel(game.screen, panel)

        fields = self._fields_for(mode)

        y = panel.y + 55
        for i, key in enumerate(fields):
            label = self._label(key)
            value = self.values[key]
            shown = value if key != 'password' else ('•' * len(value))

            line = pygame.Rect(panel.x + 38, y, panel.width - 76, 62)
            active = i == self.field_index

            bg = (45, 45, 62) if not active else (55, 60, 85)
            border = theme.PANEL_BORDER if not active else theme.PRIMARY

            pygame.draw.rect(game.screen, bg, line, border_radius=12)
            pygame.draw.rect(game.screen, border, line, 2, border_radius=12)

            draw_text(game.screen, game.small_font, label, (line.x + 14, line.y + 10), theme.MUTED)
            draw_text(game.screen, game.font, shown or '', (line.x + 14, line.y + 30), theme.TEXT)

            if active and (pygame.time.get_ticks() // 400) % 2 == 0:
                cursor_x = line.x + 14 + game.font.size(shown)[0] + 2
                cursor_y1 = line.y + 32
                cursor_y2 = line.y + 52
                pygame.draw.line(game.screen, theme.TEXT, (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)

            y += 90

        hint = 'ENTER to continue • TAB to switch fields'
        if mode == 'register' and auth_manager.mode == 'local' and not auth_manager.has_any_user():
            hint = 'Create an account to start playing • ESC quits'
        else:
            hint += ' • ESC back'

        draw_hint(game.screen, game.small_font, hint, (consts.width // 2, panel.bottom + 40))

        if self.error:
            draw_text(game.screen, game.small_font, self.error, (panel.centerx - game.small_font.size(self.error)[0] // 2, panel.bottom + 65), theme.ERROR)

        pygame.display.flip()

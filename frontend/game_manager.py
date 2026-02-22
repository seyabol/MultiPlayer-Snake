import random
import pygame

import consts
from cell import Cell
from gameplay.fruit import pick_food


class GameManager:
    def __init__(self, size, screen, sx, sy, block_cells, network_manager=None, emoji_font=None):
        self.screen = screen
        self.size = size
        self.sx = sx
        self.sy = sy
        self.network_manager = network_manager

        self.cells = []
        self.snakes = []
        self.remote_snakes = {}
        self.remote_occupied = set()
        self._remote_drawn = set()

        self.local_snake = None
        self.killed_cells = []
        self.game_over = False

        self.turn = 0

        self.fruit = None
        self.emoji_font = emoji_font

        for i in range(self.size):
            col = []
            for j in range(self.size):
                col.append(Cell(screen, sx + i * consts.cell_size, sy + j * consts.cell_size))
            self.cells.append(col)

        for cell in block_cells:
            self.get_cell(tuple(cell)).set_color(consts.block_color)

        self.spawn_fruit()

    def add_local_snake(self, snake):
        self.local_snake = snake
        self.snakes.append(snake)

    def get_cell(self, pos):
        try:
            return self.cells[pos[0]][pos[1]]
        except Exception:
            return None

    def is_block(self, pos):
        return list(pos) in consts.block_cells

    def is_remote_cell(self, pos):
        return pos in self.remote_occupied

    def is_occupied(self, pos):
        if self.is_block(pos):
            return True

        for s in self.snakes:
            if pos in s.cells:
                return True

        if pos in self.remote_occupied:
            return True

        return False

    def spawn_fruit(self):
        empties = []
        for x in range(self.size):
            for y in range(self.size):
                p = (x, y)
                if self.is_occupied(p):
                    continue
                empties.append(p)

        if not empties:
            self.fruit = None
            return

        pos = random.choice(empties)
        food = pick_food()
        self.fruit = {'pos': pos, **food}

        cell = self.get_cell(pos)
        if cell:
            cell.set_color(consts.fruit_color)

        self.draw_fruit()

    def draw_fruit(self):
        if not self.fruit:
            return

        pos = self.fruit['pos']
        cell = self.get_cell(pos)
        if not cell:
            return

        cell.set_color(consts.fruit_color)

        if not self.emoji_font:
            return

        emoji = self.fruit.get('emoji', '●')
        s = self.emoji_font.render(emoji, True, (255, 255, 255))
        x = cell.sx + (cell.size - s.get_width()) // 2
        y = cell.sy + (cell.size - s.get_height()) // 2 - 1
        self.screen.blit(s, (x, y))
        pygame.display.update(pygame.Rect(cell.sx, cell.sy, cell.size, cell.size))

    def is_fruit_at(self, pos):
        return bool(self.fruit and self.fruit.get('pos') == pos)

    def consume_fruit(self):
        if not self.fruit:
            return 0

        pos = self.fruit['pos']
        value = int(self.fruit.get('value', 10))

        cell = self.get_cell(pos)
        if cell:
            cell.set_color(consts.back_color)

        self.fruit = None
        self.spawn_fruit()
        return value

    def kill2(self, snake):
        for p in snake.cells:
            self.killed_cells.append(p)

    def kill(self, snake):
        if snake in self.snakes:
            self.snakes.remove(snake)

        if snake == self.local_snake:
            self.game_over = True

    def update_from_network(self, game_state):
        if not game_state:
            return

        snakes_data = dict(game_state.get('snakes', []))

        prev_drawn = set(self._remote_drawn)
        self.remote_snakes = {}
        self.remote_occupied = set()
        new_drawn = set()

        local_player_id = None
        if self.local_snake and self.network_manager:
            local_player_id = self.network_manager.get_player_data().get('userId')

        for player_id, snake_data in snakes_data.items():
            if player_id == local_player_id:
                continue

            if not snake_data.get('alive', True):
                continue

            cells = snake_data.get('cells', [])
            self.remote_snakes[player_id] = snake_data

            for c in cells:
                if isinstance(c, (list, tuple)) and len(c) == 2:
                    pos = (c[0], c[1])
                    self.remote_occupied.add(pos)
                    new_drawn.add(pos)

        players = game_state.get('players', [])
        colors = {p.get('id'): tuple(p.get('color', [255, 255, 255])) for p in players}

        for player_id, snake_data in self.remote_snakes.items():
            color = colors.get(player_id, (255, 255, 255))
            for c in snake_data.get('cells', []):
                if isinstance(c, (list, tuple)) and len(c) == 2:
                    self.get_cell((c[0], c[1])).set_color(color)

        for pos in prev_drawn - new_drawn:
            if self.is_block(pos):
                continue
            if self.local_snake and pos in self.local_snake.cells:
                continue
            if self.is_fruit_at(pos):
                continue
            cell = self.get_cell(pos)
            if cell:
                cell.set_color(consts.back_color)

        self._remote_drawn = new_drawn

        self.draw_fruit()

    def update(self):
        if self.game_over:
            return

        if self.local_snake and self.local_snake.alive:
            self.local_snake.next_move()

        self.turn += 1
        self.draw_fruit()

    def handle(self, key_code):
        if self.local_snake:
            self.local_snake.handle(key_code)

    def is_game_over(self):
        return self.game_over

    def hud_rect(self):
        return pygame.Rect(0, 0, consts.width, self.sy - 20)

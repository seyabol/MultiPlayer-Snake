import pygame
import consts


class Snake:
    dx = {'UP': 0, 'DOWN': 0, 'LEFT': -1, 'RIGHT': 1}
    dy = {'UP': -1, 'DOWN': 1, 'LEFT': 0, 'RIGHT': 0}

    def __init__(self, keys, game, pos, color, direction, is_local=False):
        self.length = 2
        self.keys = keys
        self.cells = [pos]
        self.game = game
        self.color = color
        self.direction = direction
        self.is_local = is_local
        self.alive = True
        self.score = 0

        game.get_cell(pos).set_color(color)

    def get_head(self):
        return self.cells[-1]

    @staticmethod
    def wrap(m, n, table_size):
        if m >= table_size:
            m = 0
        if m < 0:
            m = table_size - 1
        if n >= table_size:
            n = 0
        if n < 0:
            n = table_size - 1
        return m, n

    def draw_snake(self, cells):
        for pos in cells:
            cell = self.game.get_cell(pos)
            if cell:
                cell.set_color(self.color)

    def next_move(self):
        if not self.alive:
            return

        cur = self.get_head()

        xx = Snake.dx[self.direction]
        yy = Snake.dy[self.direction]

        new_head = (cur[0] + xx, cur[1] + yy)
        new_head = Snake.wrap(new_head[0], new_head[1], consts.table_size)

        if self.check_collision(new_head):
            self.die()
            return

        self.cells.append(new_head)

        ate = self.game.is_fruit_at(new_head)
        if ate:
            self.length += 1
            self.score += self.game.consume_fruit()

        if not ate and len(self.cells) > self.length:
            tail = tuple(self.cells.pop(0))
            self.game.get_cell(tail).set_color(consts.back_color)

        self.draw_snake(self.cells)
        self.game.draw_fruit()

    def check_collision(self, pos):
        if pos in self.cells:
            return True

        if list(pos) in consts.block_cells:
            return True

        if pos in self.game.killed_cells:
            return True

        if self.game.is_remote_cell(pos):
            return True

        for snake in self.game.snakes:
            if snake != self and snake.alive and pos in snake.cells:
                return True

        return False

    def die(self):
        self.alive = False
        self.game.kill(self)
        self.game.kill2(self)

        for pos in self.cells:
            cell = self.game.get_cell(pos)
            if cell:
                dead_color = [c // 2 for c in self.color]
                cell.set_color(dead_color)

    def handle(self, key_code):
        if not self.alive:
            return

        key = pygame.key.name(key_code)
        if key not in self.keys:
            return

        new_direction = self.keys[key]

        if new_direction == 'UP' and self.direction != 'DOWN':
            self.direction = 'UP'
        elif new_direction == 'DOWN' and self.direction != 'UP':
            self.direction = 'DOWN'
        elif new_direction == 'LEFT' and self.direction != 'RIGHT':
            self.direction = 'LEFT'
        elif new_direction == 'RIGHT' and self.direction != 'LEFT':
            self.direction = 'RIGHT'

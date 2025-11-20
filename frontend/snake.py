import consts

class Snake:
    dx = {'UP': 0, 'DOWN': 0, 'LEFT': -1, 'RIGHT': 1}
    dy = {'UP': -1, 'DOWN': 1, 'LEFT': 0, 'RIGHT': 0}
    
    def __init__(self, keys, game, pos, color, direction, is_local=False):
        self.length = 1
        self.keys = keys
        self.cells = [pos]
        self.game = game
        self.color = color
        self.direction = direction
        self.is_local = is_local
        self.alive = True
        self.score = 0
        
        # Set initial position
        game.get_cell(pos).set_color(color)
        
    def get_head(self):
        """Get head position"""
        return self.cells[-1]
        
    def val(self, x):
        """Wrap value within game boundaries"""
        if x < 0:
            x += self.game.size
        if x >= self.game.size:
            x -= self.game.size
        return x
        
    @staticmethod
    def check_table(m, n, table_size):
        """Check and wrap coordinates"""
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
        """Draw snake on grid"""
        for pos in cells:
            cell = self.game.get_cell(pos)
            if cell:
                cell.set_color(self.color)
                
    def next_move(self):
        """Calculate and execute next move"""
        if not self.alive:
            return
            
        cur = self.get_head()
        self.xx = Snake.dx[self.direction]
        self.yy = Snake.dy[self.direction]
        
        new_head = (cur[0] + self.xx, cur[1] + self.yy)
        new_head = Snake.check_table(new_head[0], new_head[1], consts.table_size)
        
        # Check collisions
        if self.check_collision(new_head):
            self.die()
            return
            
        # Move snake
        self.cells.append(new_head)
        
        # Check if ate fruit
        if self.game.get_cell(new_head).color == consts.fruit_color:
            self.length += 1
            self.score += 10
            # Fruit will be cleared by next move, no need to remove tail
        else:
            # Remove tail if didn't eat fruit
            if len(self.cells) > self.length:
                tail = tuple(self.cells.pop(0))
                self.game.get_cell(tail).set_color(consts.back_color)
                
        # Draw updated snake
        self.draw_snake(self.cells)
        
    def check_collision(self, pos):
        """Check if position causes collision"""
        # Check self collision
        if pos in self.cells:
            return True
            
        # Check block collision
        if list(pos) in consts.block_cells:
            return True
            
        # Check collision with dead snake cells
        if pos in self.game.killed_cells:
            return True
            
        # Check collision with other snakes
        for snake in self.game.snakes:
            if snake != self and snake.alive:
                if pos in snake.cells:
                    return True
                    
        return False
        
    def die(self):
        """Handle snake death"""
        self.alive = False
        self.game.kill(self)
        self.game.kill2(self)
        
        # Color dead snake cells differently
        for pos in self.cells:
            cell = self.game.get_cell(pos)
            if cell:
                # Darken the color to show it's dead
                dead_color = [c // 2 for c in self.color]
                cell.set_color(dead_color)
                
    def handle(self, keys):
        """Handle keyboard input for direction changes"""
        if not self.alive:
            return
            
        for key in keys:
            if key in self.keys:
                new_direction = self.keys[key]
                
                # Prevent 180-degree turns
                if new_direction == 'UP' and self.direction != 'DOWN':
                    self.direction = 'UP'
                    break
                elif new_direction == 'DOWN' and self.direction != 'UP':
                    self.direction = 'DOWN'
                    break
                elif new_direction == 'LEFT' and self.direction != 'RIGHT':
                    self.direction = 'LEFT'
                    break
                elif new_direction == 'RIGHT' and self.direction != 'LEFT':
                    self.direction = 'RIGHT'
                    break
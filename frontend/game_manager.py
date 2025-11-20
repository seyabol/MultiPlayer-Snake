import consts
from cell import Cell
import random

class GameManager:
    def __init__(self, size, screen, sx, sy, block_cells, network_manager=None):
        self.killed_cells = []
        self.screen = screen
        self.size = size
        self.cells = []
        self.sx = sx
        self.sy = sy
        self.snakes = list()
        self.remote_snakes = {}  # Store remote player snakes
        self.local_snake = None
        self.turn = 0
        self.network_manager = network_manager
        self.game_over = False
        
        # Initialize grid
        for i in range(self.size):
            tmp = []
            for j in range(self.size):
                tmp.append(Cell(screen, sx + i * consts.cell_size, sy + j * consts.cell_size))
            self.cells.append(tmp)
            
        # Setup blocks
        for cell in block_cells:
            self.get_cell(cell).set_color(consts.block_color)
       
    def add_snake(self, snake):
        """Add a snake to the game"""
        self.snakes.append(snake)
        
    def add_local_snake(self, snake):
        """Set the local player's snake"""
        self.local_snake = snake
        self.snakes.append(snake)
        
    def get_cell(self, pos):
        """Get cell at position"""
        try:
            return self.cells[pos[0]][pos[1]]
        except:
            return None
            
    def kill2(self, k):
        """Mark cells where snake died"""
        for p in k.cells:
            self.killed_cells.append(p)
            
    def kill(self, killed_snake):
        """Remove snake from game"""
        if killed_snake in self.snakes:
            self.snakes.remove(killed_snake)
            
        # Check if local player died
        if killed_snake == self.local_snake:
            self.game_over = True
            print("Local player died!")
            
    def get_next_fruit_pos(self):
        """Calculate optimal fruit position (furthest from all snakes)"""
        ret = -1, -1
        mx = -100
        
        for i in range(0, self.size):
            for j in range(0, self.size):
                # Skip if cell is occupied
                cell_color = self.get_cell((i, j)).color
                if cell_color != consts.back_color:
                    continue
                    
                mn = 100000000
                for x in range(0, self.size):
                    for y in range(0, self.size):
                        if self.get_cell((x, y)).color != consts.back_color:
                            mn = min(mn, int(abs(x-i) + abs(y-j)))
                            
                if mn > mx:
                    mx = mn
                    ret = i, j
                    
        return ret
        
    def spawn_fruit(self):
        """Spawn a new fruit"""
        coordinate = self.get_next_fruit_pos()
        if coordinate != (-1, -1):
            self.get_cell(coordinate).set_color(consts.fruit_color)
            print(f"Spawned fruit at {coordinate}")
            
    def update_from_network(self, game_state):
        """Update game state from network"""
        if not game_state:
            return
            
        # Update remote snakes
        snakes_data = dict(game_state.get('snakes', []))
        
        # Clear old remote snake visuals
        for player_id, old_snake_data in self.remote_snakes.items():
            if player_id not in snakes_data:
                # This player left, clear their cells
                old_cells = old_snake_data.get('cells', [])
                for cell in old_cells:
                    if isinstance(cell, (list, tuple)) and len(cell) == 2:
                        self.get_cell(tuple(cell)).set_color(consts.back_color)
        
        for player_id, snake_data in snakes_data.items():
            # Skip local player
            if self.local_snake:
                local_player_id = self.network_manager.get_player_data().get('userId') if self.network_manager else None
                if player_id == local_player_id:
                    continue
            
            # Update remote snake
            self.remote_snakes[player_id] = snake_data
                
        # Draw remote snakes
        for player_id, snake_data in self.remote_snakes.items():
            cells = snake_data.get('cells', [])
            alive = snake_data.get('alive', True)
            
            if alive:
                # Get color from player data
                players = game_state.get('players', [])
                color = consts.back_color
                for player in players:
                    if player.get('id') == player_id:
                        color = tuple(player.get('color', [255, 255, 255]))
                        break
                
                # Draw snake cells
                for cell in cells:
                    if isinstance(cell, (list, tuple)) and len(cell) == 2:
                        self.get_cell(tuple(cell)).set_color(color)
                        
    def update(self):
        """Update game state"""
        if self.game_over:
            return
            
        # Update local snake
        if self.local_snake and self.local_snake.alive:
            self.local_snake.next_move()
            
        # Spawn fruit periodically
        self.turn += 1
        if self.turn % 10 == 0:
            self.spawn_fruit()
            
    def handle(self, keys):
        """Handle player input"""
        if self.local_snake:
            self.local_snake.handle(keys)
            
    def is_game_over(self):
        """Check if game is over"""
        return self.game_over
        
    def draw(self):
        """Draw game state"""
        # Draw HUD with score
        if self.local_snake:
            import pygame
            font = pygame.font.Font(None, 24)
            score_text = font.render(f"Score: {self.local_snake.score}", True, (255, 255, 255))
            self.screen.blit(score_text, (10, 10))
            pygame.display.update(pygame.Rect(0, 0, 200, 40))

            
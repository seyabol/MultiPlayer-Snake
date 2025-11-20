import pygame
import sys
import argparse
from game_manager import GameManager
from snake import Snake
from network_manager import NetworkManager
from auth_manager import AuthManager
from ui_manager import UIManager
import consts

class Game:
    def __init__(self, debug=False):
        pygame.init()
        self.debug = debug
        self.screen = pygame.display.set_mode((consts.width, consts.height))
        pygame.display.set_caption("Multiplayer Snake Game")
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Managers
        self.auth_manager = AuthManager()
        self.network_manager = None
        self.ui_manager = UIManager(self.screen, self.font, self.small_font)
        
        # Game state
        self.state = "menu"  # menu, auth, lobby, playing, game_over
        self.game_manager = None
        self.local_snake = None
        self.room_id = None
        self.is_host = False
        self.players = []
        self.should_start_game = False  # Flag for game start
        
        # UI state
        self.menu_selection = 0
        self.menu_options = ["Login", "Register", "Quit"]
        self.error_message = ""
        self.success_message = ""
        
    def init_network(self):
        """Initialize network manager with callback"""
        if not self.network_manager:
            self.network_manager = NetworkManager(consts.server_url)
            # Set up game start callback
            self.network_manager.on_game_start = self.on_network_game_started
            
    def on_network_game_started(self):
        """Callback when game starts from network"""
        self.should_start_game = True
        
    def authenticate_user(self):
        """Handle user authentication"""
        if self.auth_manager.current_user:
            # Initialize network after auth
            self.init_network()
            
            # Already authenticated
            token = self.auth_manager.get_id_token()
            success = self.network_manager.authenticate(
                token, 
                self.auth_manager.current_user['username']
            )
            if success:
                self.state = "lobby"
                return True
            else:
                self.error_message = "Network authentication failed"
        return False
        
    def create_room(self):
        """Create a new game room"""
        self.room_id = self.network_manager.create_room({
            'table_size': consts.table_size,
            'cell_size': consts.cell_size
        })
        if self.room_id:
            self.is_host = True
            self.state = "waiting"
            self.success_message = f"Room created: {self.room_id}"
        else:
            self.error_message = "Failed to create room"
            
    def join_room(self, room_id):
        """Join an existing game room"""
        success = self.network_manager.join_room(room_id)
        if success:
            self.room_id = room_id
            self.is_host = False
            self.state = "waiting"
            self.success_message = f"Joined room: {room_id}"
        else:
            self.error_message = "Failed to join room"
            
    def start_game(self):
        """Initialize game when starting"""
        print("Starting local game...")
        
        self.game_manager = GameManager(
            consts.table_size, 
            self.screen, 
            consts.sx,
            consts.sy, 
            consts.block_cells,
            self.network_manager
        )
        
        # Create local snake
        player_data = self.network_manager.get_player_data()
        if player_data:
            # Use different starting positions for host vs joiner
            snake_config = consts.snakes[0] if self.is_host else consts.snakes[1]
            self.local_snake = Snake(
                snake_config['keys'], 
                self.game_manager,
                (snake_config['sx'], snake_config['sy']),
                snake_config['color'],
                snake_config['direction'],
                is_local=True
            )
            self.game_manager.add_local_snake(self.local_snake)
            
            # Spawn initial fruit
            self.game_manager.spawn_fruit()
        
        self.state = "playing"
        print("Game started!")
        
    def handle_menu_input(self, event):
        """Handle menu navigation"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu_selection = (self.menu_selection - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN:
                self.menu_selection = (self.menu_selection + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN:
                option = self.menu_options[self.menu_selection]
                if option == "Login":
                    self.state = "login"
                elif option == "Register":
                    self.state = "register"
                elif option == "Quit":
                    return False
        return True
        
    def handle_lobby_input(self, event):
        """Handle lobby navigation"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:  # Create room
                self.create_room()
            elif event.key == pygame.K_j:  # Join room
                self.state = "join_input"
            elif event.key == pygame.K_s:  # View stats
                self.state = "stats"
            elif event.key == pygame.K_l:  # View leaderboard
                self.state = "leaderboard"
            elif event.key == pygame.K_ESCAPE:
                self.state = "menu"
                
    def handle_waiting_input(self, event):
        """Handle waiting room input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and self.is_host:  # Start game
                if len(self.players) >= 2:
                    self.network_manager.start_game(self.room_id)
                    self.start_game()  # Host starts immediately
                else:
                    self.error_message = "Need at least 2 players"
            elif event.key == pygame.K_ESCAPE:
                if self.room_id:
                    self.network_manager.leave_room(self.room_id)
                self.state = "lobby"
                
    def update_game(self):
        """Update game state"""
        if self.state == "playing" and self.game_manager:
            # Get network updates
            game_state = self.network_manager.get_game_state()
            if game_state:
                self.game_manager.update_from_network(game_state)
            
            # Update local game
            self.game_manager.update()
            
            # Send updates to server
            if self.local_snake and self.local_snake.alive:
                snake_data = {
                    'cells': self.local_snake.cells,
                    'direction': self.local_snake.direction,
                    'alive': self.local_snake.alive
                }
                self.network_manager.send_game_update(
                    self.room_id,
                    snake_data,
                    self.local_snake.score
                )
            
            # Check if local player died
            if self.local_snake and not self.local_snake.alive:
                self.network_manager.send_player_died(self.room_id)
                self.local_snake = None  # Prevent multiple death messages
            
            # Check for game over from network
            winner = self.network_manager.get_winner_info()
            if winner is not None:
                self.state = "game_over"
    
    def draw_menu(self):
        """Draw main menu"""
        self.screen.fill(consts.back_color)
        
        # Title
        title = self.font.render("Multiplayer Snake", True, (255, 255, 255))
        title_rect = title.get_rect(center=(consts.width // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Menu options
        for i, option in enumerate(self.menu_options):
            color = (255, 255, 0) if i == self.menu_selection else (255, 255, 255)
            text = self.small_font.render(option, True, color)
            text_rect = text.get_rect(center=(consts.width // 2, 250 + i * 50))
            self.screen.blit(text, text_rect)
        
        # Messages
        if self.error_message:
            error_text = self.small_font.render(self.error_message, True, (255, 0, 0))
            error_rect = error_text.get_rect(center=(consts.width // 2, 450))
            self.screen.blit(error_text, error_rect)
            
        if self.success_message:
            success_text = self.small_font.render(self.success_message, True, (0, 255, 0))
            success_rect = success_text.get_rect(center=(consts.width // 2, 450))
            self.screen.blit(success_text, success_rect)
        
        pygame.display.flip()
        
    def draw_lobby(self):
        """Draw lobby screen"""
        self.screen.fill(consts.back_color)
        
        # Welcome message
        username = self.auth_manager.current_user.get('username', 'Player')
        welcome = self.font.render(f"Welcome, {username}!", True, (255, 255, 255))
        welcome_rect = welcome.get_rect(center=(consts.width // 2, 50))
        self.screen.blit(welcome, welcome_rect)
        
        # Options
        options = [
            "C - Create Room",
            "J - Join Room",
            "S - View Stats",
            "L - Leaderboard",
            "ESC - Back to Menu"
        ]
        
        for i, option in enumerate(options):
            text = self.small_font.render(option, True, (255, 255, 255))
            text_rect = text.get_rect(center=(consts.width // 2, 150 + i * 40))
            self.screen.blit(text, text_rect)
        
        # Active games
        if self.network_manager:
            active_games = self.network_manager.get_active_games()
            if active_games:
                games_title = self.small_font.render("Active Games:", True, (255, 255, 0))
                self.screen.blit(games_title, (50, 400))
                
                for i, game in enumerate(active_games[:5]):
                    game_text = self.small_font.render(
                        f"{game['id']}: {game['playerCount']} players",
                        True, (200, 200, 200)
                    )
                    self.screen.blit(game_text, (50, 430 + i * 30))
        
        pygame.display.flip()
        
    def draw_waiting_room(self):
        """Draw waiting room"""
        self.screen.fill(consts.back_color)
        
        # Room info
        room_text = self.font.render(f"Room: {self.room_id}", True, (255, 255, 255))
        room_rect = room_text.get_rect(center=(consts.width // 2, 50))
        self.screen.blit(room_text, room_rect)
        
        # Player list
        players_title = self.small_font.render("Players:", True, (255, 255, 0))
        self.screen.blit(players_title, (100, 120))
        
        for i, player in enumerate(self.players):
            player_text = self.small_font.render(
                f"{i+1}. {player.get('username', 'Player')}",
                True, (200, 200, 200)
            )
            self.screen.blit(player_text, (100, 150 + i * 30))
        
        # Instructions
        if self.is_host:
            instruction = "Press S to start game (need 2+ players)"
        else:
            instruction = "Waiting for host to start..."
            
        inst_text = self.small_font.render(instruction, True, (255, 255, 255))
        inst_rect = inst_text.get_rect(center=(consts.width // 2, 400))
        self.screen.blit(inst_text, inst_rect)
        
        back_text = self.small_font.render("ESC - Leave Room", True, (150, 150, 150))
        back_rect = back_text.get_rect(center=(consts.width // 2, 450))
        self.screen.blit(back_text, back_rect)
        
        pygame.display.flip()
        
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(consts.back_color)
        
        # Game over text
        game_over = self.font.render("Game Over!", True, (255, 255, 255))
        game_over_rect = game_over.get_rect(center=(consts.width // 2, 200))
        self.screen.blit(game_over, game_over_rect)
        
        # Winner info (winner_info is just the winner's user ID string)
        winner_id = self.network_manager.get_winner_info()
        if winner_id:
            # Find winner's username from players list
            winner_username = "Unknown"
            for player in self.players:
                if player.get('id') == winner_id:
                    winner_username = player.get('username', 'Unknown')
                    break
            
            winner_text = self.small_font.render(
                f"Winner: {winner_username}",
                True, (255, 255, 0)
            )
            winner_rect = winner_text.get_rect(center=(consts.width // 2, 250))
            self.screen.blit(winner_text, winner_rect)
        
        # Your score
        if self.game_manager and self.game_manager.local_snake:
            score_text = self.small_font.render(
                f"Your Score: {self.game_manager.local_snake.score}",
                True, (200, 200, 200)
            )
            score_rect = score_text.get_rect(center=(consts.width // 2, 300))
            self.screen.blit(score_text, score_rect)
        
        # Return to lobby
        back_text = self.small_font.render("Press ENTER to return to lobby", True, (200, 200, 200))
        back_rect = back_text.get_rect(center=(consts.width // 2, 400))
        self.screen.blit(back_text, back_rect)
        
        pygame.display.flip()
        
    def run(self):
        """Main game loop"""
        # Try to auto-authenticate
        self.authenticate_user()
        
        running = True
        while running:
            self.clock.tick(10)  # 10 FPS for snake game
            
            # Check if game should start (from network event)
            if self.should_start_game and self.state == "waiting":
                self.start_game()
                self.should_start_game = False
            
            # Collect all events first
            events = pygame.event.get()
            
            # Handle events
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                    
                if self.state == "menu":
                    running = self.handle_menu_input(event)
                elif self.state == "lobby":
                    self.handle_lobby_input(event)
                elif self.state == "waiting":
                    self.handle_waiting_input(event)
                elif self.state == "playing":
                    if event.type == pygame.KEYDOWN:
                        keys = [event.unicode]
                        if self.game_manager:
                            self.game_manager.handle(keys)
                elif self.state == "game_over":
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        self.state = "lobby"
                        self.game_manager = None
                        self.room_id = None
                        
            # Update game state
            if self.state == "playing":
                self.update_game()
            elif self.state in ["waiting", "lobby"]:
                # Poll for updates
                if self.network_manager:
                    self.players = self.network_manager.get_players()
                
            # Draw based on state
            if self.state == "menu":
                self.draw_menu()
            elif self.state in ["login", "register"]:
                result = self.ui_manager.draw_auth_screen(
                    self.state, 
                    self.auth_manager,
                    events  # Pass events to UI manager
                )
                if result == "lobby":
                    self.authenticate_user()
                elif result == "menu":
                    self.state = "menu"
            elif self.state == "lobby":
                self.draw_lobby()
            elif self.state == "waiting":
                self.draw_waiting_room()
            elif self.state == "playing":
                # Game is drawn via cell updates in game_manager
                pass
            elif self.state == "game_over":
                self.draw_game_over()
            elif self.state == "join_input":
                room_id = self.ui_manager.draw_text_input("Enter Room ID:", events)
                if room_id == "cancel":
                    self.state = "lobby"
                elif room_id:
                    self.join_room(room_id)
            elif self.state == "stats":
                if self.network_manager:
                    self.ui_manager.draw_stats(
                        self.auth_manager.current_user['uid'],
                        consts.server_url
                    )
                if self.ui_manager.check_back_button(events):
                    self.state = "lobby"
            elif self.state == "leaderboard":
                if self.network_manager:
                    self.ui_manager.draw_leaderboard(consts.server_url)
                if self.ui_manager.check_back_button(events):
                    self.state = "lobby"
                    
        # Cleanup
        if self.network_manager:
            if self.room_id:
                self.network_manager.leave_room(self.room_id)
            self.network_manager.disconnect()
        pygame.quit()

def main():
    parser = argparse.ArgumentParser(description='Multiplayer Snake Game')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    game = Game(debug=args.debug)
    game.run()

if __name__ == '__main__':
    main()
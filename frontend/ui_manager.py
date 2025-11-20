import pygame
import requests

class UIManager:
    def __init__(self, screen, font, small_font):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.input_text = ""
        self.input_active = False
        self.auth_step = "email"  # "email" or "password"
        self.email = ""
        self.password = ""
        
    def draw_auth_screen(self, auth_type, auth_manager, events):
        """Draw authentication screen (login/register)"""
        from consts import back_color, width, height
        
        self.screen.fill(back_color)
        
        # Title
        title = auth_type.capitalize()
        title_text = self.font.render(title, True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(width // 2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Instructions
        if self.auth_step == "email":
            prompt = "Enter your email:"
        else:
            prompt = "Enter password (or leave empty for 'password123'):"
            
        prompt_text = self.small_font.render(prompt, True, (200, 200, 200))
        prompt_rect = prompt_text.get_rect(center=(width // 2, 150))
        self.screen.blit(prompt_text, prompt_rect)
        
        instructions = [
            "Press ENTER to continue",
            "Press ESC to go back",
            "",
            "(Simplified auth - password defaults to 'password123')"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_text = self.small_font.render(instruction, True, (150, 150, 150))
            inst_rect = inst_text.get_rect(center=(width // 2, 400 + i * 25))
            self.screen.blit(inst_text, inst_rect)
        
        # Input box
        input_box = pygame.Rect(width // 2 - 200, 250, 400, 50)
        color = (100, 150, 255) if self.input_active else (100, 100, 100)
        pygame.draw.rect(self.screen, color, input_box, 3)
        
        # Input text (mask password)
        display_text = self.input_text
        if self.auth_step == "password" and self.input_text:
            display_text = "*" * len(self.input_text)
            
        input_surface = self.small_font.render(display_text, True, (255, 255, 255))
        self.screen.blit(input_surface, (input_box.x + 10, input_box.y + 15))
        
        # Cursor blink
        if self.input_active and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = input_box.x + 10 + input_surface.get_width() + 2
            pygame.draw.line(self.screen, (255, 255, 255), 
                           (cursor_x, input_box.y + 10), 
                           (cursor_x, input_box.y + 40), 2)
        
        pygame.display.flip()
        
        # Handle input from events passed in
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.input_active = True
                
                if event.key == pygame.K_ESCAPE:
                    self.reset_auth_state()
                    return "menu"
                    
                elif event.key == pygame.K_RETURN:
                    if self.auth_step == "email":
                        # Save email and move to password
                        self.email = self.input_text
                        self.input_text = ""
                        self.auth_step = "password"
                    else:
                        # Process authentication
                        password = self.input_text if self.input_text else "password123"
                        
                        if auth_type == "login":
                            success, message = auth_manager.login(self.email, password)
                        else:
                            username = self.email.split('@')[0]
                            success, message = auth_manager.register(
                                self.email, 
                                password, 
                                username
                            )
                        
                        print(f"Auth result: {success}, {message}")
                        
                        if success:
                            self.reset_auth_state()
                            return "lobby"
                        else:
                            # Show error and reset
                            print(f"Authentication failed: {message}")
                            self.reset_auth_state()
                            
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                    
                else:
                    # Add character
                    if len(self.input_text) < 50:  # Limit length
                        self.input_text += event.unicode
        
        return None
    
    def reset_auth_state(self):
        """Reset authentication state"""
        self.input_text = ""
        self.email = ""
        self.password = ""
        self.auth_step = "email"
        self.input_active = False
        
    def draw_text_input(self, prompt, events):
        """Draw text input screen"""
        from consts import back_color, width, height
        
        self.screen.fill(back_color)
        
        # Prompt
        prompt_text = self.font.render(prompt, True, (255, 255, 255))
        prompt_rect = prompt_text.get_rect(center=(width // 2, 200))
        self.screen.blit(prompt_text, prompt_rect)
        
        # Input box
        input_box = pygame.Rect(width // 2 - 200, 300, 400, 50)
        color = (100, 150, 255) if self.input_active else (100, 100, 100)
        pygame.draw.rect(self.screen, color, input_box, 3)
        
        # Input text
        input_surface = self.small_font.render(self.input_text, True, (255, 255, 255))
        self.screen.blit(input_surface, (input_box.x + 10, input_box.y + 15))
        
        # Cursor blink
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = input_box.x + 10 + input_surface.get_width() + 2
            pygame.draw.line(self.screen, (255, 255, 255), 
                           (cursor_x, input_box.y + 10), 
                           (cursor_x, input_box.y + 40), 2)
        
        # Instructions
        inst_text = self.small_font.render("Press ENTER to submit, ESC to cancel", True, (150, 150, 150))
        inst_rect = inst_text.get_rect(center=(width // 2, 400))
        self.screen.blit(inst_text, inst_rect)
        
        pygame.display.flip()
        
        # Handle input
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.input_active = True
                
                if event.key == pygame.K_ESCAPE:
                    self.input_text = ""
                    self.input_active = False
                    return "cancel"
                    
                elif event.key == pygame.K_RETURN:
                    result = self.input_text
                    self.input_text = ""
                    self.input_active = False
                    return result
                    
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                    
                else:
                    if len(self.input_text) < 50:
                        self.input_text += event.unicode
        
        return None
        
    def draw_stats(self, user_id, server_url="http://localhost:3000"):
        """Draw user statistics screen"""
        from consts import back_color, width, height
        
        self.screen.fill(back_color)
        
        # Title
        title_text = self.font.render("Your Statistics", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(width // 2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Fetch stats
        try:
            response = requests.get(f"{server_url}/api/stats/{user_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                stats = data.get('stats', {})
                recent_games = data.get('recentGames', [])
                
                # Display stats
                stats_y = 120
                stat_items = [
                    f"Games Played: {stats.get('gamesPlayed', 0)}",
                    f"Wins: {stats.get('wins', 0)}",
                    f"Total Score: {stats.get('totalScore', 0)}",
                    f"Win Rate: {stats.get('wins', 0) / max(stats.get('gamesPlayed', 1), 1) * 100:.1f}%"
                ]
                
                for item in stat_items:
                    text = self.small_font.render(item, True, (255, 255, 255))
                    self.screen.blit(text, (100, stats_y))
                    stats_y += 35
                
                # Recent games
                if recent_games:
                    recent_title = self.small_font.render("Recent Games:", True, (255, 255, 0))
                    self.screen.blit(recent_title, (100, stats_y + 20))
                    stats_y += 50
                    
                    for i, game in enumerate(recent_games[:5]):
                        game_text = f"Game {i+1}: Score {game.get('score', 0)}"
                        text = self.small_font.render(game_text, True, (200, 200, 200))
                        self.screen.blit(text, (120, stats_y))
                        stats_y += 30
            else:
                error_text = self.small_font.render("Failed to load statistics", True, (255, 0, 0))
                self.screen.blit(error_text, (100, 150))
        except Exception as e:
            error_text = self.small_font.render(f"Error: {str(e)}", True, (255, 0, 0))
            self.screen.blit(error_text, (100, 150))
        
        # Back button
        back_text = self.small_font.render("Press ESC to go back", True, (150, 150, 150))
        back_rect = back_text.get_rect(center=(width // 2, height - 50))
        self.screen.blit(back_text, back_rect)
        
        pygame.display.flip()
        
    def draw_leaderboard(self, server_url="http://localhost:3000"):
        """Draw leaderboard screen"""
        from consts import back_color, width, height
        
        self.screen.fill(back_color)
        
        # Title
        title_text = self.font.render("Leaderboard", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(width // 2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Fetch leaderboard
        try:
            response = requests.get(f"{server_url}/api/leaderboard?limit=10", timeout=5)
            if response.status_code == 200:
                data = response.json()
                leaderboard = data.get('leaderboard', [])
                
                # Display leaderboard
                y_pos = 120
                for i, player in enumerate(leaderboard):
                    rank = i + 1
                    username = player.get('username', 'Unknown')
                    score = player.get('totalScore', 0)
                    wins = player.get('wins', 0)
                    
                    color = (255, 215, 0) if rank == 1 else (192, 192, 192) if rank == 2 else (205, 127, 50) if rank == 3 else (255, 255, 255)
                    
                    text = f"{rank}. {username} - Score: {score}, Wins: {wins}"
                    text_surface = self.small_font.render(text, True, color)
                    self.screen.blit(text_surface, (100, y_pos))
                    y_pos += 40
            else:
                error_text = self.small_font.render("Failed to load leaderboard", True, (255, 0, 0))
                self.screen.blit(error_text, (100, 150))
        except Exception as e:
            error_text = self.small_font.render(f"Error: {str(e)}", True, (255, 0, 0))
            self.screen.blit(error_text, (100, 150))
        
        # Back button
        back_text = self.small_font.render("Press ESC to go back", True, (150, 150, 150))
        back_rect = back_text.get_rect(center=(width // 2, height - 50))
        self.screen.blit(back_text, back_rect)
        
        pygame.display.flip()
        
    def check_back_button(self, events):
        """Check if ESC was pressed from events"""
        for event in events:
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return True
        return False
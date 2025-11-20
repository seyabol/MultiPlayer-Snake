import socketio
import requests
from threading import Thread
import time

class NetworkManager:
    def __init__(self, server_url):
        self.server_url = server_url
        self.sio = socketio.Client()
        self.connected = False
        self.authenticated = False
        self.player_data = {}
        self.game_state = {}
        self.players = []
        self.winner_info = None
        
        # Callbacks
        self.on_game_start = None  # Callback for when game starts
        
        # Setup event handlers
        self.setup_handlers()
        
        # Connect to server
        try:
            self.sio.connect(server_url)
            self.connected = True
            print(f"Connected to server: {server_url}")
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            
    def setup_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.on('authenticated')
        def on_authenticated(data):
            self.authenticated = True
            self.player_data = data
            print(f"Authenticated as: {data.get('username')}")
            
        @self.sio.on('auth_error')
        def on_auth_error(data):
            print(f"Authentication error: {data.get('message')}")
            self.authenticated = False
            
        @self.sio.on('room_created')
        def on_room_created(data):
            print(f"Room created: {data.get('roomId')}")
            self.game_state = data.get('game', {})
            self.players = self.game_state.get('players', [])
            
        @self.sio.on('player_joined')
        def on_player_joined(data):
            print(f"Player joined: {data.get('username')}")
            self.game_state = data.get('game', {})
            self.players = self.game_state.get('players', [])
            
        @self.sio.on('player_left')
        def on_player_left(data):
            print(f"Player left: {data.get('username')}")
            # Update players list
            game_state = data.get('game', {})
            if game_state:
                self.players = game_state.get('players', [])
            
        @self.sio.on('game_started')
        def on_game_started(data):
            print("Game started!")
            self.game_state = data.get('game', {})
            # Trigger callback if set
            if self.on_game_start:
                self.on_game_start()
            
        @self.sio.on('game_state')
        def on_game_state(data):
            self.game_state = data
            self.players = data.get('players', [])
            
        @self.sio.on('player_died')
        def on_player_died(data):
            print(f"Player died: {data.get('username')}")
            
        @self.sio.on('game_over')
        def on_game_over(data):
            print("Game over!")
            self.winner_info = data.get('winner')
            self.game_state = data.get('finalState', {})
            print(f"Winner ID: {self.winner_info}")
            
        @self.sio.on('error')
        def on_error(data):
            print(f"Error: {data.get('message')}")
            
    def authenticate(self, id_token, username):
        """Authenticate with the server"""
        if not self.connected:
            return False
            
        self.sio.emit('authenticate', {
            'idToken': id_token,
            'username': username
        })
        
        # Wait for authentication
        timeout = 5
        start_time = time.time()
        while not self.authenticated and time.time() - start_time < timeout:
            time.sleep(0.1)
            
        return self.authenticated
        
    def create_room(self, config):
        """Create a new game room"""
        if not self.authenticated:
            print("Not authenticated")
            return None
            
        self.sio.emit('create_room', {
            'config': config,
            'color': [0, 255, 0]
        })
        
        # Wait for room creation
        time.sleep(0.5)
        return self.game_state.get('id')
        
    def join_room(self, room_id, color=None):
        """Join an existing game room"""
        if not self.authenticated:
            print("Not authenticated")
            return False
            
        if color is None:
            color = [0, 0, 255]
            
        self.sio.emit('join_room', {
            'roomId': room_id,
            'color': color
        })
        
        # Wait a bit for join confirmation
        time.sleep(0.3)
        return True
        
    def start_game(self, room_id):
        """Start the game (host only)"""
        self.sio.emit('start_game', {
            'roomId': room_id
        })
        
    def send_game_update(self, room_id, snake_data, score):
        """Send game state update to server"""
        self.sio.emit('game_update', {
            'roomId': room_id,
            'snakeData': snake_data,
            'score': score
        })
        
    def send_player_died(self, room_id):
        """Notify server that player died"""
        self.sio.emit('player_died', {
            'roomId': room_id
        })
        
    def leave_room(self, room_id):
        """Leave the current room"""
        self.sio.emit('leave_room', {
            'roomId': room_id
        })
        
    def get_game_state(self):
        """Get current game state"""
        return self.game_state
        
    def get_players(self):
        """Get list of players in current game"""
        return self.players
        
    def get_player_data(self):
        """Get current player data"""
        return self.player_data
        
    def get_winner_info(self):
        """Get winner information (returns winner's user ID)"""
        return self.winner_info
        
    def get_active_games(self):
        """Get list of active games from REST API"""
        try:
            response = requests.get(f"{self.server_url}/api/games/active", timeout=5)
            if response.status_code == 200:
                return response.json().get('games', [])
        except Exception as e:
            print(f"Error fetching active games: {e}")
        return []
        
    def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            self.sio.disconnect()
            self.connected = False
            print("Disconnected from server")
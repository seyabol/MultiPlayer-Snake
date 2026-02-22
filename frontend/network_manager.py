import socketio
import requests
import time


class NetworkManager:
    def __init__(self, server_url):
        self.server_url = server_url
        self.sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=1)

        self.connected = False
        self.authenticated = False

        self.player_data = {}
        self.game_state = {}
        self.players = []
        self.rooms = []
        self.winner_info = None

        self.last_error = None
        self.on_game_start = None

        self.setup_handlers()

        try:
            self.sio.connect(server_url)
            self.connected = True
            print(f"Connected to server: {server_url}")
        except Exception as e:
            self.connected = False
            self.last_error = f"Server connection failed: {e}"
            print(self.last_error)

    def setup_handlers(self):
        @self.sio.on('connect')
        def _():
            self.connected = True

        @self.sio.on('disconnect')
        def _():
            self.connected = False
            self.authenticated = False

        @self.sio.on('authenticated')
        def on_authenticated(data):
            self.authenticated = True
            self.player_data = data
            self.last_error = None
            print(f"Authenticated as: {data.get('username')}")

        @self.sio.on('auth_error')
        def on_auth_error(data):
            self.authenticated = False
            self.last_error = data.get('message')
            print(f"Authentication error: {self.last_error}")

        @self.sio.on('rooms_update')
        def on_rooms_update(data):
            self.rooms = data.get('rooms', []) or []

        @self.sio.on('room_created')
        def on_room_created(data):
            self.game_state = data.get('game', {}) or {}
            self.players = self.game_state.get('players', []) or []
            self.last_error = None

        @self.sio.on('joined_room')
        def on_joined_room(data):
            self.game_state = data.get('game', {}) or {}
            self.players = self.game_state.get('players', []) or []
            self.last_error = None

        @self.sio.on('player_joined')
        def on_player_joined(data):
            self.game_state = data.get('game', {}) or {}
            self.players = self.game_state.get('players', []) or []

        @self.sio.on('player_left')
        def on_player_left(data):
            game_state = data.get('game')
            if game_state:
                self.game_state = game_state
                self.players = self.game_state.get('players', []) or []

        @self.sio.on('game_started')
        def on_game_started(data):
            self.game_state = data.get('game', {}) or {}
            if self.on_game_start:
                self.on_game_start()

        @self.sio.on('game_state')
        def on_game_state(data):
            self.game_state = data or {}
            self.players = self.game_state.get('players', []) or []

        @self.sio.on('game_over')
        def on_game_over(data):
            self.winner_info = data.get('winner')
            self.game_state = data.get('finalState', {}) or {}

        @self.sio.on('error')
        def on_error(data):
            self.last_error = data.get('message')
            print(f"Error: {self.last_error}")

    def authenticate(self, id_token, username, user_id=None):
        if not self.connected:
            self.last_error = "Not connected"
            return False

        payload = {
            'idToken': id_token,
            'username': username,
        }
        if user_id:
            payload['userId'] = user_id

        try:
            res = self.sio.call('authenticate', payload, timeout=5)
            if res and res.get('ok'):
                self.authenticated = True
        except Exception:
            pass

        timeout = 5
        start_time = time.time()
        while not self.authenticated and time.time() - start_time < timeout:
            time.sleep(0.05)

        return self.authenticated

    def refresh_rooms(self):
        if not self.connected:
            return []

        try:
            res = self.sio.call('list_rooms', {}, timeout=3)
            if res and res.get('ok'):
                self.rooms = res.get('rooms', []) or []
                return self.rooms
        except Exception:
            pass

        try:
            r = requests.get(f"{self.server_url}/api/rooms", timeout=3)
            if r.status_code == 200:
                self.rooms = r.json().get('rooms', []) or []
        except Exception:
            pass

        return self.rooms

    def create_room(self, config, title=None):
        if not self.authenticated:
            self.last_error = "Not authenticated"
            return None

        payload = {
            'config': config,
            'color': [0, 255, 0],
        }
        if title:
            payload['title'] = title

        try:
            res = self.sio.call('create_room', payload, timeout=4)
            if res and res.get('ok'):
                return res.get('roomId')
            self.last_error = res.get('error') if isinstance(res, dict) else "Create room failed"
        except Exception as e:
            self.last_error = f"Create room failed: {e}"

        return None

    def join_room(self, room_id, color=None):
        if not self.authenticated:
            self.last_error = "Not authenticated"
            return False

        payload = {
            'roomId': room_id,
            'color': color or [0, 0, 255],
        }

        try:
            res = self.sio.call('join_room', payload, timeout=4)
            if res and res.get('ok'):
                return True
            self.last_error = res.get('error') if isinstance(res, dict) else "Join failed"
        except Exception as e:
            self.last_error = f"Join failed: {e}"

        return False

    def start_game(self, room_id):
        try:
            self.sio.call('start_game', {'roomId': room_id}, timeout=3)
        except Exception:
            self.sio.emit('start_game', {'roomId': room_id})

    def send_game_update(self, room_id, snake_data, score):
        self.sio.emit('game_update', {
            'roomId': room_id,
            'snakeData': snake_data,
            'score': score,
        })

    def send_player_died(self, room_id):
        self.sio.emit('player_died', {'roomId': room_id})

    def leave_room(self, room_id):
        try:
            self.sio.call('leave_room', {'roomId': room_id}, timeout=2)
        except Exception:
            self.sio.emit('leave_room', {'roomId': room_id})

    def get_game_state(self):
        return self.game_state

    def get_players(self):
        return self.players

    def get_rooms(self):
        return self.rooms

    def get_host_id(self):
        return (self.game_state or {}).get('hostId')

    def get_player_data(self):
        return self.player_data

    def get_winner_info(self):
        return self.winner_info

    def get_active_games(self):
        try:
            response = requests.get(f"{self.server_url}/api/games/active", timeout=5)
            if response.status_code == 200:
                return response.json().get('games', [])
        except Exception:
            pass
        return []

    def disconnect(self):
        if self.connected:
            self.sio.disconnect()
            self.connected = False

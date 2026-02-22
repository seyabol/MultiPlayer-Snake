import json
import os
import pickle
import uuid
import hashlib
import requests


class AuthManager:
    """Auth manager.

    - If firebase_config.json has a real api_key, uses Firebase Auth REST API.
    - Otherwise uses a simple local auth (good for portfolio / offline testing).

    Local auth stores users in users_local.json and a logged-in session in session.pkl.
    """

    def __init__(self, config_file='firebase_config.json'):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.session_file = os.path.join(self.base_dir, 'session.pkl')
        self.local_users_file = os.path.join(self.base_dir, 'users_local.json')

        self.current_user = None
        self.project_id = None
        self.api_key = None
        self.mode = 'local'

        # Load Firebase config (optional)
        cfg_path = os.path.join(self.base_dir, config_file)
        try:
            if os.path.exists(cfg_path):
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.project_id = config.get('project_id')
                self.api_key = config.get('api_key')

                if self.api_key and self.api_key != 'YOUR_FIREBASE_WEB_API_KEY':
                    self.mode = 'firebase'
        except Exception as e:
            print(f"Auth config load error: {e}")

        self._ensure_local_users_file()
        self.load_session()

    # -----------------
    # Local auth helpers
    # -----------------

    def _ensure_local_users_file(self):
        if not os.path.exists(self.local_users_file):
            try:
                with open(self.local_users_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
            except Exception:
                pass

    def _load_local_users(self):
        try:
            with open(self.local_users_file, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def _save_local_users(self, users):
        try:
            with open(self.local_users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    # -----------------
    # Public API
    # -----------------

    def register(self, email, password, username):
        if self.mode == 'firebase':
            return self._firebase_register(email, password, username)
        return self._local_register(email, password, username)

    def login(self, email, password):
        if self.mode == 'firebase':
            return self._firebase_login(email, password)
        return self._local_login(email, password)

    def logout(self):
        self.current_user = None
        if os.path.exists(self.session_file):
            try:
                os.remove(self.session_file)
            except Exception:
                pass
        return True

    def get_id_token(self):
        # For local auth we return a constant marker; server DEV mode ignores it.
        if not self.current_user:
            return None
        return self.current_user.get('idToken') or ('dev' if self.mode == 'local' else None)

    def get_user_id(self):
        if not self.current_user:
            return None
        return self.current_user.get('uid')

    def is_authenticated(self):
        return self.current_user is not None

    def has_any_user(self):
        if self.mode == 'firebase':
            return True
        users = self._load_local_users()
        return bool(users)

    # -----------------
    # Session
    # -----------------

    def save_session(self):
        try:
            with open(self.session_file, 'wb') as f:
                pickle.dump(self.current_user, f)
        except Exception as e:
            print(f"Error saving session: {e}")

    def load_session(self):
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'rb') as f:
                    self.current_user = pickle.load(f)
        except Exception:
            self.current_user = None

    # -----------------
    # Local auth impl
    # -----------------

    def _local_register(self, email, password, username):
        users = self._load_local_users()
        key = email.strip().lower()
        if key in users:
            return False, 'User already exists (local)'

        uid = str(uuid.uuid4())
        users[key] = {
            'uid': uid,
            'email': key,
            'username': username.strip() or key.split('@')[0],
            'passwordHash': self._hash_password(password),
        }
        self._save_local_users(users)

        self.current_user = {
            'uid': uid,
            'email': key,
            'username': users[key]['username'],
            'idToken': 'dev',
        }
        self.save_session()
        return True, 'Registration successful (local)'

    def _local_login(self, email, password):
        users = self._load_local_users()
        key = email.strip().lower()
        user = users.get(key)
        if not user:
            return False, 'User not found (local)'

        if user.get('passwordHash') != self._hash_password(password):
            return False, 'Wrong password (local)'

        self.current_user = {
            'uid': user['uid'],
            'email': user['email'],
            'username': user['username'],
            'idToken': 'dev',
        }
        self.save_session()
        return True, 'Login successful (local)'

    # -----------------
    # Firebase auth impl
    # -----------------

    def _firebase_register(self, email, password, username):
        if not self.api_key:
            return False, 'Firebase not configured'

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
            payload = {"email": email, "password": password, "returnSecureToken": True}
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self._firebase_update_profile(data['idToken'], username)

                self.current_user = {
                    'uid': data['localId'],
                    'email': email,
                    'username': username,
                    'idToken': data['idToken'],
                    'refreshToken': data.get('refreshToken'),
                }
                self.save_session()
                return True, 'Registration successful'

            error_message = response.json().get('error', {}).get('message', 'Registration failed')
            return False, error_message

        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    def _firebase_login(self, email, password):
        if not self.api_key:
            return False, 'Firebase not configured'

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            payload = {"email": email, "password": password, "returnSecureToken": True}
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                username = self._firebase_get_user_profile(data['idToken'])

                self.current_user = {
                    'uid': data['localId'],
                    'email': email,
                    'username': username or email.split('@')[0],
                    'idToken': data['idToken'],
                    'refreshToken': data.get('refreshToken'),
                }
                self.save_session()
                return True, 'Login successful'

            error_message = response.json().get('error', {}).get('message', 'Login failed')
            return False, error_message

        except Exception as e:
            return False, f"Login failed: {str(e)}"

    def _firebase_update_profile(self, id_token, display_name):
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={self.api_key}"
            payload = {"idToken": id_token, "displayName": display_name, "returnSecureToken": False}
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"Error updating profile: {e}")

    def _firebase_get_user_profile(self, id_token):
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={self.api_key}"
            payload = {"idToken": id_token}
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                if users:
                    return users[0].get('displayName', '')
        except Exception as e:
            print(f"Error getting profile: {e}")

        return None

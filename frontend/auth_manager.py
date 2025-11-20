import json
import os
import pickle
import requests

class AuthManager:
    def __init__(self, config_file='firebase_config.json'):
        self.current_user = None
        self.session_file = 'session.pkl'
        
        # Load Firebase config
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.project_id = config['project_id']
                # Get Web API Key from Firebase Console
                # Go to Project Settings > General > Web API Key
                self.api_key = "AIzaSyBSjiI200g3cjhoG8nTZoxbOiNr_k6rOv4"  # You need to add this!
        except Exception as e:
            print(f"Error loading Firebase config: {e}")
            self.project_id = None
            self.api_key = None
            
        # Try to load saved session
        self.load_session()
        
    def register(self, email, password, username):
        """Register a new user using Firebase REST API"""
        if not self.api_key:
            return False, "Firebase not configured"
            
        try:
            # Create user with Firebase Authentication REST API
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
            
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                # Update display name
                self.update_profile(data['idToken'], username)
                
                self.current_user = {
                    'uid': data['localId'],
                    'email': email,
                    'username': username,
                    'idToken': data['idToken'],
                    'refreshToken': data['refreshToken']
                }
                
                self.save_session()
                return True, "Registration successful"
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Registration failed')
                return False, error_message
                
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
            
    def login(self, email, password):
        """Login user using Firebase REST API"""
        if not self.api_key:
            return False, "Firebase not configured"
            
        try:
            # Sign in with Firebase Authentication REST API
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                # Get user profile
                username = self.get_user_profile(data['idToken'])
                
                self.current_user = {
                    'uid': data['localId'],
                    'email': email,
                    'username': username or email.split('@')[0],
                    'idToken': data['idToken'],
                    'refreshToken': data['refreshToken']
                }
                
                self.save_session()
                return True, "Login successful"
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Login failed')
                return False, error_message
                
        except Exception as e:
            return False, f"Login failed: {str(e)}"
            
    def update_profile(self, id_token, display_name):
        """Update user profile"""
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={self.api_key}"
            
            payload = {
                "idToken": id_token,
                "displayName": display_name,
                "returnSecureToken": False
            }
            
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Error updating profile: {e}")
            
    def get_user_profile(self, id_token):
        """Get user profile information"""
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={self.api_key}"
            
            payload = {
                "idToken": id_token
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                if users:
                    return users[0].get('displayName', '')
        except Exception as e:
            print(f"Error getting profile: {e}")
            
        return None
        
    def refresh_token(self):
        """Refresh the ID token using refresh token"""
        if not self.current_user or not self.current_user.get('refreshToken'):
            return False
            
        try:
            url = f"https://securetoken.googleapis.com/v1/token?key={self.api_key}"
            
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": self.current_user['refreshToken']
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.current_user['idToken'] = data['id_token']
                self.current_user['refreshToken'] = data['refresh_token']
                self.save_session()
                return True
        except Exception as e:
            print(f"Error refreshing token: {e}")
            
        return False
            
    def logout(self):
        """Logout current user"""
        self.current_user = None
        if os.path.exists(self.session_file):
            os.remove(self.session_file)
        return True
        
    def get_id_token(self):
        """Get ID token for current user"""
        if self.current_user:
            # Check if token needs refresh (tokens expire after 1 hour)
            # For simplicity, we'll just return the current token
            return self.current_user.get('idToken')
        return None
        
    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.current_user is not None
        
    def save_session(self):
        """Save current session to file"""
        try:
            with open(self.session_file, 'wb') as f:
                pickle.dump(self.current_user, f)
        except Exception as e:
            print(f"Error saving session: {e}")
            
    def load_session(self):
        """Load session from file"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'rb') as f:
                    self.current_user = pickle.load(f)
                print("Session loaded successfully")
                # Try to refresh token if session exists
                self.refresh_token()
                return True
        except Exception as e:
            print(f"Error loading session: {e}")
        return False
        
    def get_current_user(self):
        """Get current user data"""
        return self.current_user
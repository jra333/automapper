import streamlit as st
import uuid
import hashlib
from .snowflake_utils import get_snowflake_connection
from config import Config

class AuthManager:
    def __init__(self):
        """Initialize the authentication manager"""
        # Remove connection initialization since we're mocking
        pass

    def hash_password(self, password):
        """Create a secure hash of the password"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username, password):
        """Mock authentication"""
        mock_users = {
            'mapper': {'account_type': 'Mapper'},
            'partnership': {'account_type': 'Partnership'},
            'performance': {'account_type': 'Performance'}
        }
        
        if username in mock_users:
            return {
                'id': username,
                'username': username,
                'name': username.title(),
                'email': f'{username}@example.com',
                'account_type': mock_users[username]['account_type']
            }
        return None

    def register_user(self, username, name, password, email, account_type):
        """Mock user registration"""
        return True, "User registered successfully"

    def get_user_data(self, username):
        """Mock get user data"""
        if username in ['mapper', 'partnership', 'performance']:
            return {
                'id': username,
                'username': username,
                'name': username.title(),
                'email': f'{username}@example.com',
                'account_type': username.title()
            }
        return None

 
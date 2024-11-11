"""
Authorization Management Module for GaDL Telegram Bot

This module handles user authentication, authorization, and access control.
"""

import os
import json
import logging
from typing import List, Dict, Union
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

class UserAuthorization:
    """
    Manages user authorization and access control
    """
    
    def __init__(self, 
                 auth_file: str = 'users_auth.json', 
                 max_users: int = 100, 
                 default_quota: int = 10):
        """
        Initialize UserAuthorization
        
        :param auth_file: Path to store user authorization data
        :param max_users: Maximum number of authorized users
        :param default_quota: Default download quota per user
        """
        self.auth_file = auth_file
        self.max_users = max_users
        self.default_quota = default_quota
        self.users = self._load_users()

    def _load_users(self) -> Dict[str, Dict]:
        """
        Load user authorization data from file
        
        :return: Dictionary of authorized users
        """
        try:
            if not os.path.exists(self.auth_file):
                return {}
            
            with open(self.auth_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading user auth file: {e}")
            return {}

    def _save_users(self):
        """
        Save user authorization data to file
        """
        try:
            os.makedirs(os.path.dirname(self.auth_file), exist_ok=True)
            with open(self.auth_file, 'w') as f:
                json.dump(self.users, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving user auth file: {e}")

    def add_user(self, 
                 user_id: int, 
                 username: str = None, 
                 role: str = 'user') -> bool:
        """
        Add a new authorized user
        
        :param user_id: Telegram User ID
        :param username: Telegram Username
        :param role: User role (default: 'user')
        :return: Whether user was successfully added
        """
        user_id_str = str(user_id)
        
        # Check user limit
        if len(self.users) >= self.max_users:
            logger.warning("Maximum user limit reached")
            return False
        
        # Check if user already exists
        if user_id_str in self.users:
            logger.info(f"User {user_id} already authorized")
            return False
        
        # Add new user
        self.users[user_id_str] = {
            'username': username,
            'role': role,
            'joined_date': datetime.now().isoformat(),
            'quota': {
                'total': self.default_quota,
                'used': 0,
                'reset_date': (datetime.now() + timedelta(days=30)).isoformat()
            },
            'is_active': True
        }
        
        self._save_users()
        logger.info(f"User {user_id} authorized successfully")
        return True

    def remove_user(self, user_id: int) -> bool:
        """
        Remove an authorized user
        
        :param user_id: Telegram User ID
        :return: Whether user was successfully removed
        """
        user_id_str = str(user_id)
        
        if user_id_str in self.users:
            del self.users[user_id_str]
            self._save_users()
            logger.info(f"User {user_id} removed")
            return True
        
        return False

    def is_authorized(self, user_id: int) -> bool:
        """
        Check if a user is authorized
        
        :param user_id: Telegram User ID
        :return: Authorization status
        """
        user_id_str = str(user_id)
        
        # Check if user exists and is active
        return (user_id_str in self.users and 
                self.users[user_id_str].get('is_active', False))

    def check_download_quota(self, user_id: int) -> bool:
        """
        Check if user has available download quota
        
        :param user_id: Telegram User ID
        :return: Whether user can download
        """
        user_id_str = str(user_id)
        
        if not self.is_authorized(user_id):
            return False
        
        user_data = self.users[user_id_str]
        quota = user_data.get('quota', {})
        
        # Check and reset quota if needed
        reset_date = datetime.fromisoformat(quota.get('reset_date', datetime.now().isoformat()))
        if datetime.now() >= reset_date:
            quota['used'] = 0
            quota['reset_date'] = (datetime.now() + timedelta(days=30)).isoformat()
        
        # Check remaining quota
        return quota.get('used', 0) < quota.get('total', self.default_quota)

    def use_download_quota(self, user_id: int):
        """
        Consume a download quota for a user
        
        :param user_id: Telegram User ID
        """
        user_id_str = str(user_id)
        
        if self.check_download_quota(user_id):
            user_data = self.users[user_id_str]
            user_data['quota']['used'] = user_data['quota'].get('used', 0) + 1
            self._save_users()

    def get_user_info(self, user_id: int) -> Union[Dict, None]:
        """
        Get detailed user information
        
        :param user_id: Telegram User ID
        :return: User information dictionary
        """
        user_id_str = str(user_id)
        return self.users.get(user_id_str)

    def update_user_role(self, user_id: int, role: str) -> bool:
        """
        Update user role
        
        :param user_id: Telegram User ID
        :param role: New user role
        :return: Whether role was updated successfully
        """
        user_id_str = str(user_id)
        
        if user_id_str in self.users:
            self.users[user_id_str]['role'] = role
            self._save_users()
            return True
        
        return False

    def list_authorized_users(self) -> List[Dict]:
        """
        List all authorized users
        
        :return: List of authorized user details
        """
        return [
            {
                'user_id': int(user_id),
                'username': user_data.get('username'),
                'role': user_data.get('role'),
                'joined_date': user_data.get('joined_date'),
                'quota_used': user_data.get('quota', {}).get('used', 0),
                'quota_total': user_data.get('quota', {}).get('total', self.default_quota)
            }
            for user_id, user_data in self.users.items()
        ]

# Admin Utility Functions
def generate_invite_code(length: int = 8) -> str:
    """
    Generate a secure invite code
    
    :param length: Length of invite code
    :return: Generated invite code
    """
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    """
    Example usage and testing
    """
    auth = UserAuthorization()
    
    # Add a test user
    user_id = 123456789
    auth.add_user(user_id, username='testuser')
    
    # Check authorization
    print(f"Is user authorized? {auth.is_authorized(user_id)}")
     ```python
    # List authorized users
    users = auth.list_authorized_users()
    print("Authorized Users:", users)

    # Check download quota
    print(f"User  {user_id} download quota available? {auth.check_download_quota(user_id)}")

    # Use download quota
    auth.use_download_quota(user_id)
    print(f"User  {user_id} quota used after download: {auth.get_user_info(user_id)['quota']['used']}")

    # Remove the test user
    auth.remove_user(user_id)
    print(f"Is user authorized after removal? {auth.is_authorized(user_id)}")

if __name__ == '__main__':
    main()

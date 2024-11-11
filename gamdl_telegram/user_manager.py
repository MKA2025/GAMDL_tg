"""
User Management Module for GaDL Telegram Bot

This module provides advanced user management capabilities.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid

# Configure logging
logger = logging.getLogger(__name__)

class UserManager:
    """
    Advanced User Management System
    """
    
    def __init__(
        self, 
        users_file: str = 'users_database.json', 
        max_users: int = 1000,
        default_quota: int = 10
    ):
        """
        Initialize UserManager
        
        :param users_file: Path to users database file
        :param max_users: Maximum number of users
        :param default_quota: Default download quota
        """
        self.users_file = users_file
        self.max_users = max_users
        self.default_quota = default_quota
        self.users = self._load_users()

    def _load_users(self) -> Dict[str, Dict]:
        """
        Load users from JSON file
        
        :return: Dictionary of users
        """
        try:
            if not os.path.exists(self.users_file):
                return {}
            
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading users file: {e}")
            return {}

    def _save_users(self):
        """
        Save users to JSON file
        """
        try:
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving users file: {e}")

    def create_user(
        self, 
        user_id: int, 
        username: Optional[str] = None, 
        role: str = 'user'
    ) -> Dict:
        """
        Create a new user
        
        :param user_id: Telegram User ID
        :param username: Telegram Username
        :param role: User role
        :return: User data dictionary
        """
        user_id_str = str(user_id)
        
        # Check user limit
        if len(self.users) >= self.max_users:
            logger.warning("Maximum user limit reached")
            return None
        
        # Check if user already exists
        if user_id_str in self.users:
            logger.info(f"User {user_id} already exists")
            return self.users[user_id_str]
        
        # Generate unique user token
        user_token = str(uuid.uuid4())
        
        # Create user data
        user_data = {
            'user_id': user_id,
            'username': username,
            'token': user_token,
            'role': role,
            'registration_date': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat(),
            'status': {
                'is_active': True,
                'is_banned': False
            },
            'download_stats': {
                'total_downloads': 0,
                'monthly_downloads': 0,
                'last_download_date': None
            },
            'quota': {
                'total': self.default_quota,
                'used': 0,
                'reset_date': (datetime.now() + timedelta(days=30)).isoformat()
            },
            'preferences': {
                'download_format': 'best',
                'notification_preferences': {
                    'download_complete': True,
                    'quota_warning': True
                }
            }
        }
        
        # Save user
        self.users[user_id_str] = user_data
        self._save_users()
        
        logger.info(f"User {user_id} created successfully")
        return user_data

    def update_user(
        self, 
        user_id: int, 
        updates: Dict
    ) -> Optional[Dict]:
        """
        Update user information
        
        :param user_id: Telegram User ID
        :param updates: Dictionary of updates
        :return: Updated user data
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.users:
            logger.warning(f"User {user_id} not found")
            return None
        
        # Merge updates
        self.users[user_id_str].update(updates)
        self.users[user_id_str]['last_active'] = datetime.now().isoformat()
        
        self._save_users()
        return self.users[user_id_str]

    def get_user(self, user_id: int) -> Optional[Dict]:
        """
        Get user information
        
        :param user_id: Telegram User ID
        :return: User data dictionary
        """
        return self.users.get(str(user_id))

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user
        
        :param user_id: Telegram User ID
        :return: Deletion status
        """
        user_id_str = str(user_id)
        
        if user_id_str in self.users:
            del self.users[user_id_str]
            self._save_users()
            logger.info(f"User {user_id} deleted")
            return True
        
        return False

    def check_user_quota(self, user_id: int) -> bool:
        """
        Check if user has available download quota
        
        :param user_id: Telegram User ID
        :return: Quota availability
        """
        user = self.get_user(user_id)
        
        if not user or user['status']['is_banned']:
            return False
        
        quota = user['quota']
        reset_date = datetime.fromisoformat(quota['reset_date'])
        
        # Reset quota if needed
        if datetime.now() >= reset_date:
            quota['used'] = 0
            quota['reset_date'] = (datetime.now() + timedelta(days=30)).isoformat()
        
        return quota['used'] < quota['total']

    def use_download_quota(self, user_id: int):
        """
        Consume user download quota
        
        :param user_id: Telegram User ID
        """
        user_id_str = str(user_id)
        
        if user_id_str in self.users:
            user = self.users[user_id_str]
            user['quota']['used'] += 1
            user['download_stats']['total_downloads'] += 1
            user['download_stats']['monthly_downloads'] += 1
            user['download_stats']['last_download_date'] = datetime.now().isoformat()
            
            self._save_users()

    def list_users(
        self, 
        status: Optional[str] = None, 
        role: Optional[str] = None
    ) -> List[Dict]:
        """
        List users with optional filtering
        
        :param status: Filter by user status
        :param role: Filter by user role
        :return: List of user data
        """
        filtered_users = []
        
        for user_data in self.users.values():
            if (status is None or user_data['status'].get('is_active') == (status == 'active')) and \
               (role is None or user_data['role'] == role):
                filtered_users.append(user_data)
        
        return filtered_users

    def generate_invite_token(
        self, 
        role: str = 'user', 
        expires_in: int = 7
    ) -> Dict:
        """
        Generate an invite token
        
        :param role: Role for invited users
        :param expires_in: Days until token expires
        :return: Invite token details
        """
        token = str(uuid.uuid4())
        invite details = {
            'token': token,
            'role': role,
            'expires_at': (datetime.now() + timedelta(days=expires_in)).isoformat()
        }
        logger.info(f"Generated invite token: {token} for role: {role}")
        return details

def main():
    """
    Example usage and testing of UserManager
    """
    user_manager = UserManager()
    
    # Create a test user
    user_id = 987654321
    user_data = user_manager.create_user(user_id, username='testuser2')
    print("Created User:", user_data)

    # Get user information
    user_info = user_manager.get_user(user_id)
    print("User  Info:", user_info)

    # Check user quota
    print(f"User  {user_id} has quota available? {user_manager.check_user_quota(user_id)}")

    # Use download quota
    user_manager.use_download_quota(user_id)
    print(f"User  {user_id} quota used after download: {user_manager.get_user(user_id)['quota']['used']}")

    # Update user information
    updated_user = user_manager.update_user(user_id, {'role': 'admin'})
    print("Updated User Info:", updated_user)

    # List all users
    all_users = user_manager.list_users()
    print("All Users:", all_users)

    # Delete the test user
    user_manager.delete_user(user_id)
    print(f"User  {user_id} deleted. Current user info:", user_manager.get_user(user_id))

if __name__ == '__main__':
    main()

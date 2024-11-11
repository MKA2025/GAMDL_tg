"""
Admin Panel Module for GaDL Telegram Bot

Provides advanced administrative controls and monitoring capabilities
for bot management and user administration.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from user_manager import UserManager
from logging_system import AdvancedLogger

class AdminPanel:
    """
    Advanced Administrative Control System
    """
    
    def __init__(
        self, 
        user_manager: UserManager,
        logger: AdvancedLogger,
        config_path: str = 'admin_config.json'
    ):
        """
        Initialize Admin Panel
        
        :param user_manager: User management system
        :param logger: Logging system
        :param config_path: Path to admin configuration file
        """
        self.user_manager = user_manager
        self.logger = logger
        self.config_path = config_path
        self.admin_config = self._load_admin_config()
    
    def _load_admin_config(self) -> Dict[str, Any]:
        """
        Load admin configuration from file
        
        :return: Admin configuration dictionary
        """
        default_config = {
            'admin_users': [],
            'banned_users': [],
            'system_settings': {
                'max_download_quota': 100,
                'global_download_limit': 1000,
                'maintenance_mode': False
            },
            'invite_system': {
                'enabled': True,
                'default_role': 'user',
                'token_duration': 7  # days
            }
        }
        
        try:
            if not os.path.exists(self.config_path):
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                return default_config
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        
        except Exception as e:
            self.logger.log_event('ERROR', f"Failed to load admin config: {e}")
            return default_config
    
    def _save_admin_config(self):
        """
        Save admin configuration to file
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.admin_config, f, indent=4)
        except Exception as e:
            self.logger.log_event('ERROR', f"Failed to save admin config: {e}")
    
    def add_admin_user(self, user_id: int) -> bool:
        """
        Add a user to admin list
        
        :param user_id: Telegram User ID
        :return: Success status
        """
        if user_id not in self.admin_config['admin_users']:
            self.admin_config['admin_users'].append(user_id)
            self._save_admin_config()
            
            self.logger.log_event('INFO', f"Added admin user: {user_id}")
            return True
        return False
    
    def remove_admin_user(self, user_id: int) -> bool:
        """
        Remove a user from admin list
        
        :param user_id: Telegram User ID
        :return: Success status
        """
        if user_id in self.admin_config['admin_users']:
            self.admin_config['admin_users'].remove(user_id)
            self._save_admin_config()
            
            self.logger.log_event('INFO', f"Removed admin user: {user_id}")
            return True
        return False
    
    def is_admin(self, user_id: int) -> bool:
        """
        Check if a user is an admin
        
        :param user_id: Telegram User ID
        :return: Admin status
        """
        return user_id in self.admin_config['admin_users']
    
    def ban_user(
        self, 
        user_id: int, 
        reason: Optional[str] = None, 
        duration: Optional[int] = None
    ) -> bool:
        """
        Ban a user from using the bot
        
        :param user_id: Telegram User ID
        :param reason: Reason for banning
        :param duration: Ban duration in days
        :return: Success status
        """
        ban_entry = {
            'user_id': user_id,
            'banned_at': datetime.now().isoformat(),
            'reason': reason,
            'expires_at': (datetime.now() + timedelta(days=duration)).isoformat() if duration else None
        }
        
        if user_id not in self.admin_config['banned_users']:
            self.admin_config['banned_users'].append(ban_entry)
            self._save_admin_config()
            
            self.logger.log_event('WARNING', f"User banned: {user_id}", {
                'reason': reason,
                'duration': duration
            })
            return True
        return False
    
    def unban_user(self, user_id: int) -> bool:
        """
        Unban a previously banned user
        
        :param user_id: Telegram User ID
        :return: Success status
        """
        for ban_entry in self.admin_config['banned_users']:
            if ban_entry['user_id'] == user_id:
                self.admin_config['banned_users'].remove(ban_entry)
                self._save_admin_config()
                
                self.logger.log_event('INFO', f"User unbanned: {user_id}")
                return True
        return False
    
    def is_banned(self, user_id: int) -> bool:
        """
        Check if a user is banned
        
        :param user_id: Telegram User ID
        :return: Ban status
        """
        for ban_entry in self.admin_config['banned_users']:
            if ban_entry['user_id'] == user_id:
                # Check if ban has expired
                if ban_entry['expires_at']:
                    expires_at = datetime.fromisoformat(ban_entry['expires_at'])
                    if datetime.now() > expires_at:
                        self.unban_user(user_id)
                        return False
                return True
        return False
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Retrieve comprehensive system statistics
        
        :return: System statistics dictionary
        """
        total_users = len(self.user_manager.users)
        active_users = len(self.user_manager.list_users(status='active'))
        banned_users = len(self.admin_config['banned_users'])
        admin_users = len(self.admin_config['admin_users'])
        
        download_stats = {
            'total_downloads': sum(
                user.get('download_stats', {}).get('total_downloads', 0)
                for user in self.user_manager.users.values()
            ),
            'monthly_downloads': sum(
                user.get('download_stats', {}).get('monthly_downloads', 0)
                for user in self.user_manager.users.values()
            )
        }
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'banned_users': banned_users,
            'admin_users': admin_users,
            'download_stats': download_stats,
            'system_settings': self.admin_config['system_settings']
        }
    
    def update_system_settings(
        self, 
        settings: Dict[str, Any]
    ) -> bool:
        """
        Update system-wide settings
        
        :param settings: Dictionary of settings to update
        :return: Success status
        """
        try:
            self.admin_config['system_settings'].update(settings)
            self._save_admin_config()
            
            self.logger.log_event('INFO', 'System settings updated', settings)
            return True
        except Exception as e:
            self.logger.log_event('ERROR', f"Failed to update system settings: { e}")
            return False

def main():
    """
    Example usage and testing of AdminPanel
    """
    # Initialize UserManager and Logger (mocked for this example)
    user_manager = UserManager()  # Assume UserManager is defined elsewhere
    logger = AdvancedLogger()

    # Create AdminPanel instance
    admin_panel = AdminPanel(user_manager=user_manager, logger=logger)

    # Example operations
    admin_panel.add_admin_user(user_id=123456789)
    admin_panel.ban_user(user_id=987654321, reason='Spamming', duration=30)
    stats = admin_panel.get_system_stats()
    print("System Stats:", stats)

if __name__ == '__main__':
    main()

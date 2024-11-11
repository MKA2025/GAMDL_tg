"""
Telegram Bot Integration for GaDL (Gamdl)

This module provides Telegram bot functionality for Apple Music downloads.
"""

# Standard Library Imports
import logging
import os
import sys

# Third-Party Library Imports
try:
    import telebot
    import requests
except ImportError:
    print("Required libraries not installed. Please run 'pip install pyTelegramBotAPI requests'")
    sys.exit(1)

# Local Imports
from ..downloader import Downloader
from ..apple_music_api import AppleMusicApi

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gamdl_telegram.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Version Information
__version__ = "0.1.0"
__author__ = "GaDL Telegram Bot Team"
__email__ = "support@gamdl.telegram"

# Configuration Management
class ConfigManager:
    """
    Manages configuration for the Telegram Bot
    """
    DEFAULT_CONFIG = {
        'bot_token': None,
        'allowed_users': [],
        'log_level': 'INFO',
        'download_path': './downloads',
        'max_downloads_per_user': 5
    }

    @classmethod
    def load_config(cls, config_path=None):
        """
        Load configuration from environment or config file
        """
        config = cls.DEFAULT_CONFIG.copy()
        
        # Priority: Environment Variables > Config File > Default
        config['bot_token'] = os.environ.get('TELEGRAM_BOT_TOKEN', config['bot_token'])
        config['allowed_users'] = os.environ.get('ALLOWED_USERS', '').split(',') or config['allowed_users']
        
        # Optional: Load from config file if path provided
        if config_path and os.path.exists(config_path):
            try:
                import json
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
        
        return config

# Exception Handling
class GaDLTelegramException(Exception):
    """
    Custom exception for GaDL Telegram Bot
    """
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

# Utility Functions
def validate_apple_music_url(url):
    """
    Validate if the provided URL is a valid Apple Music URL
    """
    valid_patterns = [
        'music.apple.com',
        'itunes.apple.com',
        '/song/', '/album/', '/playlist/', '/artist/'
    ]
    return any(pattern in url for pattern in valid_patterns)

def setup_dependencies():
    """
    Check and setup required dependencies
    """
    try:
        import pyTelegramBotAPI
        import requests
        import m3u8
    except ImportError as e:
        logger.critical(f"Missing dependency: {e}")
        sys.exit(1)

# Initialization Function
def initialize_telegram_bot(config_path=None):
    """
    Initialize the Telegram Bot with given configuration
    """
    try:
        config = ConfigManager.load_config(config_path)
        
        # Validate essential configurations
        if not config['bot_token']:
            raise GaDLTelegramException("Bot token is required")
        
        # Setup dependencies
        setup_dependencies()
        
        # Initialize bot and related services
        bot = telebot.TeleBot(config['bot_token'])
        downloader = Downloader()
        apple_music_api = AppleMusicApi()
        
        logger.info(f"GaDL Telegram Bot v{__version__} initialized successfully")
        
        return {
            'bot': bot,
            'downloader': downloader,
            'apple_music_api': apple_music_api,
            'config': config
        }
    
    except Exception as e:
        logger.critical(f"Bot initialization failed: {e}")
        raise

# Expose key components
__all__ = [
    'initialize_telegram_bot',
    'ConfigManager',
    'GaDLTelegramException',
    'validate_apple_music_url',
    '__version__'
]

"""
Bot Configuration Module

Manages bot-specific configuration settings, including:
- Bot credentials
- API keys
- Communication settings
- Feature toggles
- Logging configurations
"""

from __future__ import annotations

import os
import json
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Any
from pathlib import Path

@dataclass
class BotCredentials:
    """
    Secure storage for bot authentication credentials
    """
    token: str = ""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

@dataclass
class CommunicationSettings:
    """
    Bot communication and interaction settings
    """
    default_prefix: str = "!"
    allowed_channels: List[int] = field(default_factory=list)
    ignored_channels: List[int] = field(default_factory=list)
    max_message_length: int = 2000
    rate_limit: int = 5  # messages per second

@dataclass
class FeatureFlags:
    """
    Toggle various bot features
    """
    enable_logging: bool = True
    enable_error_tracking: bool = True
    debug_mode: bool = False
    
    # Specific feature toggles
    music_download: bool = True
    metadata_extraction: bool = True
    quality_selection: bool = True
    
    # Advanced features
    machine_learning_recommendations: bool = False
    automated_playlist_generation: bool = False

@dataclass
class LoggingConfig:
    """
    Logging configuration settings
    """
    log_level: str = "INFO"
    log_file: Optional[str] = "bot.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_log_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5

@dataclass
class ExternalAPIs:
    """
    Configuration for external API services
    """
    musicbrainz_user_agent: str = "GaDL Bot/1.0"
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    apple_music_token: Optional[str] = None

@dataclass
class BotConfiguration:
    """
    Comprehensive bot configuration
    """
    credentials: BotCredentials = field(default_factory=BotCredentials)
    communication: CommunicationSettings = field(default_factory=CommunicationSettings)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    external_apis: ExternalAPIs = field(default_factory=ExternalAPIs)

class BotConfigManager:
    """
    Bot configuration management and loading
    """
    
    CONFIG_FILE_PATH = Path(__file__).parent / "bot_config.json"
    ENV_PREFIX = "GAMDL_BOT_"
    
    def __init__(self):
        self.config = BotConfiguration()
        self.logger = self._setup_logger()
        self.load_configuration()
    
    def _setup_logger(self) -> logging.Logger:
        """
        Set up logging based on configuration
        
        :return: Configured logger
        """
        logger = logging.getLogger("BotConfigManager")
        
        # Configure log level
        log_level = getattr(logging, self.config.logging.log_level.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # File handler (if log file is specified)
        if self.config.logging.log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.config.logging.log_file,
                maxBytes=self.config.logging.max_log_size,
                backupCount=self.config.logging.backup_count
            )
            file_handler.setLevel(log_level)
            
            # Formatters
            formatter = logging.Formatter(self.config.logging.log_format)
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
        
        logger.addHandler(console_handler)
        
        return logger
    
    def load_configuration(self):
        """
        Load configuration from multiple sources
        """
        # Load from JSON config file
        self._load_json_config()
        
        # Override with environment variables
        self._load_env_config()
        
        self.logger.info("Bot configuration loaded successfully")
    
    def _load_json_config(self):
        """
        Load configuration from JSON file
        """
        try:
            if self.CONFIG_FILE_PATH.exists():
                with open(self.CONFIG_FILE_PATH, 'r') as config_file:
                    config_data = json.load(config_file)
                    self._update_config(config_data)
        except Exception as e:
            self.logger.warning(f"Failed to load JSON config: {e}")
    
    def _load_env_config(self):
        """
        Load configuration from environment variables
        """
        env_config = {}
        for key, value in os.environ.items():
            if key.startswith(self.ENV_PREFIX):
                config_key = key[len(self.ENV_PREFIX):].lower()
                env_config[config_key] = value
        
        if env_config:
            self._update_config(env_config)
            self.logger.info("Environment variables loaded into configuration")
    
    def _update_config(self, config_dict: Dict[str, Any]):
        """
        Update configuration with provided dictionary
        
        :param config_dict: Configuration dictionary
        """
        def _recursive_update(current_obj, update_dict):
            for key, value in update_dict.items():
                if hasattr(current_obj, key):
                    current_val = getattr(current_obj, key)
                    if isinstance(current_val, (BotCredentials, CommunicationSettings, 
                                                FeatureFlags, LoggingConfig, ExternalAPIs)):
                        _recursive_update(current_val, value)
                    else:
                        setattr(current_obj, key, value)
        
        _recursive_update(self.config, config_dict)
    
    def save_configuration(self):
        """
        Save current configuration to JSON file
        """
        try:
            config_dict = json.loads(json.dumps(asdict(self.config), indent=4))
            with open(self.CONFIG_FILE_PATH, 'w') as config_file:
                json.dump(config_dict, config_file, indent=4)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def validate_configuration(self):
        """
        Validate critical configuration settings
        """
        errors = []
        
        if not self.config.credentials.token:
            errors.append("Bot token is missing")
        
        if errors:
            self.logger.critical("Configuration validation failed")
            for error in errors:
                self.logger.critical(error)
            raise ValueError("Invalid bot configuration")

# Create a singleton configuration manager
bot_config_manager = BotConfigManager()
bot_config = bot_config_manager.config

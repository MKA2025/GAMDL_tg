"""
Configuration Module for the Project

This module handles the loading and management of configuration settings
for the application. It supports loading from environment variables and
providing default values.
"""

import os
import json
from pathlib import Path

class Config:
    """
    Configuration class to manage application settings.
    """
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """
        Load configuration from environment variables and a JSON file.
        """
        # Load from environment variables
        self.app_name = os.getenv("APP_NAME", "MyApp")
        self.version = os.getenv("APP_VERSION", "1.0.0")
        self.debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")
        
        # Load from a JSON configuration file if it exists
        config_file_path = Path(__file__).parent / "config.json"
        if config_file_path.exists():
            with open(config_file_path, 'r') as config_file:
                config_data = json.load(config_file)
                self.update_config(config_data)
    
    def update_config(self, config_data: dict):
        """
        Update configuration settings from a dictionary.
        
        :param config_data: Dictionary containing configuration settings.
        """
        for key, value in config_data.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f"<Config(app_name={self.app_name}, version={self.version}, debug={self.debug})>"

# Initialize the configuration
config = Config()

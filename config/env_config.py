"""
Environment Configuration Management

Handles environment-specific configurations, 
including development, staging, and production settings.
"""

from __future__ import annotations

import os
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path

class EnvironmentType(Enum):
    """
    Supported environment types
    """
    DEVELOPMENT = auto()
    STAGING = auto()
    PRODUCTION = auto()
    TESTING = auto()

@dataclass
class DatabaseConfig:
    """
    Database configuration settings
    """
    host: str = 'localhost'
    port: int = 5432
    name: str = 'gamdl_db'
    user: str = 'gamdl_user'
    password: Optional[str] = None
    max_connections: int = 10
    ssl_mode: bool = False

@dataclass
class CacheConfig:
    """
    Caching configuration settings
    """
    enabled: bool = True
    backend: str = 'redis'
    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    default_timeout: int = 300  # 5 minutes

@dataclass
class StorageConfig:
    """
    Storage and file system configuration
    """
    base_path: Path = Path('./data')
    download_path: Path = Path('./downloads')
    temp_path: Path = Path('./temp')
    max_storage_gb: float = 50.0
    cleanup_threshold: float = 0.8  # 80% storage usage

@dataclass
class SecurityConfig:
    """
    Security-related configurations
    """
    secret_key: Optional[str] = None
    jwt_expiration: int = 3600  # 1 hour
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 3600  # 1 hour
    allowed_ips: list[str] = field(default_factory=list)

@dataclass
class LoggingConfig:
    """
    Logging configuration settings
    """
    level: str = 'INFO'
    path: Optional[Path] = Path('./logs')
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

@dataclass
class ExternalServicesConfig:
    """
    Configuration for external services and APIs
    """
    apple_music_api_key: Optional[str] = None
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    musicbrainz_user_agent: str = 'GaDL/1.0'

class EnvironmentConfigManager:
    """
    Environment configuration management and loading
    """
    
    ENV_PREFIX = 'GAMDL_'
    CONFIG_FILE_PATH = Path(__file__).parent / 'env_config.json'
    
    def __init__(self, env_type: EnvironmentType = EnvironmentType.DEVELOPMENT):
        """
        Initialize environment configuration
        
        :param env_type: Environment type
        """
        self.env_type = env_type
        self.config = self._create_default_config()
        self.load_configuration()
    
    def _create_default_config(self) -> Dict[EnvironmentType, Dict[str, Any]]:
        """
        Create default configuration for different environments
        
        :return: Configuration dictionary
        """
        return {
            EnvironmentType.DEVELOPMENT: {
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'name': 'gamdl_dev',
                },
                'cache': {
                    'enabled': True,
                    'backend': 'redis',
                },
                'security': {
                    'rate_limit_enabled': False,
                },
                'logging': {
                    'level': 'DEBUG',
                },
            },
            EnvironmentType.STAGING: {
                'database': {
                    'host': 'staging-db.example.com',
                    'port': 5432,
                    'name': 'gamdl_staging',
                },
                'cache': {
                    'enabled': True,
                },
                'security': {
                    'rate_limit_enabled': True,
                    'rate_limit_requests': 200,
                },
                'logging': {
                    'level': 'INFO',
                },
            },
            EnvironmentType.PRODUCTION: {
                'database': {
                    'host': 'prod-db.example.com',
                    'port': 5432,
                    'name': 'gamdl_prod',
                },
                'cache': {
                    'enabled': True,
                    'backend': 'redis-cluster',
                },
                'security': {
                    'rate_limit_enabled': True,
                    'rate_limit_requests': 100,
                },
                'logging': {
                    'level': 'WARNING',
                    'path': Path('/var/log/gamdl'),
                },
            },
            EnvironmentType.TESTING: {
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'name': 'gamdl_test',
                },
                'cache': {
                    'enabled': False,
                },
                'security': {
                    'rate_limit_enabled': False,
                },
                'logging': {
                    'level': 'DEBUG',
                },
            }
        }
    
    def load_configuration(self):
        """
        Load configuration from multiple sources
        """
        # Load environment-specific configuration
        env_config = self._create_default_config().get(self.env_type, {})
        
        # Override with environment variables
        self._load_env_config(env_config)
        
        # Update configuration attributes
        self._update_config_attributes(env_config)
    
    def _load_env_config(self, config: Dict[str, Any]):
        """
        Load configuration from environment variables
        
        :param config: Configuration dictionary to update
        """
        for key, value in os.environ.items():
            if key.startswith(self.ENV_PREFIX):
                config_key = key[len(self.ENV_PREFIX):].lower()
                
                # Recursive update for nested configurations
                def update_nested_config(current_dict, keys, value):
                    if len(keys) == 1:
                        current_dict[keys[0]] = value
                    else:
                        if keys[0] not in current_dict:
                            current_dict[keys[0]] = {}
                        update_nested_config(current_dict[keys[0]], keys[1:], value)
                
                keys = config_key.split('_')
                update_nested_config(config, keys, value)
    
    def _update_config_attributes(self, config: Dict[str, Any]):
        """
        Update configuration attributes based on loaded configuration
        
        :param config: Configuration dictionary
        """
        # Database configuration
        db_config = config.get('database', {})
        self.database = DatabaseConfig(**db_config)
        
        # Cache configuration
        cache_config = config.get('cache', {})
        self.cache = CacheConfig(**cache_config)
        
        # Storage configuration
        storage_config = config.get('storage', {})
        self.storage = StorageConfig(**storage_config)
        
        # Security configuration
        security_config = config.get('security', {})
        self.security = SecurityConfig(**security_config)
        
        # Logging configuration
        logging_config = config.get('logging', {})
        self.logging = LoggingConfig(**logging_config)
        
        # External services configuration
        external_services_config = config.get('external_services', { })
        self.external_services = ExternalServicesConfig(**external_services_config)

# Create an instance of the environment configuration manager
env_config_manager = EnvironmentConfigManager(EnvironmentType.DEVELOPMENT)
env_config = env_config_manager.config
``` ```python
"""

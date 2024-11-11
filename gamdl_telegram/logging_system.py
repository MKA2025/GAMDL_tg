"""
Advanced Logging System for GaDL Telegram Bot

This module provides a comprehensive logging solution with multiple
logging handlers, log rotation, and advanced logging features.
"""

import os
import sys
import logging
import traceback
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
import json

class ColoredFormatter(logging.Formatter):
    """
    Custom colored log formatter for console output
    """
    COLORS = {
        'DEBUG': '\033[94m',    # Blue
        'INFO': '\033[92m',     # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[1;31m'  # Bold Red
    }
    RESET = '\033[0m'

    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.RESET)
        return f"{color}{log_message}{self.RESET}"

class AdvancedLogger:
    """
    Advanced Logging System with multiple handlers and features
    """
    
    def __init__(
        self, 
        log_dir: str = 'logs',
        app_name: str = 'GaDL_Telegram',
        console_level: str = 'INFO',
        file_level: str = 'DEBUG',
        max_log_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
    ):
        """
        Initialize Advanced Logger
        
        :param log_dir: Directory to store log files
        :param app_name: Name of the application
        :param console_level: Logging level for console
        :param file_level: Logging level for file
        :param max_log_size: Maximum log file size
        :param backup_count: Number of backup log files to keep
        """
        self.log_dir = log_dir
        self.app_name = app_name
        
        # Create log directory if not exists
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create main logger
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Console Handler with Colored Formatter
        self._setup_console_handler(console_level)
        
        # File Handlers
        self._setup_file_handlers(file_level, max_log_size, backup_count)
        
        # Exception Hook
        sys.excepthook = self.handle_exception

    def _setup_console_handler(self, console_level: str):
        """
        Setup console handler with colored formatter
        
        :param console_level: Logging level for console
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level.upper()))
        
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

    def _setup_file_handlers(
        self, 
        file_level: str, 
        max_log_size: int, 
        backup_count: int
    ):
        """
        Setup file handlers for different log types
        
        :param file_level: Logging level for files
        :param max_log_size: Maximum log file size
        :param backup_count: Number of backup log files
        """
        # Main Log File (Rotating)
        main_log_path = os.path.join(self.log_dir, f'{self.app_name}_main.log')
        main_handler = RotatingFileHandler(
            main_log_path, 
            maxBytes=max_log_size, 
            backupCount=backup_count
        )
        main_handler.setLevel(getattr(logging, file_level.upper()))
        main_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(main_handler)
        
        # Error Log File (Separate handler for errors)
        error_log_path = os.path.join(self.log_dir, f'{self.app_name}_error.log')
        error_handler = logging.FileHandler(error_log_path)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(error_handler)

    def log_event(
        self, 
        level: str, 
        message: str, 
        extra: Optional[Dict[str, Any]] = None
    ):
        """
        Log an event with optional extra metadata
        
        :param level: Logging level
        :param message: Log message
        :param extra: Additional metadata
        """
        log_method = getattr(self.logger, level.lower())
        
        if extra:
            log_method(f"{message} - Extra: {json.dumps(extra)}")
        else:
            log_method(message)

    def log_user_action(
        self, 
        user_id: int, 
        username: str, 
        action: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log user-specific actions
        
        :param user_id: Telegram User ID
        :param username: Telegram Username
        :param action: Action performed
        :param details: Additional action details
        """
        log_data = {
            'user_id': user_id,
            'username': username,
            'action': action,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            log_data.update(details)
        
        self.log_event('INFO', f"User Action: {action}", log_data)

    def log_download_event(
        self, 
        user_id: int, 
        file_id: str, 
        status: str, 
        extra: Optional[Dict[str, Any]] = None
    ):
        """
        Log download-specific events
        
        :param user_id: Telegram User ID
        :param file_id: Unique file identifier
        :param status: Download status
        :param extra: Additional download details
        """
        log_data = {
            'user_id': user_id,
            'file_id': file_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        
        if extra:
            log_data.update(extra)
        
        self.log_event('INFO', f"Download Event: {status}", log_data)

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Global exception handler
        
        :param exc_type: Exception type
        :param exc_value: Exception value
        :param exc_traceback: Traceback object
        """
        # Log the full traceback
        error_message = "Uncaught Exception"
        full_traceback = traceback.format_exception(
            exc_type, exc_value, exc_traceback
        )
        
        self.logger.critical(
            f"{error_message}\n{''.join(full_traceback)}"
        )
        
        # Optional: You can add additional error handling here
        # For example, sending an alert to admin, etc.

def main():
    """
    Example usage and testing of AdvancedLogger
    """
    # Initialize logger ```python
    logger = AdvancedLogger()

    # Log some events
    logger.log_event('INFO', 'Application started')
    logger.log_user_action(user_id=123456789, username='test_user', action='download_file', details={'file_id': 'abc123'})
    logger.log_download_event(user_id=123456789, file_id='abc123', status='success')

    try:
        # Simulate an error
        1 / 0
    except Exception as e:
        logger.handle_exception(*sys.exc_info())

if __name__ == '__main__':
    main()

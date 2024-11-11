"""
User Database Backup Script

This script provides functionality to:
- Backup user data to various formats
- Encrypt backup files
- Manage backup retention
- Log backup operations
"""

import os
import sys
import json
import csv
import sqlite3
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import your user model and database configuration
from config.database import Base, engine
from app.models.user import User  # Adjust import based on your project structure

class UserBackupManager:
    def __init__(
        self, 
        backup_dir: Optional[Path] = None, 
        retention_days: int = 30,
        encryption_key: Optional[str] = None
    ):
        """
        Initialize UserBackupManager
        
        :param backup_dir: Directory to store backups
        :param retention_days: Number of days to retain backup files
        :param encryption_key: Optional encryption key for backup files
        """
        self.backup_dir = backup_dir or BASE_DIR / 'backups' / 'users'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.retention_days = retention_days
        self.logger = self._setup_logger()
        
        # Setup encryption
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _setup_logger(self) -> logging.Logger:
        """
        Setup logging for backup operations
        
        :return: Configured logger
        """
        logger = logging.getLogger('UserBackupManager')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(
            self.backup_dir.parent / 'user_backup.log'
        )
        file_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _generate_backup_filename(self, format: str) -> Path:
        """
        Generate unique backup filename
        
        :param format: Backup file format
        :return: Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"user_backup_{timestamp}.{format}"
        return self.backup_dir / filename
    
    def _cleanup_old_backups(self):
        """
        Remove backup files older than retention period
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for backup_file in self.backup_dir.glob('*'):
            if backup_file.is_file():
                file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    backup_file.unlink()
                    self.logger.info(f"Deleted old backup: {backup_file}")
    
    def backup_to_json(self, users: List[User]) -> Path:
        """
        Backup users to JSON format
        
        :param users: List of user objects
        :return: Path to backup file
        """
        backup_file = self._generate_backup_filename('json')
        
        # Convert users to dict
        user_data = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                # Add more fields as needed
            } for user in users
        ]
        
        # Encrypt JSON data
        json_data = json.dumps(user_data, indent=2)
        encrypted_data = self.fernet.encrypt(json_data.encode())
        
        with open(backup_file, 'wb') as f:
            f.write(encrypted_data)
        
        self.logger.info(f"JSON backup created: {backup_file}")
        return backup_file
    
    def backup_to_csv(self, users: List[User]) -> Path:
        """
        Backup users to CSV format
        
        :param users: List of user objects
        :return: Path to backup file
        """
        backup_file = self._generate_backup_filename('csv')
        
        # Prepare CSV data
        csv_data = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                # Add more fields as needed
            } for user in users
        ]
        
        # Write to CSV
        with open(backup_file, 'w', newline='') as csvfile:
            if csv_data:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
        
        # Encrypt CSV
        with open(backup_file, 'rb') as f:
            csv_content = f.read()
        
        encrypted_data = self.fernet.encrypt(csv_content)
        
        with open(backup_file, 'wb') as f:
            f.write(encrypted_data)
        
        self.logger.info(f"CSV backup created: {backup_file}")
        return backup_file
    
    def backup_to_sqlite(self, users: List[User]) -> Path:
        """
        Backup users to SQLite database
        
        :param users: List of user objects
        :return: Path to backup file
        """
        backup_file = self._generate_backup_filename('sqlite')
        
        # Create SQLite connection
        conn = sqlite3.connect(backup_file)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                email TEXT,
                created_at DATETIME
            )
        ''')
        
        # Insert user data
        for user in users:
            cursor.execute('''
                INSERT INTO users (id, username, email, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                user.id, 
                user.username, 
                user.email, 
                user.created_at.isoformat() if user.created_at else None
            ))
        
        conn.commit()
        conn.close()
        
        # Encrypt SQLite database
        with open(backup_file, 'rb') as f:
            sqlite_content = f.read()
        
        encrypted_data = self.fernet.encrypt(sqlite_content)
        
        with open(backup_file, 'wb') as f:
            f.write(encrypted_data)
        
        self.logger.info(f"SQLite backup created: {backup_file}")
        return backup_file
    
    def perform_backup(self, backup_formats: List[str] = ['json', 'csv', 'sqlite']):
        """
        Perform comprehensive user database backup
        
        :param backup_formats: List of backup formats to generate
        """
        try:
            # Create database session
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Fetch all users
            users = session.query(User).all()
            
            # # Perform backups in specified formats
            for format in backup_formats:
                if format == 'json':
                    self.backup_to_json(users)
                elif format == 'csv':
                    self.backup_to_csv(users)
                elif format == 'sqlite':
                    self.backup_to_sqlite(users)
                else:
                    self.logger.warning(f"Unsupported backup format: {format}")
            
            # Cleanup old backups
            self._cleanup_old_backups()
            session.close()
            self.logger.info("Backup process completed successfully.")
        except Exception as e:
            self.logger.error(f"An error occurred during backup: {e}")
            sys.exit(1)

def main():
    """
    Main entry point for the backup script.
    """
    backup_manager = UserBackupManager()
    backup_manager.perform_backup()

if __name__ == "__main__":
    main()

"""
SQLite Storage Backend
"""
import sqlite3
import json
from typing import Any, Dict, Optional
from .base_storage import BaseStorage

class SQLiteStorage(BaseStorage):
    def __init__(self, path: str = 'storage.db'):
        """
        Initialize SQLite storage
        
        :param path: Path to SQLite database
        """
        self.path = path
        self._create_table()
    
    def _create_table(self):
        """
        Create storage table if not exists
        """
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS storage (
                    key TEXT PRIMARY KEY,
                    data TEXT
                )
            ''')
            conn.commit()
    
    def save(self, key: str, data:

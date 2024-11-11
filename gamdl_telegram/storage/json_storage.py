"""
JSON-based Storage Backend
"""
import json
import os
from typing import Any, Dict, Optional
from .base_storage import BaseStorage

class JSONStorage(BaseStorage):
    def __init__(self, path: str = 'storage.json'):
        """
        Initialize JSON storage
        
        :param path: Path to JSON file
        """
        self.path = path
        self._ensure_file()
    
    def _ensure_file(self):
        """
        Ensure storage file exists
        """
        if not os.path.exists(self.path):
            with open(self.path, 'w') as f:
                json.dump({}, f)
    
    def save(self, key: str, data: Dict[str, Any]):
        """
        Save data to JSON file
        
        :param key: Unique identifier
        :param data: Data to store
        """
        with open(self.path, 'r+') as f:
            storage = json.load(f)
            storage[key] = data
            f.seek(0)
            json.dump(storage, f, indent=4)
            f.truncate()
    
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from JSON file
        
        :param key: Unique identifier
        :return: Stored data or None
        """
        with open(self.path, 'r') as f:
            storage = json.load(f)
            return storage.get(key)
    
    def delete(self, key: str):
        """
        Delete data from JSON file
        
        :param key: Unique identifier
        """
        with open(self.path, 'r+') as f:
            storage = json.load(f)
            if key in storage:
                del storage[key]
                f.seek(0)
                json.dump(storage, f, indent=4)
                f.truncate()
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in storage
        
        :param key: Unique identifier
        :return: Existence of key
        """
        with open(self.path, 'r') as f:
            storage = json.load(f)
            return key in storage
    
    def list_keys(self) -> list:
        """
        List all keys in storage
        
        :return: List of keys
        """
        with open(self.path, 'r') as f:
            storage = json.load(f)
            return list(storage.keys())

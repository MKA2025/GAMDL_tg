"""
Base Storage Abstract Class
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseStorage(ABC):
    """
    Abstract base class for storage backends
    """
    
    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]):
        """
        Save data to storage
        
        :param key: Unique identifier
        :param data: Data to store
        """
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from storage
        
        :param key: Unique identifier
        :return: Stored data or None
        """
        pass
    
    @abstractmethod
    def delete(self, key: str):
        """
        Delete data from storage
        
        :param key: Unique identifier
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if key exists in storage
        
        :param key: Unique identifier
        :return: Existence of key
        """
        pass
    
    @abstractmethod
    def list_keys(self) -> list:
        """
        List all keys in storage
        
        :return: List of keys
        """
        pass

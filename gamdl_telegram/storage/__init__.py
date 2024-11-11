"""
Storage Module Initialization

This module provides a centralized storage management system with 
multiple storage backends and abstraction layers.
"""

from .base_storage import BaseStorage
from .json_storage import JSONStorage
from .sqlite_storage import SQLiteStorage
from .redis_storage import RedisStorage

__all__ = [
    'BaseStorage',
    'JSONStorage', 
    'SQLiteStorage', 
    'RedisStorage',
    'StorageFactory'
]

class StorageFactory:
    """
    Storage Factory for creating and managing different storage backends
    """
    
    @staticmethod
    def create_storage(
        storage_type: str = 'json', 
        **kwargs
    ) -> BaseStorage:
        """
        Create a storage backend based on the specified type
        
        :param storage_type: Type of storage backend
        :param kwargs: Additional configuration parameters
        :return: Storage backend instance
        """
        storage_backends = {
            'json': JSONStorage,
            'sqlite': SQLiteStorage,
            'redis': RedisStorage
        }
        
        if storage_type.lower() not in storage_backends:
            raise ValueError(f"Unsupported storage type: {storage_type}")
        
        storage_class = storage_backends[storage_type.lower()]
        return storage_class(**kwargs)
    
    @staticmethod
    def get_recommended_storage() -> str:
        """
        Determine the recommended storage backend based on system capabilities
        
        :return: Recommended storage type
        """
        try:
            import redis
            return 'redis'
        except ImportError:
            try:
                import sqlite3
                return 'sqlite'
            except ImportError:
                return 'json'

def configure_storage(
    storage_type: str = None, 
    **kwargs
) -> BaseStorage:
    """
    Configure and initialize storage backend
    
    :param storage_type: Desired storage type
    :param kwargs: Additional configuration parameters
    :return: Configured storage backend
    """
    if storage_type is None:
        storage_type = StorageFactory.get_recommended_storage()
    
    return StorageFactory.create_storage(
        storage_type, 
        **kwargs
    )

# Example configuration and usage
def main():
    """
    Demonstrate storage configuration and usage
    """
    # Basic JSON Storage
    json_storage = configure_storage('json', path='user_data.json')
    
    # SQLite Storage
    sqlite_storage = configure_storage('sqlite', path='user_database.db')
    
    # Redis Storage (if Redis is installed)
    try:
        redis_storage = configure_storage('redis', 
            host='localhost', 
            port=6379, 
            db=0
        )
    except ValueError as e:
        print(f"Redis storage not available: {e}")
    
    # Example usage
    user_data = {
        'user_id': 123456789,
        'username': 'example_user',
        'downloads': 5
    }
    
    # Store data
    json_storage.save('user_123', user_data)
    sqlite_storage.save('user_123', user_data)

if __name__ == '__main__':
    main()

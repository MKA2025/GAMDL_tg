"""
Redis Storage Backend for Distributed and High-Performance Storage

Provides a robust Redis-based storage solution with advanced features
and error handling.
"""

import json
import pickle
from typing import Any, Dict, Optional, Union

import redis
from redis.exceptions import RedisError, ConnectionError, AuthenticationError

from .base_storage import BaseStorage

class RedisStorage(BaseStorage):
    """
    Redis-based storage backend with advanced configuration and features
    """
    
    def __init__(
        self, 
        host: str = 'localhost', 
        port: int = 6379, 
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = 'gamdl:',
        serializer: str = 'json',
        socket_timeout: int = 5,
        max_connections: int = 10
    ):
        """
        Initialize Redis storage backend
        
        :param host: Redis server host
        :param port: Redis server port
        :param db: Redis database number
        :param password: Redis authentication password
        :param prefix: Key prefix for namespacing
        :param serializer: Data serialization method
        :param socket_timeout: Connection timeout
        :param max_connections: Maximum connection pool size
        """
        self.prefix = prefix
        self.serializer = serializer
        
        try:
            # Configure Redis connection pool
            self.pool = redis.ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                socket_timeout=socket_timeout,
                max_connections=max_connections
            )
            
            # Create Redis client
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Verify connection
            self.client.ping()
        
        except (ConnectionError, AuthenticationError) as e:
            raise RuntimeError(f"Redis connection failed: {e}")
    
    def _serialize_data(self, data: Any) -> bytes:
        """
        Serialize data based on selected method
        
        :param data: Data to serialize
        :return: Serialized data
        """
        if self.serializer == 'json':
            return json.dumps(data).encode('utf-8')
        elif self.serializer == 'pickle':
            return pickle.dumps(data)
        else:
            raise ValueError(f"Unsupported serializer: {self.serializer}")
    
    def _deserialize_data(self, data: bytes) -> Any:
        """
        Deserialize data based on selected method
        
        :param data: Serialized data
        :return: Deserialized data
        """
        if not data:
            return None
        
        try:
            if self.serializer == 'json':
                return json.loads(data.decode('utf-8'))
            elif self.serializer == 'pickle':
                return pickle.loads(data)
        except (json.JSONDecodeError, pickle.PickleError) as e:
            raise ValueError(f"Deserialization error: {e}")
    
    def save(
        self, 
        key: str, 
        data: Union[Dict[str, Any], Any], 
        expire: Optional[int] = None
    ):
        """
        Save data to Redis with optional expiration
        
        :param key: Unique identifier
        :param data: Data to store
        :param expire: Expiration time in seconds
        """
        try:
            full_key = f"{self.prefix}{key}"
            serialized_data = self._serialize_data(data)
            
            if expire:
                self.client.setex(full_key, expire, serialized_data)
            else:
                self.client.set(full_key, serialized_data)
        
        except RedisError as e:
            raise RuntimeError(f"Redis save error: {e}")
    
    def load(self, key: str) -> Optional[Any]:
        """
        Load data from Redis
        
        :param key: Unique identifier
        :return: Stored data or None
        """
        try:
            full_key = f"{self.prefix}{key}"
            data = self.client.get(full_key)
            return self._deserialize_data(data)
        
        except RedisError as e:
            raise RuntimeError(f"Redis load error: {e}")
    
    def delete(self, key: str):
        """
        Delete data from Redis
        
        :param key: Unique identifier
        """
        try:
            full_key = f"{self.prefix}{key}"
            self.client.delete(full_key)
        
        except RedisError as e:
            raise RuntimeError(f"Redis delete error: {e}")
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis
        
        :param key: Unique identifier
        :return: Existence of key
        """
        try:
            full_key = f"{self.prefix}{key}"
            return bool(self.client.exists(full_key))
        
        except RedisError as e:
            raise RuntimeError(f"Redis exists check error: {e}")
    
    def list_keys(self, pattern: str = '*') -> list:
        """
        List keys matching a pattern
        
        :param pattern: Key pattern (default: all keys)
        :return: List of keys
        """
        try:
            full_pattern = f"{self.prefix}{pattern}"
            return [
                key.decode('utf-8').replace(self.prefix, '') 
                for key in self.client.keys(full_pattern)
            ]
        
        except RedisError as e:
            raise RuntimeError(f"Redis list keys error: {e}")
    
    def increment(
        self, 
        key: str, 
        amount: int = 1, 
        expire: Optional[int] = None
    ) -> int:
        """
        Increment a numeric value
        
        :param key: Unique identifier
        :param amount: Increment amount
        :param expire: Optional expiration
        :return: New value
        """
        try:
            full_key = f"{self.prefix}{key}"
            new_value = self.client.incrby(full_key, amount)
            
            if expire and new_value == amount:
                self.client.expire(full_key, expire)
            
            return new_value
        
        except RedisError as e:
            raise RuntimeError(f"Redis increment error: {e}")
    
    def set_hash(
        self, 
        key: str, 
        field: str, 
        value: Any, 
        expire: Optional[int] = None
    ):
        """
        Set a field in a hash
        
        :param key: Hash key
        :param field: Hash field
        :param value: Field value
        :param expire: Optional expiration
        """
        try:
            full_key = f"{self.prefix}{key}"
            serialized_value = self._serialize_data(value)
            self.client.hset(full_key, field, serialized_value)
            
            if expire:
                self.client.expire(full_key, expire)
        
        except RedisError as e:
            raise RuntimeError(f"Redis hash set error: {e}")
    
    def get_hash(
        self, 
        key: str, 
        field: str
    ) -> Optional[Any]:
        """
        Get a field from a hash
        
        :param key: Hash key
        :param field: Hash field
        :return: Field value
        """
        try:
            full_key = f"{self.prefix}{key}"
            value = self.client.hget(full_key, field)
            return self._deserialize_data(value)
        
        except RedisError as e:
            raise RuntimeError(f"Redis hash get error: {e}")

def main():
    """
    Example usage and testing of RedisStorage
    """
    try:
        # Initialize Redis storage
        redis_storage = RedisStorage(
            host='localhost',
            port=6379,
            db=0,
            prefix='gamdl_test:'
         )
        
        # Save data
        redis_storage.save('user_123', {'username': 'example_user', 'downloads': 5}, expire=3600)
        
        # Load data
        user_data = redis_storage.load('user_123')
        print(f"Loaded user data: {user_data}")
        
        # Check existence
        exists = redis_storage.exists('user_123')
        print(f"User  exists: {exists}")
        
        # Increment a value
        downloads = redis_storage.increment('user_123:downloads', amount=1)
        print(f"Updated downloads: {downloads}")
        
        # Delete data
        redis_storage.delete('user_123')
        print("User  data deleted.")
        
    except RuntimeError as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()

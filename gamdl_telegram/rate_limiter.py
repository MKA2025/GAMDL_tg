"""
Rate Limiter Module for GaDL Telegram Bot

This module provides advanced rate limiting and throttling mechanisms
to prevent abuse and ensure fair usage of the bot's resources.
"""

import time
import logging
from typing import Dict, Any, Optional
from functools import wraps
from threading import Lock

# Configure logging
logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Advanced Rate Limiting System
    
    Supports multiple rate limiting strategies:
    1. Global Request Limit
    2. Per-User Request Limit
    3. IP-based Throttling
    4. Burst Request Handling
    """
    
    def __init__(
        self, 
        global_limit: int = 100,  # Global requests per time window
        global_window: int = 60,  # Global time window in seconds
        user_limit: int = 10,     # Per-user requests per time window
        user_window: int = 60,    # Per-user time window in seconds
        ip_limit: int = 50,       # Per-IP requests per time window
        ip_window: int = 60       # Per-IP time window in seconds
    ):
        """
        Initialize Rate Limiter
        
        :param global_limit: Maximum global requests
        :param global_window: Global time window
        :param user_limit: Maximum per-user requests
        :param user_window: Per-user time window
        :param ip_limit: Maximum per-IP requests
        :param ip_window: Per-IP time window
        """
        self.global_limit = global_limit
        self.global_window = global_window
        self.user_limit = user_limit
        self.user_window = user_window
        self.ip_limit = ip_limit
        self.ip_window = ip_window
        
        # Thread-safe data structures
        self.global_requests: Dict[float, int] = {}
        self.user_requests: Dict[int, Dict[float, int]] = {}
        self.ip_requests: Dict[str, Dict[float, int]] = {}
        
        # Locks for thread safety
        self.global_lock = Lock()
        self.user_lock = Lock()
        self.ip_lock = Lock()

    def _cleanup_expired_requests(
        self, 
        request_dict: Dict, 
        window: int, 
        current_time: float
    ) -> Dict:
        """
        Remove expired requests from tracking dictionary
        
        :param request_dict: Dictionary of requests
        :param window: Time window
        :param current_time: Current timestamp
        :return: Cleaned request dictionary
        """
        return {
            timestamp: count 
            for timestamp, count in request_dict.items() 
            if current_time - timestamp <= window
        }

    def is_allowed(
        self, 
        user_id: Optional[int] = None, 
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Check if request is allowed based on rate limits
        
        :param user_id: Telegram User ID
        :param ip_address: Client IP Address
        :return: Whether request is allowed
        """
        current_time = time.time()
        
        # Global Rate Limiting
        with self.global_lock:
            self.global_requests = self._cleanup_expired_requests(
                self.global_requests, 
                self.global_window, 
                current_time
            )
            
            if sum(self.global_requests.values()) >= self.global_limit:
                logger.warning("Global rate limit exceeded")
                return False
            
            # Increment global requests
            self.global_requests[current_time] = self.global_requests.get(current_time, 0) + 1
        
        # User-specific Rate Limiting
        if user_id is not None:
            with self.user_lock:
                # Initialize user requests if not exists
                if user_id not in self.user_requests:
                    self.user_requests[user_id] = {}
                
                user_reqs = self.user_requests[user_id]
                user_reqs = self._cleanup_expired_requests(
                    user_reqs, 
                    self.user_window, 
                    current_time
                )
                
                if sum(user_reqs.values()) >= self.user_limit:
                    logger.warning(f"Rate limit exceeded for user {user_id}")
                    return False
                
                # Increment user requests
                user_reqs[current_time] = user_reqs.get(current_time, 0) + 1
                self.user_requests[user_id] = user_reqs
        
        # IP-based Rate Limiting
        if ip_address is not None:
            with self.ip_lock:
                # Initialize IP requests if not exists
                if ip_address not in self.ip_requests:
                    self.ip_requests[ip_address] = {}
                
                ip_reqs = self.ip_requests[ip_address]
                ip_reqs = self._cleanup_expired_requests(
                    ip_reqs, 
                    self.ip_window, 
                    current_time
                )
                
                if sum(ip_reqs.values()) >= self.ip_limit:
                    logger.warning(f"Rate limit exceeded for IP {ip_address}")
                    return False
                
                # Increment IP requests
                ip_reqs[current_time] = ip_reqs.get(current_time, 0) + 1
                self.ip_requests[ip_address] = ip_reqs
        
        return True

    def rate_limit(
        self, 
        limit: int = 10, 
        window: int = 60
    ):
        """
        Decorator for rate limiting function calls
        
        :param limit: Maximum requests in time window
        :param window: Time window in seconds
        :return: Decorated function
        """
        def decorator(func):
            requests: Dict[float, int] = {}
            lock = Lock()
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                current_time = time.time()
                
                with lock:
                    # Clean up expired requests
                    nonlocal requests
                    requests = {
                        timestamp: count 
                        for timestamp, count in requests.items() 
                        if current_time - timestamp <= window
                    }
                    
                    # Check rate limit
                    if sum(requests.values()) >= limit:
                        logger.warning(f"Function rate limit exceeded: {func.__name__}")
                        raise RuntimeError("Rate limit exceeded")
                    
                    # Increment request count
                    requests[current_time] = requests.get(current_time, 0) + 1
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator

    def get_wait_time(
        self, 
        user_id: Optional[int] = None, 
        ip_address: Optional[str] = None
    ) -> float:
        """
        Calculate wait time before next allowed request
        
        :param user_id: Telegram User ID
        :param ip_address: Client IP Address
        :return: Wait time in seconds
        """
        current_time = time.time()
        max_wait = 0
        
        # Check global wait time
        global_requests = self._cleanup_expired_requests(
            self.global_requests.copy(), 
            self.global_window, 
            current_time
        )
        if sum(global_requests.values()) >= self.global_limit:
            max_wait = max(max_wait, self.global_window)
        
        # Check user wait time
        if user_id is not None and user_id in self.user_requests:
            user_reqs = self._cleanup_expired_requests(
                self.user_requests[user_id].copy(), 
                self.user_window, 
                current_time
            )
            if sum(user_reqs.values()) >= self.user_limit:
                max_wait = max(max_wait, self.user_window)
        
        # Check IP wait time
        if ip_address is not None and ip_address in self.ip_requests:
            ip_reqs = self._cleanup_expired_requests(
                self.ip_requests[ip_address].copy(), 
                self.ip_window, 
                current_time
            )
            if sum(ip_reqs.values()) >= self.ip_limit:
                max_wait = max(max_wait, self.ip_window)
        
        return max_wait

def main():
    """
    Example usage and testing of RateLimiter
    """
    rate_limiter = RateLimiter()
    
    user_id = 123456789
    ip_address = "192.168.1.1"
    
    # Simulate requests
    for i in range(15):
        if rate_limiter.is_allowed(user_id=user_id, ip_address=ip_address):
            print(f"Request {i + 1} allowed")
        else:
            print(f"Request {i + 1} denied")
            wait_time = rate_limiter.get_wait_time(user_id=user_id, ip_address=ip_address)
            print(f"Please wait for {wait_time:.2f} seconds before retrying")
            time.sleep(wait_time + 1)  # Wait for the required time before retrying

if __name__ == '__main__':
    main()

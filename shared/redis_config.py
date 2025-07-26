import redis
import json
import os
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class RedisConfig:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.password = os.getenv("REDIS_PASSWORD", None)
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.client = None
        
    def connect(self):
        """Establish connection to Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def set_cache(self, key: str, value: Any, ttl: int = 3600):
        """Set cache with TTL (Time To Live)"""
        try:
            if not self.client:
                self.connect()
            
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            self.client.setex(key, ttl, serialized_value)
            logger.debug(f"Cache set for key: {key}")
        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache by key"""
        try:
            if not self.client:
                self.connect()
            
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Failed to get cache for key {key}: {e}")
            return None
    
    def delete_cache(self, key: str):
        """Delete cache by key"""
        try:
            if not self.client:
                self.connect()
            
            self.client.delete(key)
            logger.debug(f"Cache deleted for key: {key}")
        except Exception as e:
            logger.error(f"Failed to delete cache for key {key}: {e}")
    
    def set_session(self, session_id: str, user_data: dict, ttl: int = 86400):
        """Set user session (24 hours default TTL)"""
        self.set_cache(f"session:{session_id}", user_data, ttl)
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get user session"""
        return self.get_cache(f"session:{session_id}")
    
    def delete_session(self, session_id: str):
        """Delete user session"""
        self.delete_cache(f"session:{session_id}")

# Global instance
redis_client = RedisConfig() 
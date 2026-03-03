"""Redis caching service for API responses."""
import json
import logging
from typing import Optional, Any
import redis
from config.settings import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client instance."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=True
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis cache client initialized")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            _redis_client = None
    return _redis_client


class CacheService:
    """Service for caching API responses in Redis."""

    # Cache TTLs in seconds
    PUBLIC_JOBS_TTL = 6 * 60 * 60  # 6 hours
    PUBLIC_FILTERS_TTL = 12 * 60 * 60  # 12 hours (filters change less frequently)
    
    def __init__(self):
        self.client = get_redis_client()
    
    def _make_key(self, prefix: str, *args) -> str:
        """Create a cache key from prefix and arguments."""
        parts = [prefix] + [str(a) for a in args]
        return ":".join(parts)
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self.client:
            return None
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set a value in cache with TTL."""
        if not self.client:
            return False
        try:
            self.client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if not self.client:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def get_public_jobs(self, limit: int) -> Optional[dict]:
        """Get cached public jobs response."""
        key = self._make_key("public_jobs", f"limit_{limit}")
        return self.get(key)
    
    def set_public_jobs(self, limit: int, data: dict) -> bool:
        """Cache public jobs response for 6 hours."""
        key = self._make_key("public_jobs", f"limit_{limit}")
        return self.set(key, data, self.PUBLIC_JOBS_TTL)
    
    def invalidate_public_jobs(self) -> bool:
        """Invalidate all public jobs cache entries."""
        if not self.client:
            return False
        try:
            # Find and delete all public_jobs keys
            keys = self.client.keys("public_jobs:*")
            if keys:
                self.client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} public_jobs cache entries")
            return True
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            return False

    def get_public_filters(self) -> Optional[dict]:
        """Get cached public filters response."""
        key = self._make_key("public_filters")
        return self.get(key)

    def set_public_filters(self, data: dict) -> bool:
        """Cache public filters response for 12 hours."""
        key = self._make_key("public_filters")
        return self.set(key, data, self.PUBLIC_FILTERS_TTL)

    def invalidate_public_filters(self) -> bool:
        """Invalidate public filters cache."""
        key = self._make_key("public_filters")
        return self.delete(key)


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create cache service singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

"""Redis caching module."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, TypeVar, Generic

import redis.asyncio as redis

from atlas.core.config import get_settings


T = TypeVar("T")


class Cache(Generic[T]):
    """Redis-based cache with type hints."""
    
    def __init__(
        self,
        prefix: str = "atlas",
        default_ttl: int = 300,
    ):
        """Initialize cache.
        
        Args:
            prefix: Key prefix for namespacing
            default_ttl: Default TTL in seconds
        """
        self.prefix = prefix
        self.default_ttl = default_ttl
        self._client: redis.Redis | None = None
    
    async def get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            settings = get_settings()
            self._client = redis.from_url(
                settings.redis.url,
                db=settings.redis.db,
                password=settings.redis.password,
                max_connections=settings.redis.max_connections,
                socket_timeout=settings.redis.socket_timeout,
                socket_connect_timeout=settings.redis.socket_connect_timeout,
                decode_responses=True,
            )
        return self._client
    
    def _make_key(self, key: str) -> str:
        """Create namespaced key."""
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str) -> T | None:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        client = await self.get_client()
        full_key = self._make_key(key)
        
        value = await client.get(full_key)
        
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (None for default)
            
        Returns:
            True if successful
        """
        client = await self.get_client()
        full_key = self._make_key(key)
        
        if ttl is None:
            ttl = self.default_ttl
        
        if not isinstance(value, str):
            value = json.dumps(value)
        
        return await client.set(full_key, value, ex=ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        client = await self.get_client()
        full_key = self._make_key(key)
        
        result = await client.delete(full_key)
        return result > 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        client = await self.get_client()
        full_key = self._make_key(key)
        
        return await client.exists(full_key) > 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on key.
        
        Args:
            key: Cache key
            ttl: TTL in seconds
            
        Returns:
            True if TTL was set
        """
        client = await self.get_client()
        full_key = self._make_key(key)
        
        return await client.expire(full_key, ttl)
    
    async def ttl(self, key: str) -> int:
        """Get TTL on key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        client = await self.get_client()
        full_key = self._make_key(key)
        
        return await client.ttl(full_key)
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value.
        
        Args:
            key: Cache key
            amount: Amount to increment
            
        Returns:
            New value
        """
        client = await self.get_client()
        full_key = self._make_key(key)
        
        return await client.incrby(full_key, amount)
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement numeric value.
        
        Args:
            key: Cache key
            amount: Amount to decrement
            
        Returns:
            New value
        """
        client = await self.get_client()
        full_key = self._make_key(key)
        
        return await client.decrby(full_key, amount)
    
    async def get_many(self, *keys: str) -> dict[str, T | None]:
        """Get multiple values.
        
        Args:
            *keys: Cache keys
            
        Returns:
            Dict of key -> value
        """
        client = await self.get_client()
        full_keys = [self._make_key(k) for k in keys]
        
        values = await client.mget(full_keys)
        
        result = {}
        for key, value in zip(keys, values):
            if value is None:
                result[key] = None
            else:
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
        
        return result
    
    async def set_many(self, mapping: dict[str, Any], ttl: int | None = None) -> bool:
        """Set multiple values.
        
        Args:
            mapping: Dict of key -> value
            ttl: TTL in seconds
            
        Returns:
            True if successful
        """
        client = await self.get_client()
        pipe = client.pipeline()
        
        for key, value in mapping.items():
            full_key = self._make_key(key)
            if not isinstance(value, str):
                value = json.dumps(value)
            pipe.set(full_key, value, ex=ttl or self.default_ttl)
        
        await pipe.execute()
        return True
    
    async def delete_many(self, *keys: str) -> int:
        """Delete multiple keys.
        
        Args:
            *keys: Cache keys
            
        Returns:
            Number of keys deleted
        """
        client = await self.get_client()
        full_keys = [self._make_key(k) for k in keys]
        
        return await client.delete(*full_keys)
    
    async def clear(self) -> int:
        """Clear all keys with prefix.
        
        Returns:
            Number of keys deleted
        """
        client = await self.get_client()
        pattern = f"{self.prefix}:*"
        
        cursor = 0
        deleted = 0
        
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            if keys:
                deleted += await client.delete(*keys)
            if cursor == 0:
                break
        
        return deleted
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


# Global cache instances
agent_cache = Cache[dict]("atlas:agents", default_ttl=60)
workflow_cache = Cache[dict]("atlas:workflows", default_ttl=300)
memory_cache = Cache[dict]("atlas:memory", default_ttl=600)
session_cache = Cache[dict]("atlas:sessions", default_ttl=3600)


async def get_cache_stats() -> dict[str, Any]:
    """Get cache statistics.
    
    Returns:
        Dict with cache stats
    """
    cache = Cache("atlas")
    client = await cache.get_client()
    
    info = await client.info("stats")
    
    return {
        "connected": True,
        "hits": info.get("keyspace_hits", 0),
        "misses": info.get("keyspace_misses", 0),
        "memory_used": info.get("used_memory_human", "N/A"),
        "connected_clients": info.get("connected_clients", 0),
    }

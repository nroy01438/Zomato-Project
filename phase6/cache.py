"""
Caching Layer (Redis/Memcached)

Provides high-performance caching with Redis/Memcached support,
cache warming, invalidation strategies, and performance monitoring.
"""

import asyncio
import json
import logging
import time
import pickle
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib

# Try to import Redis, fallback to in-memory cache
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available, using in-memory cache")

# Try to import Memcached, fallback to in-memory cache
try:
    import pymemcache
    MEMCACHED_AVAILABLE = True
except ImportError:
    MEMCACHED_AVAILABLE = False
    logging.warning("Memcached not available, using in-memory cache")


class CacheBackend(Enum):
    """Supported cache backends"""
    REDIS = "redis"
    MEMCACHED = "memcached"
    MEMORY = "memory"


@dataclass
class CacheConfig:
    """Cache configuration"""
    backend: CacheBackend = CacheBackend.MEMORY
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 10
    default_ttl: int = 300  # 5 minutes
    key_prefix: str = "restaurant_app:"
    serialization: str = "json"  # "json" or "pickle"


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    ttl: int
    created_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    avg_access_time_ms: float = 0.0


class CacheManager:
    """Production-ready cache manager with multiple backend support"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.metrics = CacheMetrics()
        
        # Initialize backend
        self.backend = None
        self._initialize_backend()
        
        # In-memory fallback cache
        self._memory_cache: Dict[str, CacheEntry] = {}
        
        # Cache warming tasks
        self._warming_tasks: List[asyncio.Task] = []
    
    def _initialize_backend(self):
        """Initialize the cache backend"""
        
        try:
            if self.config.backend == CacheBackend.REDIS and REDIS_AVAILABLE:
                self.backend = redis.Redis(
                    host=self.config.host,
                    port=self.config.port,
                    db=self.config.db,
                    password=self.config.password,
                    decode_responses=False,  # Handle bytes for pickle support
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    max_connections=self.config.max_connections
                )
                
                # Test connection
                self.backend.ping()
                self.logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
                
            elif self.config.backend == CacheBackend.MEMCACHED and MEMCACHED_AVAILABLE:
                from pymemcache.client.base import Client
                
                self.backend = Client(
                    (self.config.host, self.config.port),
                    connect_timeout=5,
                    timeout=5,
                    no_delay=True
                )
                
                # Test connection
                self.backend.set('test_key', 'test_value', 1)
                self.backend.delete('test_key')
                self.logger.info(f"Connected to Memcached at {self.config.host}:{self.config.port}")
                
            else:
                self.logger.warning(f"Backend {self.config.backend} not available, using in-memory cache")
                self.config.backend = CacheBackend.MEMORY
                
        except Exception as e:
            self.logger.error(f"Failed to initialize cache backend {self.config.backend}: {e}")
            self.config.backend = CacheBackend.MEMORY
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage"""
        
        if self.config.serialization == "pickle":
            return pickle.dumps(value)
        else:
            return json.dumps(value, default=str).encode('utf-8')
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        
        if self.config.serialization == "pickle":
            return pickle.loads(data)
        else:
            return json.loads(data.decode('utf-8'))
    
    def _make_key(self, key: str) -> str:
        """Create full cache key with prefix"""
        return f"{self.config.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        
        start_time = time.time()
        full_key = self._make_key(key)
        
        try:
            if self.config.backend == CacheBackend.MEMORY:
                # In-memory cache
                entry = self._memory_cache.get(full_key)
                if entry and (entry.created_at + timedelta(seconds=entry.ttl)) > datetime.now():
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()
                    self.metrics.hits += 1
                    return entry.value
                else:
                    self.metrics.misses += 1
                    return None
                    
            elif self.config.backend == CacheBackend.REDIS:
                # Redis cache
                data = self.backend.get(full_key)
                if data:
                    self.metrics.hits += 1
                    return self._deserialize_value(data)
                else:
                    self.metrics.misses += 1
                    return None
                    
            elif self.config.backend == CacheBackend.MEMCACHED:
                # Memcached cache
                data = self.backend.get(full_key)
                if data:
                    self.metrics.hits += 1
                    return self._deserialize_value(data)
                else:
                    self.metrics.misses += 1
                    return None
                    
        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            self.metrics.misses += 1
        
        finally:
            # Update metrics
            access_time = (time.time() - start_time) * 1000
            self._update_avg_access_time(access_time)
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        
        if ttl is None:
            ttl = self.config.default_ttl
        
        full_key = self._make_key(key)
        serialized_value = self._serialize_value(value)
        
        try:
            if self.config.backend == CacheBackend.MEMORY:
                # In-memory cache
                entry = CacheEntry(
                    key=full_key,
                    value=value,
                    ttl=ttl,
                    created_at=datetime.now(),
                    size_bytes=len(serialized_value)
                )
                self._memory_cache[full_key] = entry
                self._cleanup_expired_memory_cache()
                
            elif self.config.backend == CacheBackend.REDIS:
                # Redis cache
                self.backend.setex(full_key, ttl, serialized_value)
                
            elif self.config.backend == CacheBackend.MEMCACHED:
                # Memcached cache
                self.backend.set(full_key, serialized_value, expire=ttl)
            
            self.metrics.sets += 1
            self.metrics.total_size_bytes += len(serialized_value)
            return True
            
        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        
        full_key = self._make_key(key)
        
        try:
            if self.config.backend == CacheBackend.MEMORY:
                # In-memory cache
                if full_key in self._memory_cache:
                    del self._memory_cache[full_key]
                    
            elif self.config.backend == CacheBackend.REDIS:
                # Redis cache
                self.backend.delete(full_key)
                
            elif self.config.backend == CacheBackend.MEMCACHED:
                # Memcached cache
                self.backend.delete(full_key)
            
            self.metrics.deletes += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries"""
        
        cleared_count = 0
        
        try:
            if pattern:
                # Clear entries matching pattern
                full_pattern = self._make_key(pattern)
                
                if self.config.backend == CacheBackend.MEMORY:
                    # In-memory cache
                    keys_to_delete = [k for k in self._memory_cache.keys() if pattern in k]
                    for key in keys_to_delete:
                        del self._memory_cache[key]
                        cleared_count += 1
                        
                elif self.config.backend == CacheBackend.REDIS:
                    # Redis cache
                    keys = self.backend.keys(full_pattern)
                    if keys:
                        cleared_count = len(keys)
                        self.backend.delete(*keys)
                        
                elif self.config.backend == CacheBackend.MEMCACHED:
                    # Memcached doesn't support pattern matching, need to track keys
                    pass
            else:
                # Clear all cache
                if self.config.backend == CacheBackend.MEMORY:
                    cleared_count = len(self._memory_cache)
                    self._memory_cache.clear()
                    
                elif self.config.backend == CacheBackend.REDIS:
                    # Clear only keys with our prefix
                    keys = self.backend.keys(f"{self.config.key_prefix}*")
                    if keys:
                        cleared_count = len(keys)
                        self.backend.delete(*keys)
                        
                elif self.config.backend == CacheBackend.MEMCACHED:
                    # Memcached doesn't support clearing by prefix
                    cleared_count = 0
            
            self.logger.info(f"Cleared {cleared_count} cache entries")
            return cleared_count
            
        except Exception as e:
            self.logger.error(f"Cache clear error: {e}")
            return 0
    
    def _cleanup_expired_memory_cache(self):
        """Clean up expired entries from in-memory cache"""
        
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self._memory_cache.items():
            if (entry.created_at + timedelta(seconds=entry.ttl)) <= now:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._memory_cache[key]
            self.metrics.evictions += 1
    
    def _update_avg_access_time(self, access_time_ms: float):
        """Update average access time metric"""
        
        total_requests = self.metrics.hits + self.metrics.misses
        if total_requests > 0:
            self.metrics.avg_access_time_ms = (
                (self.metrics.avg_access_time_ms * (total_requests - 1) + access_time_ms) / total_requests
            )
    
    # Cache warming and preloading
    async def warm_cache(self, warm_data: Dict[str, Any], ttl: Optional[int] = None):
        """Warm cache with predefined data"""
        
        self.logger.info(f"Warming cache with {len(warm_data)} entries")
        
        tasks = []
        for key, value in warm_data.items():
            task = asyncio.create_task(self.set(key, value, ttl))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("Cache warming completed")
    
    async def preload_restaurant_data(self, restaurant_data: List[Dict[str, Any]]):
        """Preload frequently accessed restaurant data"""
        
        warm_data = {}
        
        for restaurant in restaurant_data:
            # Cache individual restaurant
            key = f"restaurant:{restaurant['name']}:{restaurant['location']}"
            warm_data[key] = restaurant
            
            # Cache by location
            location_key = f"restaurants:location:{restaurant['location']}"
            if location_key not in warm_data:
                warm_data[location_key] = []
            warm_data[location_key].append(restaurant)
        
        await self.warm_cache(warm_data, ttl=3600)  # 1 hour
    
    # Cache invalidation strategies
    async def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        
        return await self.clear(pattern)
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a specific user"""
        
        patterns = [
            f"user:{user_id}:*",
            f"recommendations:user:{user_id}:*",
            f"preferences:user:{user_id}"
        ]
        
        total_cleared = 0
        for pattern in patterns:
            cleared = await self.clear(pattern)
            total_cleared += cleared
        
        self.logger.info(f"Invalidated {total_cleared} cache entries for user {user_id}")
        return total_cleared
    
    async def invalidate_location_cache(self, location: str):
        """Invalidate cache entries for a specific location"""
        
        patterns = [
            f"restaurants:location:{location}",
            f"recommendations:location:{location}:*",
            f"search:location:{location}:*"
        ]
        
        total_cleared = 0
        for pattern in patterns:
            cleared = await self.clear(pattern)
            total_cleared += cleared
        
        self.logger.info(f"Invalidated {total_cleared} cache entries for location {location}")
        return total_cleared
    
    # Cache analytics and monitoring
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        
        total_requests = self.metrics.hits + self.metrics.misses
        hit_rate = self.metrics.hits / total_requests if total_requests > 0 else 0
        
        return {
            'backend': self.config.backend.value,
            'hits': self.metrics.hits,
            'misses': self.metrics.misses,
            'sets': self.metrics.sets,
            'deletes': self.metrics.deletes,
            'evictions': self.metrics.evictions,
            'hit_rate': hit_rate,
            'total_size_bytes': self.metrics.total_size_bytes,
            'avg_access_time_ms': self.metrics.avg_access_time_ms,
            'memory_entries': len(self._memory_cache) if self.config.backend == CacheBackend.MEMORY else None
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics"""
        
        stats = self.get_metrics()
        
        # Add backend-specific stats
        if self.config.backend == CacheBackend.REDIS and self.backend:
            try:
                redis_info = self.backend.info()
                stats.update({
                    'redis_memory_used': redis_info.get('used_memory', 0),
                    'redis_connected_clients': redis_info.get('connected_clients', 0),
                    'redis_keyspace_hits': redis_info.get('keyspace_hits', 0),
                    'redis_keyspace_misses': redis_info.get('keyspace_misses', 0)
                })
            except Exception as e:
                self.logger.warning(f"Could not get Redis stats: {e}")
        
        elif self.config.backend == CacheBackend.MEMORY:
            # In-memory cache stats
            total_entries = len(self._memory_cache)
            expired_entries = sum(
                1 for entry in self._memory_cache.values()
                if (entry.created_at + timedelta(seconds=entry.ttl)) <= datetime.now()
            )
            
            stats.update({
                'memory_total_entries': total_entries,
                'memory_expired_entries': expired_entries,
                'memory_active_entries': total_entries - expired_entries
            })
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        
        health_status = {
            'healthy': True,
            'backend': self.config.backend.value,
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        try:
            # Test basic set/get operation
            test_key = f"health_check_{int(time.time())}"
            test_value = {"test": True, "timestamp": time.time()}
            
            # Set test value
            set_success = await self.set(test_key, test_value, 10)
            health_status['checks']['set_operation'] = set_success
            
            # Get test value
            retrieved_value = await self.get(test_key)
            get_success = retrieved_value == test_value
            health_status['checks']['get_operation'] = get_success
            
            # Clean up test value
            await self.delete(test_key)
            
            # Check hit rate
            metrics = self.get_metrics()
            health_status['checks']['hit_rate'] = metrics['hit_rate']
            
            # Overall health
            health_status['healthy'] = all([
                set_success,
                get_success,
                metrics['hit_rate'] >= 0  # Basic sanity check
            ])
            
        except Exception as e:
            health_status['healthy'] = False
            health_status['error'] = str(e)
            self.logger.error(f"Cache health check failed: {e}")
        
        return health_status
    
    # Cache utilities
    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate a consistent cache key from arguments"""
        
        # Create a deterministic key from arguments
        key_parts = []
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))
        
        # Add keyword arguments (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (dict, list)):
                key_parts.append(f"{k}={json.dumps(v, sort_keys=True)}")
            else:
                key_parts.append(f"{k}={v}")
        
        # Create hash for long keys
        key_string = ":".join(key_parts)
        if len(key_string) > 200:
            key_string = hashlib.md5(key_string.encode()).hexdigest()
        
        return key_string
    
    async def get_or_set(self, key: str, factory: Callable[[], Any], 
                        ttl: Optional[int] = None) -> Any:
        """Get value from cache or set using factory function"""
        
        # Try to get from cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Generate value using factory
        try:
            value = await factory() if asyncio.iscoroutinefunction(factory) else factory()
            
            # Cache the generated value
            await self.set(key, value, ttl)
            
            return value
            
        except Exception as e:
            self.logger.error(f"Factory function failed for key {key}: {e}")
            raise
    
    def close(self):
        """Close cache connections"""
        
        try:
            if self.config.backend == CacheBackend.REDIS and self.backend:
                self.backend.close()
                self.logger.info("Redis connection closed")
                
            elif self.config.backend == CacheBackend.MEMCACHED and self.backend:
                self.backend.close()
                self.logger.info("Memcached connection closed")
                
        except Exception as e:
            self.logger.error(f"Error closing cache connection: {e}")
        
        # Cancel warming tasks
        for task in self._warming_tasks:
            if not task.done():
                task.cancel()
        
        self.logger.info("Cache manager closed")


# Cache decorators for easy integration
def cache_result(ttl: int = 300, key_prefix: str = "", cache_manager: Optional[CacheManager] = None):
    """Decorator to cache function results"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Use provided cache manager or create a default one
            cache = cache_manager or CacheManager(CacheConfig())
            
            # Generate cache key
            func_key = f"{key_prefix}{func.__name__}"
            cache_key = cache.generate_cache_key(func_key, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_user_data(ttl: int = 3600, cache_manager: Optional[CacheManager] = None):
    """Decorator to cache user-specific data"""
    
    def decorator(func):
        async def wrapper(user_id: str, *args, **kwargs):
            cache = cache_manager or CacheManager(CacheConfig())
            
            cache_key = f"user:{user_id}:{func.__name__}"
            
            return await cache.get_or_set(
                cache_key,
                lambda: func(user_id, *args, **kwargs),
                ttl
            )
        
        return wrapper
    return decorator

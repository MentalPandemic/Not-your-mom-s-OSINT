import json
import asyncio
import hashlib
from typing import Any, Optional, Union, Callable, Dict
from datetime import datetime, timedelta
import pickle
import logging

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Custom exception for cache operations"""
    pass


class CacheManager:
    """Unified cache manager supporting both Redis and in-memory caching"""
    
    def __init__(self, config: dict):
        self.config = config
        self.use_redis = config.get('use_redis', False)
        self.default_ttl = config.get('default_ttl', 3600)
        self.enabled = config.get('enabled', True)
        
        # In-memory cache storage
        self._memory_cache = {}
        self._cache_lock = asyncio.Lock()
        
        # Redis connection (lazy initialization)
        self._redis_client = None
        self._redis_connected = False
        
        self._cleanup_task = None
        
    async def initialize(self):
        """Initialize cache manager"""
        await self._setup_redis()
        await self._start_cleanup_task()
        logger.info(f"Cache manager initialized with Redis: {self.use_redis}")
    
    async def _setup_redis(self):
        """Setup Redis connection if configured"""
        if not self.use_redis:
            return
        
        try:
            import redis.asyncio as redis
            
            redis_config = {
                'host': self.config.get('redis_host', 'localhost'),
                'port': self.config.get('redis_port', 6379),
                'db': self.config.get('redis_db', 0),
                'decode_responses': False
            }
            
            if self.config.get('redis_password'):
                redis_config['password'] = self.config['redis_password']
            
            self._redis_client = redis.Redis(**redis_config)
            
            # Test connection
            await self._redis_client.ping()
            self._redis_connected = True
            logger.info("Redis cache connected successfully")
            
        except ImportError:
            logger.warning("Redis library not available, falling back to in-memory cache")
            self.use_redis = False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, falling back to in-memory cache")
            self.use_redis = False
    
    async def _start_cleanup_task(self):
        """Start background cleanup task for in-memory cache"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_entries())
    
    async def _cleanup_expired_entries(self):
        """Periodically remove expired cache entries"""
        cleanup_interval = 300  # 5 minutes
        
        while True:
            try:
                await asyncio.sleep(cleanup_interval)
                await self._remove_expired_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    async def _remove_expired_entries(self):
        """Remove expired entries from in-memory cache"""
        async with self._cache_lock:
            current_time = datetime.utcnow()
            expired_keys = []
            
            for key, (value, expiry_time) in self._memory_cache.items():
                if current_time > expiry_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._memory_cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _generate_cache_key(self, key: Union[str, bytes]) -> str:
        """Generate cache key with prefix"""
        prefix = self.config.get('key_prefix', 'username_enum:')
        
        if isinstance(key, str):
            return f"{prefix}{key}"
        else:
            return f"{prefix}{key.decode('utf-8')}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Try JSON first (more efficient)
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                return json.dumps(value).encode('utf-8')
            else:
                # Fall back to pickle for complex objects
                return pickle.dumps(value)
        except Exception as e:
            raise CacheError(f"Serialization error: {e}")
    
    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                return pickle.loads(value)
        except Exception as e:
            raise CacheError(f"Deserialization error: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            cache_key = self._generate_cache_key(key)
            
            if self.use_redis and self._redis_connected:
                value = await self._redis_client.get(cache_key)
                if value:
                    return self._deserialize_value(value)
                return None
            else:
                # In-memory cache
                async with self._cache_lock:
                    if cache_key in self._memory_cache:
                        value, expiry_time = self._memory_cache[cache_key]
                        if datetime.utcnow() <= expiry_time:
                            return value
                        else:
                            # Remove expired entry
                            del self._memory_cache[cache_key]
                
                return None
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self.enabled:
            return False
        
        try:
            cache_key = self._generate_cache_key(key)
            serialized_value = self._serialize_value(value)
            ttl = ttl or self.default_ttl
            expiry_time = datetime.utcnow() + timedelta(seconds=ttl)
            
            if self.use_redis and self._redis_connected:
                await self._redis_client.setex(cache_key, ttl, serialized_value)
            else:
                # In-memory cache
                async with self._cache_lock:
                    self._memory_cache[cache_key] = (value, expiry_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.enabled:
            return False
        
        try:
            cache_key = self._generate_cache_key(key)
            
            if self.use_redis and self._redis_connected:
                await self._redis_client.delete(cache_key)
            else:
                async with self._cache_lock:
                    self._memory_cache.pop(cache_key, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.enabled:
            return False
        
        try:
            cache_key = self._generate_cache_key(key)
            
            if self.use_redis and self._redis_connected:
                return bool(await self._redis_client.exists(cache_key))
            else:
                async with self._cache_lock:
                    if cache_key in self._memory_cache:
                        value, expiry_time = self._memory_cache[cache_key]
                        if datetime.utcnow() <= expiry_time:
                            return True
                        else:
                            del self._memory_cache[cache_key]
                
                return False
                
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries matching pattern"""
        if not self.enabled:
            return 0
        
        try:
            if self.use_redis and self._redis_connected:
                if pattern:
                    pattern = self._generate_cache_key(pattern)
                    keys = await self._redis_client.keys(pattern)
                    if keys:
                        await self._redis_client.delete(*keys)
                        return len(keys)
                else:
                    prefix = self._generate_cache_key('*')
                    keys = await self._redis_client.keys(prefix)
                    if keys:
                        await self._redis_client.delete(*keys)
                        return len(keys)
            else:
                async with self._cache_lock:
                    if pattern:
                        prefix = self._generate_cache_key(pattern)
                        keys_to_delete = [
                            key for key in self._memory_cache.keys() 
                            if key.startswith(prefix.replace('*', ''))
                        ]
                        for key in keys_to_delete:
                            del self._memory_cache[key]
                        return len(keys_to_delete)
                    else:
                        count = len(self._memory_cache)
                        self._memory_cache.clear()
                        return count
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            'enabled': self.enabled,
            'using_redis': self.use_redis and self._redis_connected,
            'default_ttl': self.default_ttl
        }
        
        try:
            if self.use_redis and self._redis_connected:
                info = await self._redis_client.info()
                stats.update({
                    'total_keys': await self._redis_client.dbsize(),
                    'used_memory_human': info.get('used_memory_human', 'N/A'),
                    'uptime_in_seconds': info.get('uptime_in_seconds', 0),
                    'connected_clients': info.get('connected_clients', 0)
                })
            else:
                async with self._cache_lock:
                    stats.update({
                        'total_keys': len(self._memory_cache),
                        'estimate_memory_usage': 'N/A (in-memory)'
                    })
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
        
        return stats
    
    def get_cache_key_for_search(
        self,
        search_type: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        tolerance: Optional[str] = None
    ) -> str:
        """Generate cache key for search parameters"""
        key_parts = [search_type]
        
        if username:
            key_parts.append(f"u:{username.lower()}")
        
        if email:
            key_parts.append(f"e:{email.lower()}")
        
        if phone:
            key_parts.append(f"p:{phone}")
        
        if tolerance:
            key_parts.append(f"t:{tolerance}")
        
        # Create hash of key parts for consistent length
        key_string = ':'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def close(self):
        """Close cache manager and cleanup resources"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._redis_client:
            await self._redis_client.close()
        
        self._memory_cache.clear()
        logger.info("Cache manager closed")
    
    def cached(self, ttl: Optional[int] = None, key_prefix: str = ''):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)
                
                # Generate cache key from function name and arguments
                key_data = f"{func.__name__}:{args}:{kwargs}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
                
                if key_prefix:
                    cache_key = f"{key_prefix}:{cache_key}"
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
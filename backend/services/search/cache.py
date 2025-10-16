"""Search result caching system with Redis and in-memory fallback."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

from .types import SearchResult


class SearchCache:
    """Cache for search results with TTL support."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Cache configuration
        self.enabled = self.config.get('enabled', True)
        self.default_ttl = self.config.get('default_ttl', 3600)  # 1 hour default
        self.max_cache_size = self.config.get('max_cache_size', 1000)
        self.enable_redis = self.config.get('enable_redis', False)
        self.redis_config = self.config.get('redis', {})

        # In-memory cache as fallback
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

        # Redis client (optional)
        self._redis_client = None
        if self.enable_redis:
            self._init_redis_client()

        self.logger.info(f"SearchCache initialized: enabled={self.enabled}, redis={self.enable_redis}")

    def _init_redis_client(self):
        """Initialize Redis client if available."""
        try:
            import redis

            host = self.redis_config.get('host', 'localhost')
            port = self.redis_config.get('port', 6379)
            db = self.redis_config.get('db', 0)
            password = self.redis_config.get('password')

            self._redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            self._redis_client.ping()
            self.logger.info(f"Redis cache connected: {host}:{port}/db{db}")

        except ImportError:
            self.logger.warning("Redis not available, falling back to in-memory cache")
            self.enable_redis = False
        except Exception as e:
            self.logger.error(f"Redis connection failed: {e}")
            self.enable_redis = False

    def _generate_cache_key(self, query: str, max_results: int, provider: str) -> str:
        """Generate a unique cache key for the search parameters."""
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()

        # Create hash of query + parameters
        cache_string = f"{normalized_query}|{max_results}|{provider}"
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()

    def _serialize_results(self, results: List[SearchResult]) -> str:
        """Serialize search results for caching."""
        serializable = []
        for result in results:
            serializable.append({
                'title': result.title,
                'url': result.url,
                'snippet': result.snippet,
                'source': result.source,
                'content': result.content,
                'relevance_score': getattr(result, 'relevance_score', None),
            })

        return json.dumps(serializable, ensure_ascii=False)

    def _deserialize_results(self, data: str) -> List[SearchResult]:
        """Deserialize search results from cache."""
        try:
            serializable = json.loads(data)
            results = []

            for item in serializable:
                result = SearchResult(
                    title=item['title'],
                    url=item['url'],
                    snippet=item['snippet'],
                    source=item['source'],
                    content=item.get('content'),
                )

                # Restore relevance score if present
                if 'relevance_score' in item and item['relevance_score'] is not None:
                    result.relevance_score = item['relevance_score']

                results.append(result)

            return results

        except Exception as e:
            self.logger.warning(f"Failed to deserialize cached results: {e}")
            return []

    def get(self, query: str, max_results: int, provider: str) -> Optional[List[SearchResult]]:
        """Retrieve cached search results."""
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(query, max_results, provider)

        try:
            # Try Redis first if available
            if self._redis_client:
                cached_data = self._redis_client.get(cache_key)
                if cached_data:
                    # Check TTL
                    ttl = self._redis_client.ttl(cache_key)
                    if ttl > 0:  # Still valid
                        return self._deserialize_results(cached_data)

            # Fallback to memory cache
            if cache_key in self._memory_cache:
                cache_entry = self._memory_cache[cache_key]
                if time.time() < cache_entry['expires_at']:
                    return self._deserialize_results(cache_entry['data'])
                else:
                    # Expired, remove from cache
                    del self._memory_cache[cache_key]

        except Exception as e:
            self.logger.warning(f"Cache retrieval failed: {e}")

        return None

    def set(self, query: str, max_results: int, provider: str,
            results: List[SearchResult], ttl: Optional[int] = None) -> None:
        """Cache search results."""
        if not self.enabled or not results:
            return

        cache_key = self._generate_cache_key(query, max_results, provider)
        ttl = ttl or self.default_ttl

        try:
            serialized_data = self._serialize_results(results)

            # Cache in Redis if available
            if self._redis_client:
                self._redis_client.setex(cache_key, ttl, serialized_data)

            # Also cache in memory (for faster access and fallback)
            self._memory_cache[cache_key] = {
                'data': serialized_data,
                'expires_at': time.time() + ttl,
                'created_at': time.time(),
            }

            # Manage memory cache size
            self._cleanup_memory_cache()

        except Exception as e:
            self.logger.warning(f"Cache storage failed: {e}")

    def _cleanup_memory_cache(self) -> None:
        """Remove expired entries and enforce size limits."""
        current_time = time.time()

        # Remove expired entries
        expired_keys = [
            key for key, entry in self._memory_cache.items()
            if current_time >= entry['expires_at']
        ]

        for key in expired_keys:
            del self._memory_cache[key]

        # If still too large, remove oldest entries
        if len(self._memory_cache) > self.max_cache_size:
            # Sort by creation time (oldest first)
            sorted_entries = sorted(
                self._memory_cache.items(),
                key=lambda x: x[1]['created_at']
            )

            # Remove oldest entries until under limit
            keys_to_remove = len(self._memory_cache) - self.max_cache_size
            for i in range(min(keys_to_remove, len(sorted_entries))):
                del self._memory_cache[sorted_entries[i][0]]

    def clear(self) -> None:
        """Clear all cached results."""
        try:
            if self._redis_client:
                self._redis_client.flushdb()
            self._memory_cache.clear()
            self.logger.info("Search cache cleared")
        except Exception as e:
            self.logger.warning(f"Failed to clear cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        redis_count = 0
        if self._redis_client:
            try:
                redis_count = self._redis_client.dbsize()
            except Exception:
                pass

        return {
            'enabled': self.enabled,
            'redis_enabled': self.enable_redis,
            'memory_cache_size': len(self._memory_cache),
            'redis_cache_size': redis_count,
            'max_cache_size': self.max_cache_size,
            'default_ttl': self.default_ttl,
        }

    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate cache entries matching a pattern."""
        if not self.enabled:
            return

        try:
            # Invalidate memory cache
            keys_to_remove = [
                key for key in self._memory_cache.keys()
                if pattern.lower() in key.lower()
            ]

            for key in keys_to_remove:
                del self._memory_cache[key]

            # Invalidate Redis cache (if supported)
            if self._redis_client:
                # Note: Redis doesn't have a direct pattern delete,
                # but we can use SCAN to find matching keys
                keys = self._redis_client.scan_iter(match=f"*{pattern.lower()}*")
                if keys:
                    self._redis_client.delete(*keys)

            self.logger.info(f"Invalidated {len(keys_to_remove)} cache entries matching pattern: {pattern}")

        except Exception as e:
            self.logger.warning(f"Cache invalidation failed: {e}")


def create_search_cache(config: Optional[Dict] = None) -> SearchCache:
    """Factory function to create a SearchCache instance."""
    return SearchCache(config)

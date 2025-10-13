"""
Cache manager for verse data persistence.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

from pathlib import Path
from typing import Optional
import diskcache

from ..models.verse import Verse, VerseReference
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Manages caching of verse data using diskcache."""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_days: int = 30):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache storage
            ttl_days: Time-to-live for cache entries in days
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".verse_inserter" / "cache"
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = diskcache.Cache(str(cache_dir))
        self.ttl_seconds = ttl_days * 24 * 60 * 60
        logger.info(f"Cache initialized at {cache_dir}")
    
    def get(self, reference: VerseReference) -> Optional[Verse]:
        """
        Get verse from cache.
        
        Args:
            reference: Verse reference to look up
            
        Returns:
            Cached verse or None if not found
        """
        key = self._make_key(reference)
        try:
            verse = self.cache.get(key)
            if verse:
                logger.debug(f"Cache hit: {reference.canonical_reference}")
            return verse
        except Exception as e:
            logger.warning(f"Cache read error for {key}: {e}")
            return None
    
    def set(self, reference: VerseReference, verse: Verse) -> None:
        """
        Store verse in cache.
        
        Args:
            reference: Verse reference
            verse: Verse data to cache
        """
        key = self._make_key(reference)
        try:
            self.cache.set(key, verse, expire=self.ttl_seconds)
            logger.debug(f"Cache set: {reference.canonical_reference}")
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")
    
    def clear(self) -> None:
        """Clear all cached data."""
        try:
            self.cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def _make_key(self, reference: VerseReference) -> str:
        """Generate cache key from verse reference."""
        return f"{reference.translation.code}:{reference.canonical_reference}"
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "volume": self.cache.volume(),
        }
    
    def __del__(self):
        """Cleanup cache on deletion."""
        try:
            self.cache.close()
        except Exception:
            pass

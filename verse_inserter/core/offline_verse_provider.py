"""
Offline verse provider with API fallback.

Provides verse lookup that checks offline database first,
then falls back to API if verse not found locally.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

from typing import Optional

from verse_inserter.api.bible_api_client import BibleAPIClient
from verse_inserter.core.offline_database import OfflineBibleDatabase
from verse_inserter.core.cache_manager import CacheManager
from verse_inserter.models.verse import Verse, VerseReference
from verse_inserter.utils.logger import get_logger

logger = get_logger(__name__)


class OfflineVerseProvider:
    """
    Provide verses from offline database with API fallback.

    Lookup priority:
    1. Offline database
    2. Cache
    3. API (then cache result)
    """

    def __init__(
        self,
        api_client: BibleAPIClient,
        offline_db: Optional[OfflineBibleDatabase] = None,
        cache_manager: Optional[CacheManager] = None,
        prefer_offline: bool = True,
    ):
        """
        Initialize offline verse provider.

        Args:
            api_client: Bible API client for fallback
            offline_db: Offline database (defaults to new instance)
            cache_manager: Cache manager for API results
            prefer_offline: Whether to prefer offline lookups
        """
        self.api_client = api_client
        self.offline_db = offline_db or OfflineBibleDatabase()
        self.cache_manager = cache_manager
        self.prefer_offline = prefer_offline

        # Statistics
        self._offline_hits = 0
        self._cache_hits = 0
        self._api_calls = 0

    async def fetch_verse(self, reference: VerseReference) -> Optional[Verse]:
        """
        Fetch a verse from offline database or API.

        Args:
            reference: Verse reference to fetch

        Returns:
            Verse if found
        """
        # Try offline database first if enabled
        if self.prefer_offline:
            verse = self._try_offline(reference)
            if verse:
                self._offline_hits += 1
                logger.debug(f"Offline hit: {reference.canonical}")
                return verse

        # Try cache next
        if self.cache_manager:
            cached = self.cache_manager.get(reference)
            if cached:
                self._cache_hits += 1
                logger.debug(f"Cache hit: {reference.canonical}")
                return cached

        # Fallback to API
        try:
            verse = await self.api_client.fetch_verse(reference)
            self._api_calls += 1
            logger.debug(f"API call: {reference.canonical}")

            # Cache the result
            if verse and self.cache_manager:
                self.cache_manager.set(reference, verse)

            # Store in offline database for future use
            if verse and self.prefer_offline:
                try:
                    self.offline_db.add_verse(reference.translation, verse)
                except Exception as e:
                    logger.warning(f"Failed to store verse offline: {e}")

            return verse

        except Exception as e:
            logger.error(f"Failed to fetch verse {reference.canonical}: {e}")
            return None

    def _try_offline(self, reference: VerseReference) -> Optional[Verse]:
        """
        Try to get verse from offline database.

        Args:
            reference: Verse reference

        Returns:
            Verse if found in offline database
        """
        try:
            # Check if translation exists
            if not self.offline_db.has_translation(reference.translation):
                return None

            # Try to get verse or verse range
            if reference.end_verse:
                return self.offline_db.get_verse_range(reference)
            else:
                return self.offline_db.get_verse(reference)

        except Exception as e:
            logger.warning(f"Offline lookup failed: {e}")
            return None

    def get_statistics(self) -> dict:
        """
        Get usage statistics.

        Returns:
            Dictionary with statistics
        """
        total = self._offline_hits + self._cache_hits + self._api_calls

        return {
            "total_requests": total,
            "offline_hits": self._offline_hits,
            "cache_hits": self._cache_hits,
            "api_calls": self._api_calls,
            "offline_percentage": (
                (self._offline_hits / total * 100) if total > 0 else 0
            ),
            "cache_percentage": (
                (self._cache_hits / total * 100) if total > 0 else 0
            ),
            "api_percentage": (
                (self._api_calls / total * 100) if total > 0 else 0
            ),
        }

    def reset_statistics(self) -> None:
        """Reset usage statistics."""
        self._offline_hits = 0
        self._cache_hits = 0
        self._api_calls = 0

    def is_translation_available_offline(
        self,
        reference: VerseReference,
    ) -> bool:
        """
        Check if a translation is available offline.

        Args:
            reference: Reference with translation to check

        Returns:
            True if translation is downloaded
        """
        return self.offline_db.has_translation(reference.translation)

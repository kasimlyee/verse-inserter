"""
Unit tests for cache manager.

Tests cache functionality including storage, retrieval, and expiration.
"""

import pytest
from pathlib import Path

from verse_inserter.core.cache_manager import CacheManager
from verse_inserter.models.verse import Verse, VerseReference, TranslationType


class TestCacheManager:
    """Tests for CacheManager class."""

    @pytest.fixture
    def cache_manager(self, clean_cache):
        """Create a cache manager with clean cache directory."""
        return CacheManager(cache_dir=clean_cache, ttl_days=30)

    def test_initialization(self, clean_cache):
        """Test cache manager initialization."""
        manager = CacheManager(cache_dir=clean_cache)
        assert manager.cache is not None
        assert manager.ttl_seconds == 30 * 24 * 60 * 60

    def test_set_and_get_verse(self, cache_manager, sample_verse_reference, sample_verse):
        """Test storing and retrieving a verse."""
        cache_manager.set(sample_verse_reference, sample_verse)

        retrieved = cache_manager.get(sample_verse_reference)
        assert retrieved is not None
        assert retrieved.reference.canonical_reference == sample_verse.reference.canonical_reference
        assert retrieved.text == sample_verse.text

    def test_get_nonexistent_verse(self, cache_manager, sample_verse_reference):
        """Test retrieving a non-existent verse."""
        retrieved = cache_manager.get(sample_verse_reference)
        assert retrieved is None

    def test_cache_key_includes_translation(self, cache_manager):
        """Test that cache keys differentiate by translation."""
        ref_niv = VerseReference(book="John", chapter=3, start_verse=16, translation=TranslationType.NIV)
        ref_kjv = VerseReference(book="John", chapter=3, start_verse=16, translation=TranslationType.KJV)

        verse_niv = Verse(reference=ref_niv, text="NIV text", translation=TranslationType.NIV)
        verse_kjv = Verse(reference=ref_kjv, text="KJV text", translation=TranslationType.KJV)

        cache_manager.set(ref_niv, verse_niv)
        cache_manager.set(ref_kjv, verse_kjv)

        retrieved_niv = cache_manager.get(ref_niv)
        retrieved_kjv = cache_manager.get(ref_kjv)

        assert retrieved_niv.text == "NIV text"
        assert retrieved_kjv.text == "KJV text"

    def test_clear_cache(self, cache_manager, sample_verse_reference, sample_verse):
        """Test clearing the cache."""
        cache_manager.set(sample_verse_reference, sample_verse)
        assert cache_manager.get(sample_verse_reference) is not None

        cache_manager.clear()
        assert cache_manager.get(sample_verse_reference) is None

    def test_get_stats(self, cache_manager, sample_verse_reference, sample_verse):
        """Test cache statistics."""
        cache_manager.set(sample_verse_reference, sample_verse)

        stats = cache_manager.get_stats()
        assert "size" in stats
        assert "volume" in stats
        assert stats["size"] > 0

    def test_make_key(self, cache_manager):
        """Test cache key generation."""
        ref = VerseReference(book="John", chapter=3, start_verse=16, translation=TranslationType.NIV)

        key = cache_manager._make_key(ref)
        assert "John 3:16" in key
        assert TranslationType.NIV.value in key

    def test_cache_persistence(self, clean_cache):
        """Test that cache persists across manager instances."""
        ref = VerseReference(book="John", chapter=3, start_verse=16)
        verse = Verse(reference=ref, text="Test persistence", translation=TranslationType.NIV)

        # Create first manager and store verse
        manager1 = CacheManager(cache_dir=clean_cache)
        manager1.set(ref, verse)

        # Create second manager and retrieve verse
        manager2 = CacheManager(cache_dir=clean_cache)
        retrieved = manager2.get(ref)

        assert retrieved is not None
        assert retrieved.text == "Test persistence"

    def test_ttl_configuration(self, clean_cache):
        """Test TTL configuration."""
        manager_7days = CacheManager(cache_dir=clean_cache, ttl_days=7)
        assert manager_7days.ttl_seconds == 7 * 24 * 60 * 60

        manager_90days = CacheManager(cache_dir=clean_cache, ttl_days=90)
        assert manager_90days.ttl_seconds == 90 * 24 * 60 * 60

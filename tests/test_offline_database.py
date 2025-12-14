"""
Unit tests for offline Bible database.

Tests SQLAlchemy-based offline verse storage and retrieval.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from verse_inserter.core.offline_database import (
    OfflineBibleDatabase,
    TranslationInfo,
)
from verse_inserter.models.verse import Verse, VerseReference, TranslationType


class TestOfflineBibleDatabase:
    """Tests for offline Bible database."""

    @pytest.fixture
    def db_path(self, tmp_path):
        """Create temporary database path."""
        return tmp_path / "test_bible.db"

    @pytest.fixture
    def database(self, db_path):
        """Create database instance."""
        db = OfflineBibleDatabase(db_path=db_path)
        yield db
        # Cleanup
        db.close()  # Close database connections
        import time
        time.sleep(0.1)  # Brief delay for Windows file release
        if db_path.exists():
            try:
                db_path.unlink()
            except PermissionError:
                pass  # Ignore if still locked

    def test_initialization(self, db_path):
        """Test database initialization."""
        db = OfflineBibleDatabase(db_path=db_path)

        assert db.db_path == db_path
        assert db.db_path.exists()
        assert db.engine is not None
        assert db.SessionLocal is not None

    def test_add_translation(self, database):
        """Test adding a translation."""
        trans_id = database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
            language="English",
        )

        assert trans_id > 0
        assert database.has_translation(TranslationType.KJV)

    def test_add_translation_duplicate(self, database):
        """Test adding duplicate translation returns same ID."""
        trans_id1 = database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        trans_id2 = database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        assert trans_id1 == trans_id2

    def test_add_verse(self, database):
        """Test adding a verse."""
        # Add translation first
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        # Add verse
        reference = VerseReference.parse("John 3:16", TranslationType.KJV)
        verse = Verse(
            reference=reference,
            text="For God so loved the world...",
            translation=TranslationType.KJV,
        )

        result = database.add_verse(TranslationType.KJV, verse)

        assert result is True

    def test_add_verse_without_translation(self, database):
        """Test adding verse without translation fails."""
        reference = VerseReference.parse("John 3:16", TranslationType.KJV)
        verse = Verse(
            reference=reference,
            text="For God so loved the world...",
            translation=TranslationType.KJV,
        )

        result = database.add_verse(TranslationType.KJV, verse)

        assert result is False

    def test_add_verse_update_existing(self, database):
        """Test updating existing verse."""
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        reference = VerseReference.parse("John 3:16", TranslationType.KJV)

        # Add first version
        verse1 = Verse(
            reference=reference,
            text="Original text",
            translation=TranslationType.KJV,
        )
        database.add_verse(TranslationType.KJV, verse1)

        # Update with new text
        verse2 = Verse(
            reference=reference,
            text="Updated text",
            translation=TranslationType.KJV,
        )
        database.add_verse(TranslationType.KJV, verse2)

        # Verify updated
        retrieved = database.get_verse(reference)
        assert retrieved.text == "Updated text"

    def test_add_verses_bulk(self, database):
        """Test bulk verse insertion."""
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        verses = [
            Verse(
                reference=VerseReference.parse("John 3:16", TranslationType.KJV),
                text="For God so loved...",
                translation=TranslationType.KJV,
            ),
            Verse(
                reference=VerseReference.parse("John 3:17", TranslationType.KJV),
                text="For God sent not...",
                translation=TranslationType.KJV,
            ),
            Verse(
                reference=VerseReference.parse("Psalm 23:1", TranslationType.KJV),
                text="The Lord is my shepherd...",
                translation=TranslationType.KJV,
            ),
        ]

        count = database.add_verses_bulk(TranslationType.KJV, verses)

        assert count == 3

    def test_add_verses_bulk_empty(self, database):
        """Test bulk insert with empty list."""
        count = database.add_verses_bulk(TranslationType.KJV, [])

        assert count == 0

    def test_get_verse(self, database):
        """Test retrieving a verse."""
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        reference = VerseReference.parse("John 3:16", TranslationType.KJV)
        verse = Verse(
            reference=reference,
            text="For God so loved the world...",
            translation=TranslationType.KJV,
        )

        database.add_verse(TranslationType.KJV, verse)

        retrieved = database.get_verse(reference)

        assert retrieved is not None
        assert retrieved.text == verse.text
        assert retrieved.reference.canonical_reference == reference.canonical_reference

    def test_get_verse_not_found(self, database):
        """Test getting non-existent verse."""
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        reference = VerseReference.parse("John 3:16", TranslationType.KJV)
        retrieved = database.get_verse(reference)

        assert retrieved is None

    def test_get_verse_range(self, database):
        """Test retrieving verse range."""
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        # Add multiple verses
        verses = [
            Verse(
                reference=VerseReference.parse("John 3:16", TranslationType.KJV),
                text="For God so loved the world,",
                translation=TranslationType.KJV,
            ),
            Verse(
                reference=VerseReference.parse("John 3:17", TranslationType.KJV),
                text="that he gave his only begotten Son,",
                translation=TranslationType.KJV,
            ),
            Verse(
                reference=VerseReference.parse("John 3:18", TranslationType.KJV),
                text="that whosoever believeth in him...",
                translation=TranslationType.KJV,
            ),
        ]

        database.add_verses_bulk(TranslationType.KJV, verses)

        # Get range
        reference = VerseReference(
            book="John",
            chapter=3,
            start_verse=16,
            end_verse=18,
            translation=TranslationType.KJV,
        )

        retrieved = database.get_verse_range(reference)

        assert retrieved is not None
        assert "For God so loved" in retrieved.text
        assert "whosoever believeth" in retrieved.text

    def test_has_translation(self, database):
        """Test checking translation existence."""
        assert not database.has_translation(TranslationType.KJV)

        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        assert database.has_translation(TranslationType.KJV)
        assert not database.has_translation(TranslationType.NIV)

    def test_get_translation_info(self, database):
        """Test getting translation information."""
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
            language="English",
        )

        info = database.get_translation_info(TranslationType.KJV)

        assert info is not None
        assert info.translation == TranslationType.KJV
        assert info.name == "King James Version"
        assert info.abbreviation == "KJV"
        assert info.language == "English"
        assert info.verse_count == 0

    def test_get_translation_info_not_found(self, database):
        """Test getting info for non-existent translation."""
        info = database.get_translation_info(TranslationType.KJV)

        assert info is None

    def test_get_all_translations(self, database):
        """Test getting all translations."""
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        database.add_translation(
            translation=TranslationType.NIV,
            name="New International Version",
        )

        translations = database.get_all_translations()

        assert len(translations) == 2
        abbreviations = [t.abbreviation for t in translations]
        assert "KJV" in abbreviations
        assert "NIV" in abbreviations

    def test_delete_translation(self, database):
        """Test deleting a translation."""
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        # Add some verses
        verse = Verse(
            reference=VerseReference.parse("John 3:16", TranslationType.KJV),
            text="For God so loved...",
            translation=TranslationType.KJV,
        )
        database.add_verse(TranslationType.KJV, verse)

        # Delete translation
        result = database.delete_translation(TranslationType.KJV)

        assert result is True
        assert not database.has_translation(TranslationType.KJV)

        # Verify verses were deleted too
        retrieved = database.get_verse(
            VerseReference.parse("John 3:16", TranslationType.KJV)
        )
        assert retrieved is None

    def test_delete_translation_not_found(self, database):
        """Test deleting non-existent translation."""
        result = database.delete_translation(TranslationType.KJV)

        assert result is False

    def test_get_statistics(self, database):
        """Test getting database statistics."""
        stats = database.get_statistics()

        assert "translation_count" in stats
        assert "verse_count" in stats
        assert "database_size_bytes" in stats
        assert "database_size_mb" in stats
        assert "database_path" in stats

        assert stats["translation_count"] == 0
        assert stats["verse_count"] == 0

        # Add data
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        verse = Verse(
            reference=VerseReference.parse("John 3:16", TranslationType.KJV),
            text="For God so loved...",
            translation=TranslationType.KJV,
        )
        database.add_verse(TranslationType.KJV, verse)

        # Check updated stats
        stats = database.get_statistics()
        assert stats["translation_count"] == 1
        assert stats["verse_count"] == 1

    def test_clear_all(self, database):
        """Test clearing all data."""
        # Add data
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        verse = Verse(
            reference=VerseReference.parse("John 3:16", TranslationType.KJV),
            text="For God so loved...",
            translation=TranslationType.KJV,
        )
        database.add_verse(TranslationType.KJV, verse)

        # Clear all
        database.clear_all()

        # Verify empty
        stats = database.get_statistics()
        assert stats["translation_count"] == 0
        assert stats["verse_count"] == 0

    def test_verse_count_updates(self, database):
        """Test that verse count is updated correctly."""
        database.add_translation(
            translation=TranslationType.KJV,
            name="King James Version",
        )

        # Add verses
        verses = [
            Verse(
                reference=VerseReference.parse(f"John 3:{i}", TranslationType.KJV),
                text=f"Verse {i}",
                translation=TranslationType.KJV,
            )
            for i in range(1, 11)
        ]

        database.add_verses_bulk(TranslationType.KJV, verses)

        # Check verse count
        info = database.get_translation_info(TranslationType.KJV)
        assert info.verse_count == 10

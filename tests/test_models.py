"""
Unit tests for verse data models.

Tests VerseReference, Verse, and Placeholder models including parsing,
validation, and serialization.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from verse_inserter.models.verse import (
    Verse,
    VerseReference,
    TranslationType,
    Placeholder,
)


class TestTranslationType:
    """Tests for TranslationType enum."""

    def test_translation_values(self):
        """Test that translation enums have correct API IDs."""
        assert TranslationType.NIV.value == "de4e12af7f28f599-02"
        assert TranslationType.KJV.value == "de4e12af7f28f599-01"
        assert TranslationType.ESV.value == "f421fe261da7624f-01"

    def test_display_names(self):
        """Test translation display names."""
        assert "New International Version" in TranslationType.NIV.display_name
        assert "King James Version" in TranslationType.KJV.display_name
        assert "(NIV)" in TranslationType.NIV.display_name

    def test_from_display_name(self):
        """Test parsing display names back to enum."""
        assert TranslationType.from_display_name("NIV") == TranslationType.NIV
        assert TranslationType.from_display_name("King James Version") == TranslationType.KJV
        assert TranslationType.from_display_name("niv") == TranslationType.NIV

    def test_from_display_name_invalid(self):
        """Test error handling for invalid translation names."""
        with pytest.raises(ValueError, match="Unsupported translation"):
            TranslationType.from_display_name("INVALID_TRANSLATION")


class TestVerseReference:
    """Tests for VerseReference model."""

    def test_create_simple_reference(self):
        """Test creating a simple verse reference."""
        ref = VerseReference(
            book="John",
            chapter=3,
            start_verse=16,
            translation=TranslationType.NIV
        )
        assert ref.book == "John"
        assert ref.chapter == 3
        assert ref.start_verse == 16
        assert ref.end_verse is None
        assert ref.translation == TranslationType.NIV

    def test_create_verse_range(self):
        """Test creating a verse range reference."""
        ref = VerseReference(
            book="Psalm",
            chapter=23,
            start_verse=1,
            end_verse=6,
            translation=TranslationType.KJV
        )
        assert ref.is_range is True
        assert ref.start_verse == 1
        assert ref.end_verse == 6

    def test_canonical_reference_simple(self):
        """Test canonical reference string generation."""
        ref = VerseReference(book="John", chapter=3, start_verse=16)
        assert ref.canonical_reference == "John 3:16"

    def test_canonical_reference_range(self):
        """Test canonical reference for verse ranges."""
        ref = VerseReference(book="Psalm", chapter=23, start_verse=1, end_verse=3)
        assert ref.canonical_reference == "Psalm 23:1-3"

    def test_parse_simple_reference(self):
        """Test parsing simple verse references."""
        ref = VerseReference.parse("John 3:16")
        assert ref.book == "John"
        assert ref.chapter == 3
        assert ref.start_verse == 16
        assert ref.end_verse is None

    def test_parse_verse_range(self):
        """Test parsing verse ranges."""
        ref = VerseReference.parse("Genesis 1:1-5")
        assert ref.book == "Genesis"
        assert ref.chapter == 1
        assert ref.start_verse == 1
        assert ref.end_verse == 5

    def test_parse_numbered_book(self):
        """Test parsing books with numbers."""
        ref = VerseReference.parse("1 Corinthians 13:4")
        assert ref.book == "1 Corinthians"
        assert ref.chapter == 13
        assert ref.start_verse == 4

    def test_parse_with_extra_spaces(self):
        """Test parsing with extra whitespace."""
        ref = VerseReference.parse("  John   3:16  ")
        assert ref.book.strip() == "John"
        assert ref.chapter == 3

    def test_parse_invalid_format(self):
        """Test error handling for invalid formats."""
        with pytest.raises(ValueError, match="Invalid scripture reference format"):
            VerseReference.parse("Invalid Reference")

        with pytest.raises(ValueError, match="Invalid scripture reference format"):
            VerseReference.parse("John 3")  # Missing verse

    def test_validation_invalid_chapter(self):
        """Test validation of invalid chapter numbers."""
        with pytest.raises(ValidationError):
            VerseReference(book="John", chapter=0, start_verse=16)

        with pytest.raises(ValidationError):
            VerseReference(book="John", chapter=-1, start_verse=16)

    def test_validation_invalid_verse(self):
        """Test validation of invalid verse numbers."""
        with pytest.raises(ValidationError):
            VerseReference(book="John", chapter=3, start_verse=0)

        with pytest.raises(ValidationError):
            VerseReference(book="John", chapter=3, start_verse=200)

    def test_validation_invalid_range(self):
        """Test validation of invalid verse ranges."""
        with pytest.raises(ValidationError, match="end_verse.*must be greater than start_verse"):
            VerseReference(
                book="John",
                chapter=3,
                start_verse=16,
                end_verse=10  # end < start
            )

    def test_immutability(self):
        """Test that VerseReference is immutable."""
        ref = VerseReference(book="John", chapter=3, start_verse=16)
        with pytest.raises(ValidationError):
            ref.chapter = 5

    def test_book_abbreviation(self):
        """Test book abbreviation conversion."""
        assert VerseReference._get_book_abbreviation("John") == "JHN"
        assert VerseReference._get_book_abbreviation("Genesis") == "GEN"
        assert VerseReference._get_book_abbreviation("1 Corinthians") == "1CO"
        assert VerseReference._get_book_abbreviation("Psalm") == "PSA"

    def test_to_api_id(self):
        """Test API ID generation."""
        ref = VerseReference(book="John", chapter=3, start_verse=16)
        assert "JHN.3.16" in ref.to_api_id()

        range_ref = VerseReference(book="John", chapter=3, start_verse=16, end_verse=18)
        api_id = range_ref.to_api_id()
        assert "JHN.3.16" in api_id
        assert "JHN.3.18" in api_id


class TestVerse:
    """Tests for Verse model."""

    def test_create_verse(self, sample_verse_reference):
        """Test creating a verse object."""
        verse = Verse(
            reference=sample_verse_reference,
            text="For God so loved the world...",
            translation=TranslationType.NIV,
            source_api="test_api"
        )
        assert verse.reference == sample_verse_reference
        assert "For God so loved" in verse.text
        assert verse.translation == TranslationType.NIV

    def test_formatted_text(self, sample_verse):
        """Test formatted text generation."""
        formatted = sample_verse.formatted_text
        assert "John 3:16" in formatted
        assert "—" in formatted
        assert sample_verse.text in formatted

    def test_verse_immutability(self, sample_verse):
        """Test that Verse is immutable."""
        with pytest.raises(ValidationError):
            sample_verse.text = "Changed text"

    def test_verse_validation_empty_text(self, sample_verse_reference):
        """Test validation of empty verse text."""
        with pytest.raises(ValidationError):
            Verse(
                reference=sample_verse_reference,
                text="",  # Empty text
                translation=TranslationType.NIV
            )

    def test_verse_validation_long_text(self, sample_verse_reference):
        """Test validation of extremely long text."""
        long_text = "A" * 20000  # Over 10000 char limit
        with pytest.raises(ValidationError):
            Verse(
                reference=sample_verse_reference,
                text=long_text,
                translation=TranslationType.NIV
            )

    def test_to_dict(self, sample_verse):
        """Test verse serialization to dictionary."""
        verse_dict = sample_verse.to_dict()
        assert "reference" in verse_dict
        assert "text" in verse_dict
        assert "translation" in verse_dict
        assert verse_dict["reference"] == "John 3:16"
        assert verse_dict["translation"] == "NIV"

    def test_retrieved_at_auto_generation(self, sample_verse_reference):
        """Test that retrieved_at is automatically set."""
        verse = Verse(
            reference=sample_verse_reference,
            text="Test text",
            translation=TranslationType.NIV
        )
        assert isinstance(verse.retrieved_at, datetime)
        assert verse.retrieved_at <= datetime.now()


class TestPlaceholder:
    """Tests for Placeholder model."""

    def test_create_placeholder(self, sample_verse_reference):
        """Test creating a placeholder object."""
        placeholder = Placeholder(
            raw_text="{{John 3:16}}",
            reference=sample_verse_reference,
            position=100,
            paragraph_index=5
        )
        assert placeholder.raw_text == "{{John 3:16}}"
        assert placeholder.reference == sample_verse_reference
        assert placeholder.position == 100
        assert placeholder.paragraph_index == 5
        assert placeholder.status == Placeholder.Status.PENDING

    def test_placeholder_status_update(self, sample_verse_reference):
        """Test updating placeholder status."""
        placeholder = Placeholder(
            raw_text="{{John 3:16}}",
            reference=sample_verse_reference
        )
        placeholder.status = Placeholder.Status.COMPLETED
        assert placeholder.status == Placeholder.Status.COMPLETED

    def test_placeholder_unique_key(self, sample_verse_reference):
        """Test unique key generation for placeholders."""
        placeholder = Placeholder(
            raw_text="{{John 3:16}}",
            reference=sample_verse_reference
        )
        key = placeholder.unique_key
        assert "John 3:16" in key
        assert sample_verse_reference.translation.value in key

    def test_placeholder_error_handling(self, sample_verse_reference):
        """Test placeholder with error message."""
        placeholder = Placeholder(
            raw_text="{{John 3:16}}",
            reference=sample_verse_reference,
            status=Placeholder.Status.FAILED,
            error_message="API request failed"
        )
        assert placeholder.status == Placeholder.Status.FAILED
        assert placeholder.error_message == "API request failed"

    def test_placeholder_validation_negative_position(self, sample_verse_reference):
        """Test validation of negative positions."""
        with pytest.raises(ValidationError):
            Placeholder(
                raw_text="{{John 3:16}}",
                reference=sample_verse_reference,
                position=-1  # Invalid negative position
            )

"""
Data models for scripture verse representation and management.

This module provides immutable, type-safe data models for representing Bible verses,
placeholders, and related metadata using Pydantic for validation and serialization.

Author: Kasim Lyee <lyee@codewithlyee.com>
Organization: Softlite Inc.
License: MIT
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Optional, ClassVar
from pydantic import BaseModel, Field, field_validator, computed_field
from pydantic.config import ConfigDict


class TranslationType(str, Enum):
    """
    Enumeration of supported Bible translations.
    
    Each translation is mapped to its API.Bible identifier for seamless
    integration with the scripture API service.
    """
    
    NIV = "de4e12af7f28f599-02"  # New International Version
    KJV = "de4e12af7f28f599-01"  # King James Version
    ESV = "f421fe261da7624f-01"  # English Standard Version
    NKJV = "de4e12af7f28f599-03"  # New King James Version
    NLT = "de4e12af7f28f599-04"  # New Living Translation
    
    @classmethod
    def from_display_name(cls, name: str) -> TranslationType:
        """
        Convert human-readable translation name to enum value.
        
        Args:
            name: Display name (e.g., "NIV", "King James Version")
            
        Returns:
            Corresponding TranslationType enum member
            
        Raises:
            ValueError: If translation name is not recognized
        """
        name_upper = name.upper().strip()
        
        # Direct match
        if name_upper in cls.__members__:
            return cls[name_upper]
        
        # Fuzzy match for full names
        mapping = {
            "NEW INTERNATIONAL VERSION": cls.NIV,
            "KING JAMES VERSION": cls.KJV,
            "ENGLISH STANDARD VERSION": cls.ESV,
            "NEW KING JAMES VERSION": cls.NKJV,
            "NEW LIVING TRANSLATION": cls.NLT,
        }
        
        if name_upper in mapping:
            return mapping[name_upper]
        
        raise ValueError(f"Unsupported translation: {name}")
    
    @property
    def display_name(self) -> str:
        """Get human-friendly display name for UI rendering."""
        names = {
            self.NIV: "New International Version (NIV)",
            self.KJV: "King James Version (KJV)",
            self.ESV: "English Standard Version (ESV)",
            self.NKJV: "New King James Version (NKJV)",
            self.NLT: "New Living Translation (NLT)",
        }
        return names[self]


class VerseReference(BaseModel):
    """
    Immutable representation of a Bible verse reference.
    
    Provides structured parsing and validation of scripture references,
    supporting both single verses and verse ranges with robust error handling.
    
    Attributes:
        book: Name of the Bible book (e.g., "John", "1 Corinthians")
        chapter: Chapter number (must be positive)
        start_verse: Starting verse number
        end_verse: Optional ending verse for ranges
        translation: Bible translation to use
    
    Examples:
        >>> ref = VerseReference(book="John", chapter=3, start_verse=16)
        >>> ref.canonical_reference
        'John 3:16'
        
        >>> range_ref = VerseReference(book="Psalm", chapter=23, start_verse=1, end_verse=3)
        >>> range_ref.canonical_reference
        'Psalm 23:1-3'
    """
    
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)
    
    # Regex pattern for parsing scripture references
    REFERENCE_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^\s*(\d?\s*[A-Za-z]+\.?)\s+(\d+):(\d+)(?:-(\d+))?\s*$"
    )
    
    book: str = Field(..., min_length=2, max_length=50)
    chapter: int = Field(..., ge=1, le=150)
    start_verse: int = Field(..., ge=1, le=176)
    end_verse: Optional[int] = Field(None, ge=1, le=176)
    translation: TranslationType = Field(default=TranslationType.NLT)
    
    @field_validator("end_verse")
    @classmethod
    def validate_verse_range(cls, v: Optional[int], info) -> Optional[int]:
        """
        Ensure end_verse is greater than start_verse when specified.
        
        Args:
            v: The end_verse value to validate
            info: Pydantic validation context containing other field values
            
        Returns:
            Validated end_verse value
            
        Raises:
            ValueError: If end_verse <= start_verse
        """
        if v is not None and "start_verse" in info.data:
            start = info.data["start_verse"]
            if v <= start:
                raise ValueError(
                    f"end_verse ({v}) must be greater than start_verse ({start})"
                )
        return v
    
    @computed_field
    @property
    def canonical_reference(self) -> str:
        """
        Generate standardized scripture reference string.
        
        Returns:
            Canonical reference format (e.g., "John 3:16" or "Psalm 23:1-3")
        """
        base = f"{self.book} {self.chapter}:{self.start_verse}"
        if self.end_verse:
            return f"{base}-{self.end_verse}"
        return base
    
    @computed_field
    @property
    def is_range(self) -> bool:
        """Check if this reference represents a verse range."""
        return self.end_verse is not None
    
    @classmethod
    def parse(cls, reference: str, translation: TranslationType = TranslationType.NLT) -> VerseReference:
        """
        Parse a scripture reference string into a structured VerseReference object.
        
        This method supports various common reference formats including:
        - Simple references: "John 3:16"
        - Verse ranges: "Genesis 1:1-5"
        - Books with numbers: "1 Corinthians 13:4"
        - Abbreviated books: "Gen. 1:1"
        
        Args:
            reference: Scripture reference string to parse
            translation: Bible translation to use (default: NLT)
            
        Returns:
            Parsed and validated VerseReference instance
            
        Raises:
            ValueError: If reference format is invalid or cannot be parsed
            
        Examples:
            >>> VerseReference.parse("John 3:16")
            VerseReference(book='John', chapter=3, start_verse=16, ...)
            
            >>> VerseReference.parse("Psalm 23:1-6", TranslationType.KJV)
            VerseReference(book='Psalm', chapter=23, start_verse=1, end_verse=6, ...)
        """
        match = cls.REFERENCE_PATTERN.match(reference.strip())
        
        if not match:
            raise ValueError(
                f"Invalid scripture reference format: '{reference}'. "
                f"Expected format: 'Book Chapter:Verse' or 'Book Chapter:Verse-Verse'"
            )
        
        book, chapter, start_verse, end_verse = match.groups()
        
        return cls(
            book=book.strip(),
            chapter=int(chapter),
            start_verse=int(start_verse),
            end_verse=int(end_verse) if end_verse else None,
            translation=translation,
        )
    
    def to_api_id(self) -> str:
        """
        Convert reference to API.Bible verse identifier format.
        
        Returns:
            API-compatible verse ID (e.g., "JHN.3.16")
        """
        # Book abbreviation mapping (simplified - extend as needed)
        book_abbrev = self._get_book_abbreviation(self.book)
        
        if self.is_range:
            return f"{book_abbrev}.{self.chapter}.{self.start_verse}-{book_abbrev}.{self.chapter}.{self.end_verse}"
        return f"{book_abbrev}.{self.chapter}.{self.start_verse}"
    
    @staticmethod
    def _get_book_abbreviation(book: str) -> str:
        """
        Convert book name to standard three-letter abbreviation.
        
        Args:
            book: Full or partial book name
            
        Returns:
            Three-letter book abbreviation for API usage
        """
        # Comprehensive abbreviation mapping
        abbreviations = {
            "genesis": "GEN", "gen": "GEN",
            "exodus": "EXO", "exo": "EXO",
            "leviticus": "LEV", "lev": "LEV",
            "numbers": "NUM", "num": "NUM",
            "deuteronomy": "DEU", "deut": "DEU",
            "joshua": "JOS", "josh": "JOS",
            "judges": "JDG", "judg": "JDG",
            "ruth": "RUT",
            "1 samuel": "1SA", "1sam": "1SA",
            "2 samuel": "2SA", "2sam": "2SA",
            "1 kings": "1KI", "1ki": "1KI",
            "2 kings": "2KI", "2ki": "2KI",
            "1 chronicles": "1CH", "1chr": "1CH",
            "2 chronicles": "2CH", "2chr": "2CH",
            "ezra": "EZR",
            "nehemiah": "NEH", "neh": "NEH",
            "esther": "EST",
            "job": "JOB",
            "psalm": "PSA", "psalms": "PSA", "psa": "PSA",
            "proverbs": "PRO", "prov": "PRO",
            "ecclesiastes": "ECC", "eccl": "ECC",
            "song of solomon": "SNG", "song": "SNG",
            "isaiah": "ISA", "isa": "ISA",
            "jeremiah": "JER", "jer": "JER",
            "lamentations": "LAM", "lam": "LAM",
            "ezekiel": "EZK", "ezek": "EZK",
            "daniel": "DAN", "dan": "DAN",
            "hosea": "HOS", "hos": "HOS",
            "joel": "JOL",
            "amos": "AMO",
            "obadiah": "OBA", "obad": "OBA",
            "jonah": "JON",
            "micah": "MIC", "mic": "MIC",
            "nahum": "NAM", "nah": "NAM",
            "habakkuk": "HAB", "hab": "HAB",
            "zephaniah": "ZEP", "zeph": "ZEP",
            "haggai": "HAG", "hag": "HAG",
            "zechariah": "ZEC", "zech": "ZEC",
            "malachi": "MAL", "mal": "MAL",
            "matthew": "MAT", "matt": "MAT",
            "mark": "MRK",
            "luke": "LUK",
            "john": "JHN",
            "acts": "ACT",
            "romans": "ROM", "rom": "ROM",
            "1 corinthians": "1CO", "1cor": "1CO",
            "2 corinthians": "2CO", "2cor": "2CO",
            "galatians": "GAL", "gal": "GAL",
            "ephesians": "EPH", "eph": "EPH",
            "philippians": "PHP", "phil": "PHP",
            "colossians": "COL", "col": "COL",
            "1 thessalonians": "1TH", "1thess": "1TH",
            "2 thessalonians": "2TH", "2thess": "2TH",
            "1 timothy": "1TI", "1tim": "1TI",
            "2 timothy": "2TI", "2tim": "2TI",
            "titus": "TIT",
            "philemon": "PHM", "phlm": "PHM",
            "hebrews": "HEB", "heb": "HEB",
            "james": "JAS", "jas": "JAS",
            "1 peter": "1PE", "1pet": "1PE",
            "2 peter": "2PE", "2pet": "2PE",
            "1 john": "1JN", "1jn": "1JN",
            "2 john": "2JN", "2jn": "2JN",
            "3 john": "3JN", "3jn": "3JN",
            "jude": "JUD",
            "revelation": "REV", "rev": "REV",
        }
        
        book_lower = book.lower().strip().replace(".", "")
        return abbreviations.get(book_lower, book[:3].upper())


class Verse(BaseModel):
    """
    Complete verse data model with content and metadata.
    
    Represents a fully fetched Bible verse with all associated information
    including the text content, reference, translation details, and retrieval metadata.
    
    Attributes:
        reference: Structured verse reference
        text: The actual verse text content
        translation: Translation used for this verse
        retrieved_at: Timestamp when verse was fetched
        source_api: API source identifier
        copyright_notice: Optional copyright attribution
    """
    
    model_config = ConfigDict(frozen=True)
    
    reference: VerseReference
    text: str = Field(..., min_length=1, max_length=10000)
    translation: TranslationType
    retrieved_at: datetime = Field(default_factory=datetime.now)
    source_api: str = Field(default="api.bible")
    copyright_notice: Optional[str] = None
    
    @computed_field
    @property
    def formatted_text(self) -> str:
        """
        Generate formatted verse text for document insertion.
        
        Returns:
            Formatted string: "Reference — Text" (e.g., "John 3:16 — For God so loved...")
        """
        return f"{self.reference.canonical_reference} — {self.text}"
    
    def to_dict(self) -> dict:
        """
        Convert verse to dictionary for serialization.
        
        Returns:
            Dictionary representation of verse data
        """
        return {
            "reference": self.reference.canonical_reference,
            "text": self.text,
            "translation": self.translation.name,
            "retrieved_at": self.retrieved_at.isoformat(),
            "source_api": self.source_api,
        }


class Placeholder(BaseModel):
    """
    Representation of a verse placeholder found in a document.
    
    Tracks placeholder location and metadata for efficient replacement operations.
    
    Attributes:
        raw_text: Original placeholder text (e.g., "{{John 3:16}}")
        reference: Parsed verse reference
        position: Character position in document
        paragraph_index: Index of containing paragraph
        status: Processing status
        error_message: Optional error message if processing failed
    """
    
    model_config = ConfigDict(frozen=False)  # Allow status updates
    
    class Status(str, Enum):
        """Placeholder processing status."""
        PENDING = "pending"
        FETCHING = "fetching"
        COMPLETED = "completed"
        FAILED = "failed"
        SKIPPED = "skipped"
    
    raw_text: str = Field(..., min_length=1, description="Original placeholder text")
    reference: VerseReference = Field(..., description="Parsed verse reference")
    position: int = Field(default=0, ge=0, description="Character position in document")
    paragraph_index: int = Field(default=0, ge=0, description="Index of containing paragraph")
    status: Status = Field(default=Status.PENDING, description="Processing status")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    @computed_field
    @property
    def unique_key(self) -> str:
        """Generate unique identifier for caching and deduplication."""
        return f"{self.reference.canonical_reference}:{self.reference.translation.value}"
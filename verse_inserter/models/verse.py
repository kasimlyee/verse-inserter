"""
Data models for Bible verses, references, and placeholders.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class TranslationType(Enum):
    """Supported Bible translations."""
    
    NIV = ("NIV", "de4e12af7f28f599-02", "New International Version")
    KJV = ("KJV", "de4e12af7f28f599-01", "King James Version")
    ESV = ("ESV", "f421fe261da7624f-01", "English Standard Version")
    NKJV = ("NKJV", "de4e12af7f28f599-03", "New King James Version")
    NLT = ("NLT", "de4e12af7f28f599-04", "New Living Translation")
    
    def __init__(self, code: str, bible_id: str, display_name: str):
        self.code = code
        self.bible_id = bible_id
        self.display_name = display_name
    
    @classmethod
    def from_code(cls, code: str) -> TranslationType:
        """Get translation type from code."""
        for trans in cls:
            if trans.code == code:
                return trans
        raise ValueError(f"Unknown translation code: {code}")


@dataclass
class VerseReference:
    """Reference to a Bible verse or verse range."""
    
    book: str
    chapter: int
    verse_start: int
    verse_end: Optional[int] = None
    translation: TranslationType = TranslationType.NIV
    
    @property
    def canonical_reference(self) -> str:
        """Get canonical reference string."""
        if self.verse_end and self.verse_end != self.verse_start:
            return f"{self.book} {self.chapter}:{self.verse_start}-{self.verse_end}"
        return f"{self.book} {self.chapter}:{self.verse_start}"
    
    def __str__(self) -> str:
        return self.canonical_reference


@dataclass
class Placeholder:
    """Placeholder found in document for verse insertion."""
    
    reference: VerseReference
    original_text: str
    location: str
    paragraph_index: Optional[int] = None
    run_index: Optional[int] = None
    position: int = 0
    
    @property
    def unique_key(self) -> str:
        """Get unique key for deduplication."""
        return self.reference.canonical_reference
    
    def __str__(self) -> str:
        return f"Placeholder({self.original_text} at {self.location})"


@dataclass
class Verse:
    """Complete verse data with text and metadata."""
    
    reference: VerseReference
    text: str
    translation: TranslationType
    verse_id: Optional[str] = None
    
    @property
    def formatted_text(self) -> str:
        """Get formatted verse text with reference."""
        return f"{self.reference.canonical_reference} — {self.text}"
    
    def __str__(self) -> str:
        return self.formatted_text


@dataclass
class Document:
    """Document metadata and processing results."""
    
    input_path: str
    output_path: Optional[str] = None
    placeholders_found: int = 0
    placeholders_replaced: int = 0
    placeholders_failed: int = 0
    verses: List[Verse] = None
    
    def __post_init__(self):
        if self.verses is None:
            self.verses = []
    
    @property
    def success_rate(self) -> float:
        """Calculate replacement success rate."""
        if self.placeholders_found == 0:
            return 0.0
        return (self.placeholders_replaced / self.placeholders_found) * 100
    
    def __str__(self) -> str:
        return (
            f"Document Processing Results:\n"
            f"  Input: {self.input_path}\n"
            f"  Output: {self.output_path}\n"
            f"  Found: {self.placeholders_found}\n"
            f"  Replaced: {self.placeholders_replaced}\n"
            f"  Failed: {self.placeholders_failed}\n"
            f"  Success Rate: {self.success_rate:.1f}%"
        )

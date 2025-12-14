"""
Citation formatter for Bible verses in various academic styles.

Supports multiple citation formats including SBL, Chicago, MLA, APA, and Turabian.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

from enum import Enum
from typing import Optional

from verse_inserter.models.verse import Verse, VerseReference, TranslationType


class CitationStyle(str, Enum):
    """Supported citation styles for Bible verses."""

    PLAIN = "plain"  # Just the verse text
    SBL = "sbl"  # Society of Biblical Literature
    CHICAGO = "chicago"  # Chicago Manual of Style
    MLA = "mla"  # Modern Language Association
    APA = "apa"  # American Psychological Association
    TURABIAN = "turabian"  # Turabian (similar to Chicago)

    @property
    def display_name(self) -> str:
        """Get human-friendly display name."""
        names = {
            self.PLAIN: "Plain Text (No Citation)",
            self.SBL: "SBL Handbook of Style",
            self.CHICAGO: "Chicago Manual of Style",
            self.MLA: "MLA Style",
            self.APA: "APA Style",
            self.TURABIAN: "Turabian Style",
        }
        return names[self]


class CitationFormatter:
    """
    Format Bible verses according to various citation styles.

    Features:
    - Multiple citation formats
    - Proper abbreviations for each style
    - Translation notation
    - Verse range formatting
    """

    # Translation abbreviations for citations
    TRANSLATION_ABBR = {
        TranslationType.KJV: "KJV",
        TranslationType.NIV: "NIV",
        TranslationType.ESV: "ESV",
        TranslationType.NKJV: "NKJV",
        TranslationType.NLT: "NLT",
    }

    # Book abbreviations for SBL style
    SBL_ABBR = {
        "Genesis": "Gen", "Exodus": "Exod", "Leviticus": "Lev",
        "Numbers": "Num", "Deuteronomy": "Deut", "Joshua": "Josh",
        "Judges": "Judg", "Ruth": "Ruth", "1 Samuel": "1 Sam",
        "2 Samuel": "2 Sam", "1 Kings": "1 Kgs", "2 Kings": "2 Kgs",
        "1 Chronicles": "1 Chr", "2 Chronicles": "2 Chr", "Ezra": "Ezra",
        "Nehemiah": "Neh", "Esther": "Esth", "Job": "Job",
        "Psalm": "Ps", "Proverbs": "Prov", "Ecclesiastes": "Eccl",
        "Song of Solomon": "Song", "Isaiah": "Isa", "Jeremiah": "Jer",
        "Lamentations": "Lam", "Ezekiel": "Ezek", "Daniel": "Dan",
        "Hosea": "Hos", "Joel": "Joel", "Amos": "Amos",
        "Obadiah": "Obad", "Jonah": "Jonah", "Micah": "Mic",
        "Nahum": "Nah", "Habakkuk": "Hab", "Zephaniah": "Zeph",
        "Haggai": "Hag", "Zechariah": "Zech", "Malachi": "Mal",
        "Matthew": "Matt", "Mark": "Mark", "Luke": "Luke",
        "John": "John", "Acts": "Acts", "Romans": "Rom",
        "1 Corinthians": "1 Cor", "2 Corinthians": "2 Cor",
        "Galatians": "Gal", "Ephesians": "Eph", "Philippians": "Phil",
        "Colossians": "Col", "1 Thessalonians": "1 Thess",
        "2 Thessalonians": "2 Thess", "1 Timothy": "1 Tim",
        "2 Timothy": "2 Tim", "Titus": "Titus", "Philemon": "Phlm",
        "Hebrews": "Heb", "James": "Jas", "1 Peter": "1 Pet",
        "2 Peter": "2 Pet", "1 John": "1 John", "2 John": "2 John",
        "3 John": "3 John", "Jude": "Jude", "Revelation": "Rev",
    }

    @classmethod
    def format_verse(
        cls,
        verse: Verse,
        style: CitationStyle = CitationStyle.PLAIN,
        include_reference: bool = True,
    ) -> str:
        """
        Format a verse according to the specified citation style.

        Args:
            verse: Verse to format
            style: Citation style to use
            include_reference: Whether to include the reference

        Returns:
            Formatted verse text with citation
        """
        if style == CitationStyle.PLAIN:
            return cls._format_plain(verse, include_reference)
        elif style == CitationStyle.SBL:
            return cls._format_sbl(verse, include_reference)
        elif style == CitationStyle.CHICAGO:
            return cls._format_chicago(verse, include_reference)
        elif style == CitationStyle.MLA:
            return cls._format_mla(verse, include_reference)
        elif style == CitationStyle.APA:
            return cls._format_apa(verse, include_reference)
        elif style == CitationStyle.TURABIAN:
            return cls._format_turabian(verse, include_reference)
        else:
            return cls._format_plain(verse, include_reference)

    @classmethod
    def _format_plain(cls, verse: Verse, include_ref: bool) -> str:
        """Format as plain text."""
        if include_ref:
            ref = verse.reference.canonical_reference
            return f'"{verse.text}" ({ref})'
        return verse.text

    @classmethod
    def _format_sbl(cls, verse: Verse, include_ref: bool) -> str:
        """
        Format according to SBL Handbook of Style.

        Example: "For God so loved the world..." (John 3:16 NIV)
        """
        if not include_ref:
            return verse.text

        ref = verse.reference
        book_abbr = cls.SBL_ABBR.get(ref.book, ref.book)
        trans_abbr = cls.TRANSLATION_ABBR.get(ref.translation, "")

        # Format verse range
        if ref.end_verse:
            verse_ref = f"{ref.chapter}:{ref.start_verse}-{ref.end_verse}"
        else:
            verse_ref = f"{ref.chapter}:{ref.start_verse}"

        citation = f"{book_abbr} {verse_ref}"
        if trans_abbr:
            citation += f" {trans_abbr}"

        return f'"{verse.text}" ({citation})'

    @classmethod
    def _format_chicago(cls, verse: Verse, include_ref: bool) -> str:
        """
        Format according to Chicago Manual of Style.

        Example: "For God so loved the world..." (John 3:16, NIV)
        """
        if not include_ref:
            return verse.text

        ref = verse.reference
        trans_abbr = cls.TRANSLATION_ABBR.get(ref.translation, "")

        # Format verse range
        if ref.end_verse:
            verse_ref = f"{ref.chapter}:{ref.start_verse}-{ref.end_verse}"
        else:
            verse_ref = f"{ref.chapter}:{ref.start_verse}"

        citation = f"{ref.book} {verse_ref}"
        if trans_abbr:
            citation += f", {trans_abbr}"

        return f'"{verse.text}" ({citation})'

    @classmethod
    def _format_mla(cls, verse: Verse, include_ref: bool) -> str:
        """
        Format according to MLA Style.

        Example: "For God so loved the world..." (John 3.16 NIV)
        Note: MLA uses periods instead of colons
        """
        if not include_ref:
            return verse.text

        ref = verse.reference
        trans_abbr = cls.TRANSLATION_ABBR.get(ref.translation, "")

        # MLA uses periods instead of colons
        if ref.end_verse:
            verse_ref = f"{ref.chapter}.{ref.start_verse}-{ref.end_verse}"
        else:
            verse_ref = f"{ref.chapter}.{ref.start_verse}"

        citation = f"{ref.book} {verse_ref}"
        if trans_abbr:
            citation += f" {trans_abbr}"

        return f'"{verse.text}" ({citation})'

    @classmethod
    def _format_apa(cls, verse: Verse, include_ref: bool) -> str:
        """
        Format according to APA Style.

        Example: "For God so loved the world..." (John 3:16, New International Version)
        Note: APA prefers full translation names
        """
        if not include_ref:
            return verse.text

        ref = verse.reference

        # APA uses full translation names
        trans_names = {
            TranslationType.KJV: "King James Version",
            TranslationType.NIV: "New International Version",
            TranslationType.ESV: "English Standard Version",
            TranslationType.NKJV: "New King James Version",
            TranslationType.NLT: "New Living Translation",
        }
        trans_name = trans_names.get(ref.translation, "")

        # Format verse range
        if ref.end_verse:
            verse_ref = f"{ref.chapter}:{ref.start_verse}-{ref.end_verse}"
        else:
            verse_ref = f"{ref.chapter}:{ref.start_verse}"

        citation = f"{ref.book} {verse_ref}"
        if trans_name:
            citation += f", {trans_name}"

        return f'"{verse.text}" ({citation})'

    @classmethod
    def _format_turabian(cls, verse: Verse, include_ref: bool) -> str:
        """
        Format according to Turabian Style.

        Example: "For God so loved the world..." (John 3:16 NIV)
        Note: Turabian is similar to Chicago
        """
        # Turabian is very similar to Chicago for Bible verses
        return cls._format_chicago(verse, include_ref)

    @classmethod
    def get_reference_only(
        cls,
        reference: VerseReference,
        style: CitationStyle = CitationStyle.PLAIN,
    ) -> str:
        """
        Get just the reference citation without verse text.

        Args:
            reference: Verse reference
            style: Citation style to use

        Returns:
            Formatted reference string
        """
        if style == CitationStyle.SBL:
            book_abbr = cls.SBL_ABBR.get(reference.book, reference.book)
        else:
            book_abbr = reference.book

        trans_abbr = cls.TRANSLATION_ABBR.get(reference.translation, "")

        # Format verse range
        separator = "." if style == CitationStyle.MLA else ":"
        if reference.end_verse:
            verse_ref = f"{reference.chapter}{separator}{reference.start_verse}-{reference.end_verse}"
        else:
            verse_ref = f"{reference.chapter}{separator}{reference.start_verse}"

        citation = f"{book_abbr} {verse_ref}"

        # Add translation
        if trans_abbr:
            if style == CitationStyle.CHICAGO or style == CitationStyle.TURABIAN:
                citation += f", {trans_abbr}"
            else:
                citation += f" {trans_abbr}"

        return citation

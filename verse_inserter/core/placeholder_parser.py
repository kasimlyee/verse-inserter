"""
Advanced placeholder detection and parsing engine.

Implements robust, regex-based parsing of scripture placeholders with comprehensive
error handling, normalization, and support for various reference formats.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

from __future__ import annotations

import re
from typing import List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from ..models.verse import VerseReference, Placeholder, TranslationType
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ParsingStatistics:
    """
    Statistical metadata from placeholder parsing operations.
    
    Tracks parsing performance and provides insights for optimization
    and user feedback.
    
    Attributes:
        total_found: Total placeholders detected
        unique_references: Number of unique verse references
        invalid_count: Count of malformed placeholders
        duplicate_count: Number of duplicate references
        books_referenced: Set of unique Bible books referenced
    """
    
    total_found: int = 0
    unique_references: int = 0
    invalid_count: int = 0
    duplicate_count: int = 0
    books_referenced: Set[str] = field(default_factory=set)
    
    @property
    def success_rate(self) -> float:
        """Calculate percentage of successfully parsed placeholders."""
        if self.total_found == 0:
            return 0.0
        return (self.total_found - self.invalid_count) / self.total_found * 100
    
    def __str__(self) -> str:
        """Generate human-readable statistics summary."""
        return (
            f"Parsing Statistics:\n"
            f"  Total Placeholders: {self.total_found}\n"
            f"  Unique References: {self.unique_references}\n"
            f"  Invalid: {self.invalid_count}\n"
            f"  Success Rate: {self.success_rate:.1f}%\n"
            f"  Books Referenced: {len(self.books_referenced)}"
        )


class PlaceholderParser:
    """
    High-performance placeholder detection and parsing engine.
    
    Utilizes compiled regex patterns, caching, and normalization strategies
    to efficiently extract and validate scripture placeholders from document text.
    
    Features:
        - Multiple placeholder format support
        - Intelligent normalization and validation
        - Duplicate detection and consolidation
        - Comprehensive error reporting
        - Performance optimization through regex compilation
    
    Example:
        >>> parser = PlaceholderParser()
        >>> placeholders = parser.parse_text("Check {{John 3:16}} and {{Psalm 23:1-3}}")
        >>> len(placeholders)
        2
    """
    
    # Placeholder pattern: {{Book Chapter:Verse}} or {{Book Chapter:Verse-Verse}}
    PLACEHOLDER_PATTERN = re.compile(
        r"\{\{\s*"  # Opening braces with optional whitespace
        r"((?:\d\s*)?\w+(?:\s+\w+)*)"  # Book name (supports numbers and multi-word)
        r"\s+"  # Whitespace separator
        r"(\d+)"  # Chapter number
        r"\s*:\s*"  # Colon separator with optional whitespace
        r"(\d+)"  # Starting verse
        r"(?:\s*-\s*(\d+))?"  # Optional ending verse (range)
        r"\s*\}\}",  # Closing braces with optional whitespace
        re.IGNORECASE | re.MULTILINE
    )
    
    # Alternative patterns for flexibility
    ALTERNATIVE_PATTERNS = [
        # Pattern with parentheses: (John 3:16)
        re.compile(
            r"\(\s*"
            r"((?:\d\s*)?\w+(?:\s+\w+)*)\s+(\d+)\s*:\s*(\d+)(?:\s*-\s*(\d+))?"
            r"\s*\)",
            re.IGNORECASE
        ),
        # Pattern with square brackets: [John 3:16]
        re.compile(
            r"\[\s*"
            r"((?:\d\s*)?\w+(?:\s+\w+)*)\s+(\d+)\s*:\s*(\d+)(?:\s*-\s*(\d+))?"
            r"\s*\]",
            re.IGNORECASE
        ),
    ]
    
    def __init__(
        self,
        default_translation: TranslationType = TranslationType.NIV,
        enable_alternative_formats: bool = True,
        normalize_whitespace: bool = True,
    ):
        """
        Initialize the placeholder parser with configuration options.
        
        Args:
            default_translation: Default Bible translation for parsed references
            enable_alternative_formats: Whether to detect alternative placeholder formats
            normalize_whitespace: Whether to normalize whitespace in book names
        """
        self.default_translation = default_translation
        self.enable_alternative_formats = enable_alternative_formats
        self.normalize_whitespace = normalize_whitespace
        
        # Cache for parsed references to avoid re-parsing
        self._reference_cache: dict[str, Optional[VerseReference]] = {}
        
        # Statistics tracking
        self._stats = ParsingStatistics()
        
        logger.info(
            f"PlaceholderParser initialized with translation={default_translation.name}, "
            f"alternative_formats={enable_alternative_formats}"
        )
    
    def parse_text(
        self,
        text: str,
        paragraph_index: int = 0,
        position_offset: int = 0,
    ) -> List[Placeholder]:
        """
        Extract and parse all placeholders from a text segment.
        
        This method performs comprehensive placeholder detection using multiple
        regex patterns, validates each match, and constructs structured Placeholder
        objects with position tracking for document replacement operations.
        
        Args:
            text: Text content to parse for placeholders
            paragraph_index: Index of the paragraph in the document
            position_offset: Character offset for absolute positioning
            
        Returns:
            List of validated Placeholder objects, sorted by position
            
        Example:
            >>> parser = PlaceholderParser()
            >>> text = "See {{John 3:16}} and {{Genesis 1:1-3}}"
            >>> placeholders = parser.parse_text(text)
            >>> [p.reference.canonical_reference for p in placeholders]
            ['John 3:16', 'Genesis 1:1-3']
        """
        placeholders: List[Placeholder] = []
        seen_references: Set[str] = set()
        
        # Primary pattern matching
        for match in self.PLACEHOLDER_PATTERN.finditer(text):
            placeholder = self._create_placeholder_from_match(
                match, paragraph_index, position_offset
            )
            
            if placeholder:
                # Track duplicates
                ref_key = placeholder.unique_key
                if ref_key in seen_references:
                    self._stats.duplicate_count += 1
                else:
                    seen_references.add(ref_key)
                    placeholders.append(placeholder)
                    self._stats.books_referenced.add(placeholder.reference.book)
        
        # Alternative pattern matching if enabled
        if self.enable_alternative_formats:
            for pattern in self.ALTERNATIVE_PATTERNS:
                for match in pattern.finditer(text):
                    placeholder = self._create_placeholder_from_match(
                        match, paragraph_index, position_offset
                    )
                    
                    if placeholder:
                        ref_key = placeholder.unique_key
                        if ref_key not in seen_references:
                            seen_references.add(ref_key)
                            placeholders.append(placeholder)
                            self._stats.books_referenced.add(placeholder.reference.book)
        
        # Update statistics
        self._stats.total_found += len(placeholders)
        self._stats.unique_references = len(seen_references)
        
        # Sort by position for sequential processing
        placeholders.sort(key=lambda p: p.position)
        
        logger.debug(
            f"Parsed {len(placeholders)} placeholders from text "
            f"(paragraph {paragraph_index}, length {len(text)})"
        )
        
        return placeholders
    
    def _create_placeholder_from_match(
        self,
        match: re.Match,
        paragraph_index: int,
        position_offset: int,
    ) -> Optional[Placeholder]:
        """
        Create a validated Placeholder object from a regex match.
        
        Performs comprehensive validation and normalization of the matched
        scripture reference before constructing the Placeholder instance.
        
        Args:
            match: Regex match object containing reference components
            paragraph_index: Index of containing paragraph
            position_offset: Character offset for absolute positioning
            
        Returns:
            Validated Placeholder object, or None if validation fails
        """
        try:
            book, chapter, start_verse, end_verse = match.groups()
            
            # Normalize book name
            if self.normalize_whitespace:
                book = " ".join(book.split())
            
            # Create verse reference
            reference = VerseReference(
    		book=book.strip(),
    		chapter=int(chapter),
    		start_verse=int(start_verse),      # ✅ CORRECT FIELD NAME
    		end_verse=int(end_verse) if end_verse else None,  # ✅ CORRECT FIELD NAME
    		translation=self.default_translation,
	    )
            
            # Create placeholder
            placeholder = Placeholder(
                reference=reference,
                raw_text=match.group(0),
                paragraph_index=paragraph_index,
                position=match.start() + position_offset,
            )
            
            return placeholder
            
        except (ValueError, TypeError) as e:
            self._stats.invalid_count += 1
            logger.warning(
                f"Failed to parse placeholder '{match.group(0)}': {e}"
            )
            return None

	def parse_placeholder(
	    self, 
	    text: str, 
	    translation: TranslationType = None
	) -> Optional[Placeholder]:
	    """
	    Parse a single placeholder text with specified translation.
	    
	    Args:
	        text: The raw placeholder text (e.g., "{{John 3:16}}")
	        translation: Bible translation to use (defaults to instance default)
	        
	    Returns:
	        Placeholder object or None if parsing fails
	    """
	    if translation is None:
	        translation = self.default_translation
	    
	    try:
	        # Extract reference from placeholder (e.g., "{{John 3:16}}" -> "John 3:16")
	        reference_text = self._extract_reference(text)
	        if reference_text:
	            reference = VerseReference.parse(reference_text, translation=translation)
	            return Placeholder(
	                raw_text=text,
	                reference=reference,
	                position=0,  # Will be set properly in parse_text
	                paragraph_index=0  # Will be set properly in parse_text
	            )
	            
	    except Exception as e:
	        logger.warning(f"Failed to parse placeholder '{text}': {e}")
	    
	    return None

	def parse_multiple(
	    self, 
	    placeholder_texts: List[str], 
	    translation: TranslationType = None
	) -> List[Placeholder]:
	    """
	    Parse multiple placeholder texts with specified translation.
	    
	    Args:
	        placeholder_texts: List of raw placeholder texts
	        translation: Bible translation to use (defaults to instance default)
	        
	    Returns:
	        List of successfully parsed Placeholder objects
	    """
	    if translation is None:
	        translation = self.default_translation
	    
	    placeholders = []
	    for text in placeholder_texts:
	        placeholder = self.parse_placeholder(text, translation)
	        if placeholder:
	            placeholders.append(placeholder)
	    return placeholders

	def _extract_reference(self, placeholder_text: str) -> Optional[str]:
	    """
	    Extract scripture reference from placeholder text.
	    
	    Args:
	        placeholder_text: Raw placeholder (e.g., "{{John 3:16}}")
	        
	    Returns:
	        Extracted reference or None
	    """
	    # Try the main pattern first
	    match = self.PLACEHOLDER_PATTERN.match(placeholder_text.strip())
	    if match:
	        book, chapter, start_verse, end_verse = match.groups()
	        
	        # Reconstruct the reference without the brackets
	        reference = f"{book} {chapter}:{start_verse}"
	        if end_verse:
	            reference += f"-{end_verse}"
	        return reference
	    
	    # Try alternative patterns
	    if self.enable_alternative_formats:
	        for pattern in self.ALTERNATIVE_PATTERNS:
	            match = pattern.match(placeholder_text.strip())
	            if match:
	                book, chapter, start_verse, end_verse = match.groups()
	                reference = f"{book} {chapter}:{start_verse}"
	                if end_verse:
	                    reference += f"-{end_verse}"
	                return reference
	    
	    return None
    
    def parse_multiple_paragraphs(
        self,
        paragraphs: List[str],
    ) -> List[Placeholder]:
        """
        Parse placeholders from multiple paragraphs with position tracking.
        
        Processes a list of paragraph texts, maintaining accurate position
        tracking across paragraph boundaries for document-level operations.
        
        Args:
            paragraphs: List of paragraph text strings
            
        Returns:
            Consolidated list of all placeholders with accurate positions
        """
        all_placeholders: List[Placeholder] = []
        cumulative_offset = 0
        
        for idx, paragraph_text in enumerate(paragraphs):
            placeholders = self.parse_text(
                text=paragraph_text,
                paragraph_index=idx,
                position_offset=cumulative_offset,
            )
            all_placeholders.extend(placeholders)
            
            # Update offset (account for paragraph separator)
            cumulative_offset += len(paragraph_text) + 1
        
        logger.info(
            f"Parsed {len(all_placeholders)} total placeholders "
            f"from {len(paragraphs)} paragraphs"
        )
        
        return all_placeholders
    
    def validate_reference(self, reference_str: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a scripture reference string without parsing.
        
        Quick validation check for user input or preprocessing operations.
        
        Args:
            reference_str: Scripture reference string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Example:
            >>> parser = PlaceholderParser()
            >>> parser.validate_reference("John 3:16")
            (True, None)
            >>> parser.validate_reference("Invalid Reference")
            (False, "Invalid scripture reference format...")
        """
        try:
            VerseReference.parse(reference_str, self.default_translation)
            return True, None
        except ValueError as e:
            return False, str(e)
    
    def get_statistics(self) -> ParsingStatistics:
        """
        Retrieve parsing statistics for reporting and analytics.
        
        Returns:
            Current parsing statistics object
        """
        return self._stats
    
    def reset_statistics(self) -> None:
        """Reset parsing statistics for new parsing session."""
        self._stats = ParsingStatistics()
        logger.debug("Parsing statistics reset")
    
    def normalize_reference(self, reference_str: str) -> str:
        """
        Normalize a scripture reference to canonical format.
        
        Converts various reference formats to a standardized form for
        consistent processing and display.
        
        Args:
            reference_str: Reference string to normalize
            
        Returns:
            Normalized reference string
            
        Raises:
            ValueError: If reference cannot be parsed
        """
        ref = VerseReference.parse(reference_str, self.default_translation)
        return ref.canonical_reference
    
    def extract_unique_references(
        self,
        placeholders: List[Placeholder],
    ) -> List[VerseReference]:
        """
        Extract unique verse references from a list of placeholders.
        
        Eliminates duplicate references to optimize API calls and caching.
        
        Args:
            placeholders: List of placeholder objects
            
        Returns:
            List of unique VerseReference objects
        """
        unique_refs: dict[str, VerseReference] = {}
        
        for placeholder in placeholders:
            key = placeholder.unique_key
            if key not in unique_refs:
                unique_refs[key] = placeholder.reference
        
        return list(unique_refs.values())
    
    def group_by_book(
        self,
        placeholders: List[Placeholder],
    ) -> dict[str, List[Placeholder]]:
        """
        Group placeholders by Bible book for batch processing.
        
        Facilitates optimized API requests by grouping related verses.
        
        Args:
            placeholders: List of placeholder objects
            
        Returns:
            Dictionary mapping book names to placeholder lists
        """
        grouped: dict[str, List[Placeholder]] = defaultdict(list)
        
        for placeholder in placeholders:
            book = placeholder.reference.book
            grouped[book].append(placeholder)
        
        return dict(grouped)
    
    def estimate_api_calls(self, placeholders: List[Placeholder]) -> int:
        """
        Estimate the number of API calls required for a placeholder list.
        
        Accounts for caching and deduplication to provide accurate estimates.
        
        Args:
            placeholders: List of placeholders to process
            
        Returns:
            Estimated number of API requests needed
        """
        unique_refs = self.extract_unique_references(placeholders)
        return len(unique_refs)

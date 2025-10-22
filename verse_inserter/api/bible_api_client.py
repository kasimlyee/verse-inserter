"""
API.Bible client for fetching scripture text.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

from __future__ import annotations

import aiohttp
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.verse import Verse, VerseReference, TranslationType
from ..utils.logger import get_logger
from .api_exceptions import (
    APIError, 
    APIRateLimitError as RateLimitError, 
    APIAuthenticationError as AuthenticationError
)
from .free_bible_fallback import FreeBibleFallback

logger = get_logger(__name__)


class BibleAPIClient:
    """
    Async client for API.Bible service.
    
    Provides asynchronous scripture fetching with automatic retry logic,
    error handling, and integration with the Verse data models.
    
    Features:
        - Async/await support for concurrent verse fetching
        - Automatic retry with exponential backoff
        - Comprehensive error handling
        - Full integration with VerseReference and Verse models
        - Support for verse ranges
    
    Example:
        >>> async with BibleAPIClient(api_key="your-key") as client:
        ...     ref = VerseReference.parse("John 3:16", TranslationType.NIV)
        ...     verse = await client.fetch_verse(ref)
        ...     print(verse.formatted_text)
    """
    
    BASE_URL = "https://api.scripture.api.bible"
    
    def __init__(self, api_key: str):
        """
        Initialize API client.
        
        Args:
            api_key: API.Bible authentication key (get from https://scripture.api.bible)
        
        Raises:
            ValueError: If api_key is empty or invalid
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")
        
        self.api_key = api_key.strip()
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info("BibleAPIClient initialized")
    
    async def __aenter__(self) -> BibleAPIClient:
        """
        Async context manager entry.
        
        Returns:
            Self for context manager usage
        """
        self.session = aiohttp.ClientSession(
            headers={
                "api-key": self.api_key,
                "accept": "application/json"
            }
        )
        logger.debug("API session created")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Async context manager exit with cleanup.
        
        Args:
            exc_type: Exception type if any
            exc_val: Exception value if any
            exc_tb: Exception traceback if any
        """
        if self.session:
            await self.session.close()
            self.session = None
            logger.debug("API session closed")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch_verse(self, reference: VerseReference) -> Verse:
        """
        Fetch verse text from API.Bible.
        
        Automatically retries on failure with exponential backoff.
        Integrates seamlessly with VerseReference and returns typed Verse object.
        
        Args:
            reference: VerseReference object with book, chapter, and verse details
            
        Returns:
            Verse object with fetched text and metadata
            
        Raises:
            RuntimeError: If client not initialized with context manager
            AuthenticationError: If API key is invalid (401)
            RateLimitError: If rate limit exceeded (429)
            APIError: For other API errors
            
        Example:
            >>> ref = VerseReference.parse("John 3:16")
            >>> verse = await client.fetch_verse(ref)
            >>> print(verse.text)
        """
        if not self.session:
            raise RuntimeError(
                "Client not initialized. Use async context manager:\n"
                "  async with BibleAPIClient(api_key) as client:\n"
                "      verse = await client.fetch_verse(reference)"
            )
        
        # Get Bible ID from translation enum
        bible_id = reference.translation.value
        
        # Format verse ID for API
        verse_id = self._format_verse_id(reference)
        
        # Build API URL
        url = f"{self.BASE_URL}/v1/bibles/{bible_id}/verses/{verse_id}"
        
        logger.debug(f"Fetching verse: {reference.canonical_reference} from {url}")
        
        try:
            async with self.session.get(
                url,
                params={
                    "content-type": "text",
                    "include-notes": "false",
                    "include-titles": "false",
                    "include-chapter-numbers": "false",
                    "include-verse-numbers": "false"
                }
            ) as response:
                # Handle different response statuses
                if response.status == 200:
                    data = await response.json()
                    verse_text = data["data"]["content"].strip()
                    
                    # Clean HTML tags if present
                    verse_text = self._clean_verse_text(verse_text)
                    
                    logger.info(
                        f"Successfully fetched: {reference.canonical_reference} "
                        f"({len(verse_text)} chars)"
                    )
                    
                    # Return Verse object
                    return Verse(
                        reference=reference,
                        text=verse_text,
                        translation=reference.translation,
                        source_api="api.scripture.api.bible"
                    )
                
                elif response.status == 401:
                    error_data = await response.json()
                    error_msg = error_data.get("message", "Invalid API key")
                    logger.error(f"Authentication failed: {error_msg}")
                    raise AuthenticationError(
                        f"Invalid API key. Get one at https://scripture.api.bible"
                    )
                
                elif response.status == 429:
                    logger.warning("Rate limit exceeded")
                    raise RateLimitError(
                        "API rate limit exceeded. Please wait before retrying."
                    )
                
                elif response.status == 404:
                    error_data = await response.json()
                    error_msg = error_data.get("message", "Verse not found")
                    logger.error(f"Verse not found: {reference.canonical_reference}")
                    raise APIError(
                        f"Verse not found: {reference.canonical_reference}. "
                        f"Error: {error_msg}"
                    )
                
                else:
                    error_text = await response.text()
                    logger.error(
                        f"API error {response.status} for "
                        f"{reference.canonical_reference}: {error_text}"
                    )
                    raise APIError(
                        f"API error {response.status}: {error_text}"
                    )
        
        except aiohttp.ClientError as e:
            logger.error(
                f"Network error fetching {reference.canonical_reference}: {e}"
            )
            raise APIError(f"Network error: {e}") from e
    
    def _format_verse_id(self, reference: VerseReference) -> str:
        """
        Format verse reference for API.Bible endpoint.
        
        Converts VerseReference to API-compatible format:
        - Single verse: "JHN.3.16"
        - Verse range: "JHN.3.16-JHN.3.18"
        
        Args:
            reference: VerseReference object to format
            
        Returns:
            API-compatible verse ID string
            
        Example:
            >>> ref = VerseReference(book="John", chapter=3, start_verse=16)
            >>> client._format_verse_id(ref)
            'JHN.3.16'
        """
        book_abbrev = self._get_book_abbreviation(reference.book)
        
        # Handle verse ranges
        if reference.end_verse and reference.end_verse != reference.start_verse:
            return (
                f"{book_abbrev}.{reference.chapter}.{reference.start_verse}-"
                f"{book_abbrev}.{reference.chapter}.{reference.end_verse}"
            )
        
        # Single verse
        return f"{book_abbrev}.{reference.chapter}.{reference.start_verse}"
    
    def _get_book_abbreviation(self, book_name: str) -> str:
        """
        Get standardized three-letter book abbreviation for API.
        
        Maps full book names and common abbreviations to API.Bible standard codes.
        
        Args:
            book_name: Full or partial book name (e.g., "John", "1 Corinthians")
            
        Returns:
            Standard three-letter abbreviation (e.g., "JHN", "1CO")
            
        Example:
            >>> client._get_book_abbreviation("John")
            'JHN'
            >>> client._get_book_abbreviation("1 Corinthians")
            '1CO'
        """
        # Comprehensive book name to abbreviation mapping
        book_map = {
            # Old Testament
            "genesis": "GEN", "gen": "GEN",
            "exodus": "EXO", "exo": "EXO", "exod": "EXO",
            "leviticus": "LEV", "lev": "LEV",
            "numbers": "NUM", "num": "NUM",
            "deuteronomy": "DEU", "deu": "DEU", "deut": "DEU",
            "joshua": "JOS", "josh": "JOS",
            "judges": "JDG", "judg": "JDG",
            "ruth": "RUT",
            "1 samuel": "1SA", "1sam": "1SA", "1 sam": "1SA",
            "2 samuel": "2SA", "2sam": "2SA", "2 sam": "2SA",
            "1 kings": "1KI", "1ki": "1KI", "1 kin": "1KI",
            "2 kings": "2KI", "2ki": "2KI", "2 kin": "2KI",
            "1 chronicles": "1CH", "1chr": "1CH", "1 chr": "1CH",
            "2 chronicles": "2CH", "2chr": "2CH", "2 chr": "2CH",
            "ezra": "EZR",
            "nehemiah": "NEH", "neh": "NEH",
            "esther": "EST",
            "job": "JOB",
            "psalm": "PSA", "psalms": "PSA", "ps": "PSA", "psa": "PSA",
            "proverbs": "PRO", "prov": "PRO",
            "ecclesiastes": "ECC", "eccl": "ECC",
            "song of solomon": "SNG", "song": "SNG", "sos": "SNG",
            "isaiah": "ISA", "isa": "ISA",
            "jeremiah": "JER", "jer": "JER",
            "lamentations": "LAM", "lam": "LAM",
            "ezekiel": "EZK", "ezek": "EZK", "eze": "EZK",
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
            
            # New Testament
            "matthew": "MAT", "matt": "MAT", "mt": "MAT",
            "mark": "MRK", "mk": "MRK",
            "luke": "LUK", "lk": "LUK",
            "john": "JHN", "jn": "JHN",
            "acts": "ACT",
            "romans": "ROM", "rom": "ROM",
            "1 corinthians": "1CO", "1cor": "1CO", "1 cor": "1CO",
            "2 corinthians": "2CO", "2cor": "2CO", "2 cor": "2CO",
            "galatians": "GAL", "gal": "GAL",
            "ephesians": "EPH", "eph": "EPH",
            "philippians": "PHP", "phil": "PHP",
            "colossians": "COL", "col": "COL",
            "1 thessalonians": "1TH", "1thess": "1TH", "1 thess": "1TH",
            "2 thessalonians": "2TH", "2thess": "2TH", "2 thess": "2TH",
            "1 timothy": "1TI", "1tim": "1TI", "1 tim": "1TI",
            "2 timothy": "2TI", "2tim": "2TI", "2 tim": "2TI",
            "titus": "TIT", "tit": "TIT",
            "philemon": "PHM", "phlm": "PHM",
            "hebrews": "HEB", "heb": "HEB",
            "james": "JAS", "jas": "JAS", "jam": "JAS",
            "1 peter": "1PE", "1pet": "1PE", "1 pet": "1PE",
            "2 peter": "2PE", "2pet": "2PE", "2 pet": "2PE",
            "1 john": "1JN", "1jn": "1JN",
            "2 john": "2JN", "2jn": "2JN",
            "3 john": "3JN", "3jn": "3JN",
            "jude": "JUD",
            "revelation": "REV", "rev": "REV",
        }
        
        # Normalize book name: lowercase, strip whitespace, remove periods
        book_lower = book_name.lower().strip().replace(".", "")
        
        # Return mapped abbreviation or fallback to first 3 chars uppercase
        return book_map.get(book_lower, book_name.upper()[:3])

    async def fetch_verse_with_fallback(self, reference: VerseReference) -> Optional[Verse]:
        """
        Fetch verse with automatic fallback to free API.
        
        Tries the primary API.Bible first, then falls back to free API
        if the primary fails (e.g., due to plan restrictions).
        
        Args:
            reference: VerseReference to fetch
            
        Returns:
            Verse object if either API succeeds, None if both fail
        """
        try:
            # Try primary API first
            verse = await self.fetch_verse(reference)
            if verse and verse.text:
                logger.info(f"Primary API success: {reference.canonical_reference}")
                return verse
                
        except Exception as primary_error:
            logger.warning(
                f"Primary API failed for {reference.canonical_reference}: {primary_error}. "
                f"Trying free fallback..."
            )
        
        # Primary failed, try free fallback
        try:
            async with FreeBibleFallback() as free_client:
                verse = await free_client.fetch_verse(reference)
                if verse and verse.text:
                    logger.info(f"Free fallback success: {reference.canonical_reference}")
                    return verse
                else:
                    logger.error(f"Free fallback also failed for: {reference.canonical_reference}")
                    return None
                    
        except Exception as fallback_error:
            logger.error(f"Free fallback error for {reference.canonical_reference}: {fallback_error}")
            return None
    
    def _clean_verse_text(self, text: str) -> str:
        """
        Clean verse text by removing HTML tags and normalizing whitespace.
        
        Args:
            text: Raw verse text from API (may contain HTML)
            
        Returns:
            Cleaned text with HTML removed and whitespace normalized
            
        Example:
            >>> client._clean_verse_text("<p>For God so loved</p>  the world")
            'For God so loved the world'
        """
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        return text.strip()
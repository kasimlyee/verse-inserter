"""
API.Bible client for fetching scripture text.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import aiohttp
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.verse import Verse, VerseReference, TranslationType
from ..utils.logger import get_logger
from .api_exceptions import APIError, APIRateLimitError as RateLimitError, APIAuthenticationError as AuthenticationError

logger = get_logger(__name__)


class BibleAPIClient:
    """Async client for API.Bible service."""
    
    BASE_URL = "https://api.scripture.api.bible"
    
    def __init__(self, api_key: str):
        """
        Initialize API client.
        
        Args:
            api_key: API.Bible authentication key
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={"api-key": self.api_key}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch_verse(self, reference: VerseReference) -> Verse:
        """
        Fetch verse text from API.
        
        Args:
            reference: Verse reference to fetch
            
        Returns:
            Verse object with text
            
        Raises:
            APIError: On API errors
            RateLimitError: On rate limit exceeded
            AuthenticationError: On auth failures
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        bible_id = reference.translation.bible_id
        verse_id = self._format_verse_id(reference)
        url = f"{self.BASE_URL}/v1/bibles/{bible_id}/verses/{verse_id}"
        
        try:
            async with self.session.get(
                url,
                params={"content-type": "text"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    verse_text = data["data"]["content"].strip()
                    
                    logger.info(f"Fetched verse: {reference.canonical_reference}")
                    
                    return Verse(
                        reference=reference,
                        text=verse_text,
                        translation=reference.translation,
                        verse_id=verse_id
                    )
                elif response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 429:
                    raise RateLimitError("API rate limit exceeded")
                else:
                    error_text = await response.text()
                    raise APIError(
                        f"API error {response.status}: {error_text}"
                    )
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching {reference.canonical_reference}: {e}")
            raise APIError(f"Network error: {e}")
    
    def _format_verse_id(self, reference: VerseReference) -> str:
        """
        Format verse reference for API.
        
        Args:
            reference: Verse reference
            
        Returns:
            API-compatible verse ID
        """
        book_abbrev = self._get_book_abbreviation(reference.book)
        
        if reference.verse_end and reference.verse_end != reference.verse_start:
            return (
                f"{book_abbrev}.{reference.chapter}."
                f"{reference.verse_start}-"
                f"{book_abbrev}.{reference.chapter}."
                f"{reference.verse_end}"
            )
        return f"{book_abbrev}.{reference.chapter}.{reference.verse_start}"
    
    def _get_book_abbreviation(self, book_name: str) -> str:
        """
        Get standardized book abbreviation.
        
        Args:
            book_name: Full or partial book name
            
        Returns:
            Standard book abbreviation
        """
        book_map = {
            "genesis": "GEN", "gen": "GEN",
            "exodus": "EXO", "exo": "EXO",
            "leviticus": "LEV", "lev": "LEV",
            "numbers": "NUM", "num": "NUM",
            "deuteronomy": "DEU", "deu": "DEU", "deut": "DEU",
            "joshua": "JOS", "josh": "JOS",
            "judges": "JDG", "judg": "JDG",
            "ruth": "RUT",
            "1 samuel": "1SA", "1sam": "1SA", "1 sam": "1SA",
            "2 samuel": "2SA", "2sam": "2SA", "2 sam": "2SA",
            "1 kings": "1KI", "1ki": "1KI",
            "2 kings": "2KI", "2ki": "2KI",
            "1 chronicles": "1CH", "1chr": "1CH",
            "2 chronicles": "2CH", "2chr": "2CH",
            "ezra": "EZR",
            "nehemiah": "NEH", "neh": "NEH",
            "esther": "EST",
            "job": "JOB",
            "psalm": "PSA", "psalms": "PSA", "ps": "PSA",
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
        
        book_lower = book_name.lower().strip()
        return book_map.get(book_lower, book_name.upper())

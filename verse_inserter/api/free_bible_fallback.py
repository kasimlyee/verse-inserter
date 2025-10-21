"""
Free Bible API fallback client for when API.Bible fails.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import aiohttp
import re
from typing import Optional
from urllib.parse import quote
from ..models.verse import Verse, VerseReference, TranslationType
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FreeBibleFallback:
    """
    Free Bible API fallback using bible-api.com
    
    Used as a backup when the primary API.Bible service fails,
    particularly for users without Pro plan access to modern translations.
    """
    
    BASE_URL = "https://bible-api.com"
    
    # Map our TranslationType to free API codes
    TRANSLATION_MAP = {
        TranslationType.NIV: "niv",
        TranslationType.KJV: "kjv", 
        TranslationType.ESV: "esv",
        TranslationType.NKJV: "nkjv",
        TranslationType.NLT: "nlt",
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info("FreeBibleFallback initialized")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_verse(self, reference: VerseReference) -> Optional[Verse]:
        """
        Fetch verse using free bible-api.com as fallback.
        
        Args:
            reference: VerseReference to fetch
            
        Returns:
            Verse object if successful, None if failed
        """
        try:
            # Get free API translation code
            free_translation = self.TRANSLATION_MAP.get(reference.translation, "niv")
            
            # Format reference properly: "1 Peter 2:24" → "1+Peter+2:24"
            verse_ref = f"{reference.book} {reference.chapter}:{reference.start_verse}"
            if reference.end_verse:
                verse_ref += f"-{reference.end_verse}"
            
            # Replace spaces with + for URL
            verse_ref = verse_ref.replace(" ", "+")
            
            url = f"{self.BASE_URL}/{verse_ref}?translation={free_translation}"
            
            
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('verses'):
                        verse_data = data['verses'][0]
                        verse_text = verse_data.get('text', '').strip()
                        
                        # Clean the text
                        verse_text = self._clean_verse_text(verse_text)
                        
                        if verse_text:
                            logger.info(f"Free fallback success: {reference.canonical_reference}")
                            
                            return Verse(
                                reference=reference,
                                text=verse_text,
                                translation=reference.translation,  # Keep original translation type
                                source_api="bible-api.com (fallback)"
                            )
                    
                    logger.warning(f"Free fallback no data for: {reference.canonical_reference}")
                    return None
                else:
                    logger.warning(f"Free fallback HTTP {response.status} for: {reference.canonical_reference}")
                    return None
                    
        except Exception as e:
            logger.warning(f"Free fallback error for {reference.canonical_reference}: {e}")
            return None
    
    def _clean_verse_text(self, text: str) -> str:
        """Clean verse text from free API response."""
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove leading verse numbers
        text = re.sub(r'^\d+\s*', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

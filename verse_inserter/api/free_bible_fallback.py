"""
Enhanced Bible API fallback with NLT API as default.

This module uses NLT API as the primary source with free API as fallback.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import aiohttp
from typing import Optional
from ..models.verse import Verse, VerseReference, TranslationType
from ..utils.logger import get_logger
from .nlt_api_client import NLTAPIClient
from .fall_back import FreeBibleFallback

logger = get_logger(__name__)


class EnhancedBibleFallback:
    """
    Smart fallback manager that uses NLT API as default.
    
    Selection logic:
    1. Always try NLT API first if available
    2. Fall back to free bible-api.com if NLT fails
    """
    
    def __init__(self, nlt_api_key: Optional[str] = None):
        """
        Initialize enhanced fallback with NLT API key.
        
        Args:
            nlt_api_key: NLT API key. Required for NLT API access.
        """
        self.nlt_api_key = nlt_api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.nlt_client: Optional[NLTAPIClient] = None
        self.free_fallback: Optional[FreeBibleFallback] = None
        
        logger.info(f"EnhancedBibleFallback initialized with NLT API as default")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        
        # Initialize NLT client as primary
        if self.nlt_api_key:
            self.nlt_client = NLTAPIClient(self.nlt_api_key)
            await self.nlt_client.__aenter__()
        
        # Initialize free fallback as backup
        self.free_fallback = FreeBibleFallback()
        await self.free_fallback.__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.nlt_client:
            await self.nlt_client.__aexit__(exc_type, exc_val, exc_tb)
        
        if self.free_fallback:
            await self.free_fallback.__aexit__(exc_type, exc_val, exc_tb)
        
        if self.session:
            await self.session.close()
    
    async def fetch_verse(self, reference: VerseReference) -> Optional[Verse]:
        """
        Fetch verse using NLT API as default with free API fallback.
        
        Args:
            reference: VerseReference to fetch
            
        Returns:
            Verse object if successful, None if all attempts fail
        """
        try:
            # Strategy 1: Always try NLT API first if available
            if self.nlt_client and self.nlt_api_key:
                logger.info(f"Using NLT API (default) for {reference.canonical_reference}")
                verse = await self.nlt_client.fetch_verse(reference)
                
                if verse:
                    return verse
                else:
                    logger.warning(f"NLT API failed, falling back to free API")
            
            # Strategy 2: Use free bible-api.com as fallback
            logger.info(f"Using free API fallback for {reference.canonical_reference}")
            verse = await self.free_fallback.fetch_verse(reference)
            
            if verse:
                return verse
            
            # All strategies failed
            logger.error(f"All fallback attempts failed for {reference.canonical_reference}")
            return None
            
        except Exception as e:
            logger.error(f"Enhanced fallback error for {reference.canonical_reference}: {e}")
            return None
    
    async def get_fallback_stats(self) -> dict:
        """
        Get statistics about fallback usage.
        
        Returns:
            Dictionary with fallback statistics
        """
        stats = {
            "nlt_api_available": bool(self.nlt_api_key),
            "free_api_available": True,
            "primary_api": "NLT API",
            "fallback_api": "Free API"
        }
        
        # Test API availability
        if self.nlt_client:
            try:
                nlt_available = await self.nlt_client.test_connection()
                stats["nlt_api_status"] = "connected" if nlt_available else "failed"
            except Exception:
                stats["nlt_api_status"] = "error"
        
        return stats

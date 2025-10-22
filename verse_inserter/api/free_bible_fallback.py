"""
Enhanced Bible API fallback with intelligent API selection.

This module provides smart fallback logic that chooses the best API
based on translation type and available API keys.

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
    Smart fallback manager that selects the best API for each request.
    
    Selection logic:
    1. If NLT translation and NLT API key available -> Use NLT API
    2. Otherwise -> Use free bible-api.com
    
    This provides optimal results while respecting API limitations.
    """
    
    def __init__(self, nlt_api_key: Optional[str] = None):
        """
        Initialize enhanced fallback with optional NLT API key.
        
        Args:
            nlt_api_key: Optional NLT API key. If provided, will be used for NLT translations.
        """
        self.nlt_api_key = nlt_api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.nlt_client: Optional[NLTAPIClient] = None
        self.free_fallback: Optional[FreeBibleFallback] = None
        
        logger.info(f"EnhancedBibleFallback initialized (NLT API: {bool(nlt_api_key)})")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        
        # Initialize NLT client if key available
        if self.nlt_api_key:
            self.nlt_client = NLTAPIClient(self.nlt_api_key)
            await self.nlt_client.__aenter__()
        
        # Initialize free fallback
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
        Fetch verse using the most appropriate API.
        
        Args:
            reference: VerseReference to fetch
            
        Returns:
            Verse object if successful, None if all attempts fail
        """
        try:
            # Strategy 1: Use NLT API if available and translation is NLT or KJV
            if self._should_use_nlt_api(reference):
                logger.info(f"Using NLT API for {reference.canonical_reference}")
                verse = await self.nlt_client.fetch_verse(reference)
                
                if verse:
                    return verse
                else:
                    logger.warning(f"NLT API failed, falling back to free API")
            
            # Strategy 2: Use free bible-api.com as fallback
            logger.info(f"Using free API for {reference.canonical_reference}")
            verse = await self.free_fallback.fetch_verse(reference)
            
            if verse:
                return verse
            
            # All strategies failed
            logger.error(f"All fallback attempts failed for {reference.canonical_reference}")
            return None
            
        except Exception as e:
            logger.error(f"Enhanced fallback error for {reference.canonical_reference}: {e}")
            return None
    
    def _should_use_nlt_api(self, reference: VerseReference) -> bool:
        """
        Determine if NLT API should be used for this reference.
        
        Args:
            reference: VerseReference to check
            
        Returns:
            True if NLT API should be used, False otherwise
        """
        # Check if NLT client is available
        if not self.nlt_client or not self.nlt_api_key:
            return False
        
        # Check if translation is supported by NLT API
        supported_translations = [TranslationType.NLT, TranslationType.KJV]
        return reference.translation in supported_translations
    
    async def get_fallback_stats(self) -> dict:
        """
        Get statistics about fallback usage.
        
        Returns:
            Dictionary with fallback statistics
        """
        stats = {
            "nlt_api_available": bool(self.nlt_api_key),
            "free_api_available": True,
            "preferred_api": "NLT API" if self.nlt_api_key else "Free API"
        }
        
        # Test API availability
        if self.nlt_client:
            try:
                nlt_available = await self.nlt_client.test_connection()
                stats["nlt_api_status"] = "connected" if nlt_available else "failed"
            except Exception:
                stats["nlt_api_status"] = "error"
        
        return stats

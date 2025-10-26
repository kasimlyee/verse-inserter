"""
NLT Bible API client for fetching verses from api.nlt.to

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import aiohttp
import asyncio
import re
from typing import Optional
from html import unescape
from bs4 import BeautifulSoup
from ..models.verse import Verse, VerseReference, TranslationType
from ..utils.logger import get_logger

logger = get_logger(__name__)


class NLTAPIClient:
    """
    NLT Bible API client for api.nlt.to
    
    Provides access to NLT, NLT-UK, NTV (Spanish), and KJV translations
    through the official NLT API service.
    """
    
    BASE_URL = "https://api.nlt.to/api"
    
    # Map our TranslationType to NLT API version codes
    VERSION_MAP = {
        TranslationType.NLT: "NLT",
        TranslationType.KJV: "KJV",
    }
    
    def __init__(self, api_key: str):
        """
        Initialize NLT API client.
        
        Args:
            api_key: NLT API license key (use 'TEST' for testing with limits)
        """
        self.api_key = api_key or "TEST"
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info(f"NLTAPIClient initialized with key: {self.api_key[:8]}...")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_verse(self, reference: VerseReference) -> Optional[Verse]:
        """
        Fetch verse using NLT API.
        
        Args:
            reference: VerseReference to fetch
            
        Returns:
            Verse object if successful, None if failed
        """
        try:
            # Check if translation is supported
            version = self.VERSION_MAP.get(reference.translation)
            if not version:
                logger.warning(f"Translation {reference.translation} not supported by NLT API")
                return None
            
            # Format reference for NLT API: "John.3.16" or "John.3.16-17"
            ref = self._format_reference(reference)
            
            # Build URL
            url = f"{self.BASE_URL}/passages"
            params = {
                "ref": ref,
                "version": version,
                "key": self.api_key
            }
            
            logger.debug(f"Fetching from NLT API: {ref} ({version})")
            
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Extract verse text from HTML
                    verse_text = self._extract_verse_text(html_content)
                    
                    if verse_text:
                        logger.info(f"NLT API success: {reference.canonical_reference}")
                        
                        return Verse(
                            reference=reference,
                            text=verse_text,
                            translation=reference.translation,
                            source_api="api.nlt.to",
                            copyright_notice=self._get_copyright_notice(version)
                        )
                    else:
                        logger.warning(f"NLT API: No text extracted for {reference.canonical_reference}")
                        return None
                        
                elif response.status == 401:
                    logger.error("NLT API: Invalid API key")
                    return None
                elif response.status == 429:
                    logger.warning("NLT API: Rate limit exceeded")
                    return None
                else:
                    logger.warning(f"NLT API HTTP {response.status} for: {reference.canonical_reference}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.warning(f"NLT API timeout for {reference.canonical_reference}")
            return None
        except Exception as e:
            logger.warning(f"NLT API error for {reference.canonical_reference}: {e}")
            return None
    
    def _format_reference(self, reference: VerseReference) -> str:
        """
        Format reference for NLT API.
        
        Converts "John 3:16" to "John.3:16"
        Converts "John 3:16-17" to "John.3:16-17"
        
        Args:
            reference: VerseReference to format
            
        Returns:
            Formatted reference string
        """
        book = reference.book.replace(" ", "")
        
        if reference.end_verse:
            return f"{book}.{reference.chapter}:{reference.start_verse}-{reference.end_verse}"
        else:
            return f"{book}.{reference.chapter}:{reference.start_verse}"
    
    def _extract_verse_text(self, html_content: str) -> str:
        """
        Extracts and cleans the verse text from the NLT API HTML output.
        """
        # Use BeautifulSoup for accurate parsing
        soup = BeautifulSoup(html_content, "html.parser")
    
        # Find all verse paragraphs
        paragraphs = soup.find_all("p", class_="body-ch-hd")
        verses = []
    
        for p in paragraphs:
            # Remove footnotes and cross references (a-tn, tn)
            for tag in p.find_all(["a", "span"], class_=["a-tn", "tn"]):
                tag.decompose()
    
            # Remove verse numbers and formatting tags (vn, font, em, etc.)
            for tag in p.find_all(["span", "font", "em"], class_=["vn"]):
                tag.decompose()
    
            # Get clean text
            text = p.get_text(separator=" ", strip=True)
            text = unescape(text)
    
            # Clean extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
    
            if text:
                verses.append(text)
    
        # Join multiple verses (if any)
        return " ".join(verses)
    
    def _clean_verse_text(self, text: str) -> str:
        """Clean and normalize verse text."""
        # Unescape HTML entities
        text = unescape(text)
        
        # Remove verse numbers in square brackets [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove leading verse numbers like "16 "
        text = re.sub(r'^\d+\s+', '', text)
        
        # Remove superscript reference markers
        text = re.sub(r'\s*\[\w+\]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove extra whitespace around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        
        return text.strip()
    
    def _get_copyright_notice(self, version: str) -> str:
        """Get copyright notice for the given version."""
        copyright_notices = {
            "NLT": "Scripture quotations are taken from the Holy Bible, New Living Translation, copyright ©1996, 2004, 2015 by Tyndale House Foundation. Used by permission of Tyndale House Publishers, Carol Stream, Illinois 60188. All rights reserved.",
            "NLTUK": "Scripture quotations are taken from the Holy Bible, New Living Translation, copyright ©1996, 2004, 2015 by Tyndale House Foundation. Used by permission of Tyndale House Publishers, Carol Stream, Illinois 60188. All rights reserved.",
            "KJV": "King James Version - Public Domain",
            "NTV": "Nueva Traducción Viviente, © Tyndale House Foundation, 2010. Usado con permiso de Tyndale House Publishers, Inc., 351 Executive Dr., Carol Stream, IL 60188, Estados Unidos de América. Todos los derechos reservados."
        }
        return copyright_notices.get(version, "")
    
    async def test_connection(self) -> bool:
        """
        Test API connection and key validity.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/passages"
            params = {
                "ref": "John.3.16",
                "version": "NLT",
                "key": self.api_key
            }
            
            async with self.session.get(url, params=params, timeout=10) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"NLT API connection test failed: {e}")
            return False

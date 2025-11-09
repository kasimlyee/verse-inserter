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
from urllib.parse import quote
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
        book = reference.book.strip() # I think here i should be keeping 
        
        if reference.end_verse:
            ref = f"{book} {reference.chapter}:{reference.start_verse}-{reference.end_verse}"
        else:
            ref = f"{book} {reference.chapter}:{reference.start_verse}"

        return quote(ref, safe=':-')
    
    def _extract_verse_text(self, html_content: str) -> str:
        """Extract clean Bible text from NLT HTML response (handles all known variants)."""
        soup = BeautifulSoup(html_content, "html.parser")

         # Remove the header/title elements first
        for unwanted in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "title"]):
            unwanted.decompose()
        
        
        # Look for verse_export tag which contains the actual verse text
        verse_exports = soup.find("verse_export")

        if not verse_exports:
            logger.warning("No verse_export tags found in HTML")
            return ""
    
        verses = []
        
        for verse_export in verse_exports:
            
            # Remove footnote links and their content
            for footnote in verse_export.find_all("a", class_="a-tn"):
                footnote.decompose()
            for footnote_text in verse_export.find_all("span", class_="tn"):
                footnote_text.decompose()

             # Remove verse numbers
            #for vn in verse_export.find_all("span", class_="vn"):
               # vn.decompose()
            
            # Get all paragraph tags within verse_export
            paragraphs = verse_export.find_all("p")
        
            verses_parts = []
            for p in paragraphs:
               # Unwrap any remaining tags
                for tag in p.find_all():
                    tag.unwrap()
                
                text = p.get_text(separator=" ", strip=True)
               # text = unescape(re.sub(r"\s+", " ", text))
                if text:
                    verse_parts.append(text)
            
            if verse_parts:
                # Join parts of the same verse with space
                verse_text = " ".join(verse_parts)
                verses.append(verse_text)
                
        if not verses:
            logger.warning("No verse text extracted")
            return ""

        # Join all verses with space
        final_text = " ".join(verses)

        # Clean up whitespace and HTML entities
        final_text = unescape(re.sub(r"\s+", " ", final_text))
                
        return final_text.strip()

    
    def _clean_verse_text(self, text: str) -> str:
        """Clean and normalize verse text."""
        # Unescape HTML entities
        text = unescape(text)
        
        # Remove verse numbers in square brackets [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)

        # Remove square bracket notes like [1], [a]
        text = re.sub(r'\[\w+\]', '', text)

        # Remove inline footnotes or references like "* 4:9 Or a Sabbath rest."
        text = re.sub(r'\*\s*\d+:\d+.*?\.', '', text)
        
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

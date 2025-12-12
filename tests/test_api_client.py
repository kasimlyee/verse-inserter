"""
Unit tests for Bible API client.

Tests API client functionality including verse fetching, error handling,
and fallback mechanisms.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

from verse_inserter.api.bible_api_client import BibleAPIClient
from verse_inserter.api.api_exceptions import (
    APIError,
    APIRateLimitError,
    APIAuthenticationError
)
from verse_inserter.models.verse import VerseReference, TranslationType, Verse


class TestBibleAPIClient:
    """Tests for BibleAPIClient class."""

    def test_initialization(self):
        """Test client initialization."""
        client = BibleAPIClient(api_key="test_key_123")
        assert client.api_key == "test_key_123"
        assert client.session is None

    def test_initialization_empty_key(self):
        """Test error handling for empty API key."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            BibleAPIClient(api_key="")

        with pytest.raises(ValueError, match="API key cannot be empty"):
            BibleAPIClient(api_key="   ")

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager usage."""
        async with BibleAPIClient(api_key="test_key") as client:
            assert client.session is not None
            assert isinstance(client.session, aiohttp.ClientSession)

    @pytest.mark.asyncio
    async def test_fetch_verse_not_initialized(self):
        """Test error when fetching without context manager."""
        client = BibleAPIClient(api_key="test_key")
        ref = VerseReference.parse("John 3:16")

        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client.fetch_verse(ref)

    @pytest.mark.asyncio
    async def test_fetch_verse_success(self, sample_verse_reference):
        """Test successful verse fetching."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": {
                "content": "For God so loved the world..."
            }
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)

        client = BibleAPIClient(api_key="test_key")
        client.session = mock_session

        verse = await client.fetch_verse(sample_verse_reference)

        assert isinstance(verse, Verse)
        assert "For God so loved" in verse.text

    @pytest.mark.asyncio
    async def test_fetch_verse_authentication_error(self, sample_verse_reference):
        """Test handling of authentication errors."""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={
            "message": "Invalid API key"
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)

        client = BibleAPIClient(api_key="invalid_key")
        client.session = mock_session

        with pytest.raises(APIAuthenticationError):
            await client.fetch_verse(sample_verse_reference)

    @pytest.mark.asyncio
    async def test_fetch_verse_rate_limit(self, sample_verse_reference):
        """Test handling of rate limit errors."""
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)

        client = BibleAPIClient(api_key="test_key")
        client.session = mock_session

        with pytest.raises(APIRateLimitError):
            await client.fetch_verse(sample_verse_reference)

    @pytest.mark.asyncio
    async def test_fetch_verse_not_found(self, sample_verse_reference):
        """Test handling of verse not found errors."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.json = AsyncMock(return_value={
            "message": "Verse not found"
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)

        client = BibleAPIClient(api_key="test_key")
        client.session = mock_session

        with pytest.raises(APIError, match="Verse not found"):
            await client.fetch_verse(sample_verse_reference)

    def test_format_verse_id_simple(self):
        """Test verse ID formatting for simple references."""
        client = BibleAPIClient(api_key="test_key")
        ref = VerseReference(book="John", chapter=3, start_verse=16)

        verse_id = client._format_verse_id(ref)
        assert "JHN.3.16" in verse_id

    def test_format_verse_id_range(self):
        """Test verse ID formatting for verse ranges."""
        client = BibleAPIClient(api_key="test_key")
        ref = VerseReference(book="John", chapter=3, start_verse=16, end_verse=18)

        verse_id = client._format_verse_id(ref)
        assert "JHN.3.16" in verse_id
        assert "JHN.3.18" in verse_id

    def test_get_book_abbreviation(self):
        """Test book name to abbreviation conversion."""
        client = BibleAPIClient(api_key="test_key")

        assert client._get_book_abbreviation("John") == "JHN"
        assert client._get_book_abbreviation("Genesis") == "GEN"
        assert client._get_book_abbreviation("1 Corinthians") == "1CO"
        assert client._get_book_abbreviation("Psalm") == "PSA"
        assert client._get_book_abbreviation("Revelation") == "REV"

    def test_clean_verse_text(self):
        """Test HTML cleaning from verse text."""
        client = BibleAPIClient(api_key="test_key")

        html_text = "<p>For God so loved</p>  <span>the world</span>"
        clean_text = client._clean_verse_text(html_text)

        assert "<p>" not in clean_text
        assert "</p>" not in clean_text
        assert "<span>" not in clean_text
        assert "For God so loved the world" in clean_text

    def test_clean_verse_text_whitespace(self):
        """Test whitespace normalization."""
        client = BibleAPIClient(api_key="test_key")

        text = "For    God   so    loved\n\n  the   world"
        clean_text = client._clean_verse_text(text)

        assert "  " not in clean_text  # No double spaces
        assert clean_text == "For God so loved the world"

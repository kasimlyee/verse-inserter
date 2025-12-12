"""
Unit tests for batch processor.

Tests batch processing functionality including multi-document processing,
verse reuse, and error handling.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from verse_inserter.core.batch_processor import (
    BatchProcessor,
    BatchFileResult,
    BatchProcessingResult,
)
from verse_inserter.models.verse import VerseReference, Verse, TranslationType


class TestBatchFileResult:
    """Tests for BatchFileResult dataclass."""

    def test_success_result(self):
        """Test successful file result."""
        result = BatchFileResult(
            file_path=Path("test.docx"),
            success=True,
            placeholders_found=5,
            verses_inserted=5,
            output_path=Path("test_verses.docx"),
        )

        assert result.success
        assert result.placeholders_found == 5
        assert result.verses_inserted == 5
        assert result.error_message is None

    def test_failed_result(self):
        """Test failed file result."""
        result = BatchFileResult(
            file_path=Path("test.docx"),
            success=False,
            error_message="File not found",
        )

        assert not result.success
        assert result.error_message == "File not found"
        assert result.output_path is None


class TestBatchProcessingResult:
    """Tests for BatchProcessingResult dataclass."""

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = BatchProcessingResult(
            total_files=10,
            successful=8,
            failed=2,
        )

        assert result.success_rate == 80.0

    def test_success_rate_zero_files(self):
        """Test success rate with no files."""
        result = BatchProcessingResult(
            total_files=0,
            successful=0,
            failed=0,
        )

        assert result.success_rate == 0.0

    def test_success_rate_all_failed(self):
        """Test success rate with all failures."""
        result = BatchProcessingResult(
            total_files=5,
            successful=0,
            failed=5,
        )

        assert result.success_rate == 0.0


class TestBatchProcessor:
    """Tests for BatchProcessor class."""

    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client."""
        client = AsyncMock()
        client.fetch_verse = AsyncMock()
        return client

    @pytest.fixture
    def mock_cache_manager(self):
        """Create mock cache manager."""
        cache = MagicMock()
        cache.get = MagicMock(return_value=None)
        cache.set = MagicMock()
        return cache

    @pytest.fixture
    def batch_processor(self, mock_api_client, mock_cache_manager):
        """Create batch processor instance."""
        return BatchProcessor(
            api_client=mock_api_client,
            cache_manager=mock_cache_manager,
        )

    def test_initialization(self, mock_api_client, mock_cache_manager):
        """Test batch processor initialization."""
        processor = BatchProcessor(
            api_client=mock_api_client,
            cache_manager=mock_cache_manager,
        )

        assert processor.api_client == mock_api_client
        assert processor.cache_manager == mock_cache_manager
        assert processor.progress_callback is None

    def test_initialization_with_callback(self, mock_api_client):
        """Test initialization with progress callback."""
        callback = MagicMock()
        processor = BatchProcessor(
            api_client=mock_api_client,
            progress_callback=callback,
        )

        assert processor.progress_callback == callback

    def test_report_progress_with_callback(self, batch_processor):
        """Test progress reporting with callback."""
        callback = MagicMock()
        batch_processor.progress_callback = callback

        batch_processor._report_progress("Test message", 5, 10)

        callback.assert_called_once_with("Test message", 5, 10)

    def test_report_progress_without_callback(self, batch_processor):
        """Test progress reporting without callback doesn't error."""
        # Should not raise exception
        batch_processor._report_progress("Test message", 5, 10)

    @pytest.mark.asyncio
    async def test_collect_all_placeholders_success(self, batch_processor, tmp_path):
        """Test collecting placeholders from documents."""
        # Create mock document
        mock_doc = MagicMock()
        mock_placeholders = {
            VerseReference.parse("John 3:16"): ["placeholder1"],
            VerseReference.parse("Psalm 23:1"): ["placeholder2"],
        }

        with patch.object(
            batch_processor.document_processor,
            'load_document'
        ) as mock_load:
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_doc)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_load.return_value = mock_context

            with patch.object(
                batch_processor.document_processor,
                'find_all_placeholders',
                return_value=mock_placeholders,
            ):
                file_path = tmp_path / "test.docx"
                file_path.touch()

                result = await batch_processor._collect_all_placeholders([file_path])

                assert file_path in result
                assert len(result[file_path]) == 2

    @pytest.mark.asyncio
    async def test_collect_all_placeholders_error(self, batch_processor, tmp_path):
        """Test placeholder collection with error."""
        with patch.object(
            batch_processor.document_processor,
            'load_document',
            side_effect=Exception("File error"),
        ):
            file_path = tmp_path / "bad.docx"

            result = await batch_processor._collect_all_placeholders([file_path])

            # Should return empty dict for failed files
            assert result[file_path] == {}

    @pytest.mark.asyncio
    async def test_fetch_all_verses_from_api(self, batch_processor):
        """Test fetching verses from API."""
        ref1 = VerseReference.parse("John 3:16")
        ref2 = VerseReference.parse("Psalm 23:1")

        verse1 = Verse(
            reference=ref1,
            text="For God so loved...",
            translation=TranslationType.NIV,
        )
        verse2 = Verse(
            reference=ref2,
            text="The Lord is my shepherd...",
            translation=TranslationType.NIV,
        )

        batch_processor.api_client.fetch_verse.side_effect = [verse1, verse2]

        result = await batch_processor._fetch_all_verses([ref1, ref2])

        assert len(result) == 2
        assert result[ref1] == verse1
        assert result[ref2] == verse2
        assert batch_processor.api_client.fetch_verse.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_all_verses_from_cache(self, batch_processor):
        """Test fetching verses from cache."""
        ref = VerseReference.parse("John 3:16")
        cached_verse = Verse(
            reference=ref,
            text="Cached verse",
            translation=TranslationType.NIV,
        )

        batch_processor.cache_manager.get.return_value = cached_verse

        result = await batch_processor._fetch_all_verses([ref])

        assert len(result) == 1
        assert result[ref] == cached_verse
        # Should not call API if cached
        batch_processor.api_client.fetch_verse.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_all_verses_caches_results(self, batch_processor):
        """Test that fetched verses are cached."""
        ref = VerseReference.parse("John 3:16")
        verse = Verse(
            reference=ref,
            text="For God so loved...",
            translation=TranslationType.NIV,
        )

        batch_processor.api_client.fetch_verse.return_value = verse
        batch_processor.cache_manager.get.return_value = None

        await batch_processor._fetch_all_verses([ref])

        batch_processor.cache_manager.set.assert_called_once_with(ref, verse)

    @pytest.mark.asyncio
    async def test_fetch_all_verses_handles_errors(self, batch_processor):
        """Test verse fetching handles errors gracefully."""
        ref1 = VerseReference.parse("John 3:16")
        ref2 = VerseReference.parse("Invalid 99:99")

        verse1 = Verse(
            reference=ref1,
            text="For God so loved...",
            translation=TranslationType.NIV,
        )

        batch_processor.api_client.fetch_verse.side_effect = [
            verse1,
            Exception("API error"),
        ]

        result = await batch_processor._fetch_all_verses([ref1, ref2])

        # Should only have successful verse
        assert len(result) == 1
        assert ref1 in result
        assert ref2 not in result

    @pytest.mark.asyncio
    async def test_process_single_file_success(self, batch_processor, tmp_path):
        """Test processing single file successfully."""
        file_path = tmp_path / "test.docx"
        output_path = tmp_path / "test_verses.docx"

        ref = VerseReference.parse("John 3:16")
        verse = Verse(
            reference=ref,
            text="For God so loved...",
            translation=TranslationType.NIV,
        )

        placeholders = {ref: ["placeholder"]}
        verses = {ref: verse}

        mock_doc = MagicMock()

        with patch.object(
            batch_processor.document_processor,
            'load_document'
        ) as mock_load:
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_doc)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_load.return_value = mock_context

            with patch.object(
                batch_processor.document_processor,
                'replace_placeholders',
                return_value=1,
            ), patch.object(
                batch_processor.document_processor,
                'save_document',
            ):
                result = await batch_processor._process_single_file(
                    file_path=file_path,
                    placeholders=placeholders,
                    verses=verses,
                    output_dir=None,
                    output_suffix="_verses",
                )

                assert result.success
                assert result.placeholders_found == 1
                assert result.verses_inserted == 1
                assert result.error_message is None

    @pytest.mark.asyncio
    async def test_process_single_file_with_output_dir(self, batch_processor, tmp_path):
        """Test processing with custom output directory."""
        file_path = tmp_path / "test.docx"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        placeholders = {}
        verses = {}

        mock_doc = MagicMock()

        with patch.object(
            batch_processor.document_processor,
            'load_document'
        ) as mock_load:
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_doc)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_load.return_value = mock_context

            with patch.object(
                batch_processor.document_processor,
                'replace_placeholders',
                return_value=0,
            ), patch.object(
                batch_processor.document_processor,
                'save_document',
            ):
                result = await batch_processor._process_single_file(
                    file_path=file_path,
                    placeholders=placeholders,
                    verses=verses,
                    output_dir=output_dir,
                    output_suffix="_verses",
                )

                assert result.success
                assert result.output_path.parent == output_dir

    @pytest.mark.asyncio
    async def test_process_single_file_error(self, batch_processor, tmp_path):
        """Test single file processing handles errors."""
        file_path = tmp_path / "test.docx"

        with patch.object(
            batch_processor.document_processor,
            'load_document',
            side_effect=Exception("File error"),
        ):
            result = await batch_processor._process_single_file(
                file_path=file_path,
                placeholders={},
                verses={},
                output_dir=None,
                output_suffix="_verses",
            )

            assert not result.success
            assert "File error" in result.error_message

    @pytest.mark.asyncio
    async def test_process_batch_complete_workflow(self, batch_processor, tmp_path):
        """Test complete batch processing workflow."""
        # Create test files
        file1 = tmp_path / "doc1.docx"
        file2 = tmp_path / "doc2.docx"
        file1.touch()
        file2.touch()

        # Mock the entire workflow
        ref = VerseReference.parse("John 3:16")
        verse = Verse(
            reference=ref,
            text="For God so loved...",
            translation=TranslationType.NIV,
        )

        placeholders = {ref: ["placeholder"]}
        mock_doc = MagicMock()

        with patch.object(
            batch_processor,
            '_collect_all_placeholders',
            return_value={file1: placeholders, file2: placeholders},
        ), patch.object(
            batch_processor,
            '_fetch_all_verses',
            return_value={ref: verse},
        ), patch.object(
            batch_processor.document_processor,
            'load_document'
        ) as mock_load:
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_doc)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_load.return_value = mock_context

            with patch.object(
                batch_processor.document_processor,
                'replace_placeholders',
                return_value=1,
            ), patch.object(
                batch_processor.document_processor,
                'save_document',
            ):
                result = await batch_processor.process_batch(
                    file_paths=[file1, file2],
                    output_dir=None,
                )

                assert result.total_files == 2
                assert result.successful == 2
                assert result.failed == 0
                assert result.total_placeholders == 2
                assert result.total_verses_inserted == 2
                assert result.success_rate == 100.0

    @pytest.mark.asyncio
    async def test_process_batch_with_failures(self, batch_processor, tmp_path):
        """Test batch processing with some failures."""
        file1 = tmp_path / "doc1.docx"
        file2 = tmp_path / "doc2.docx"
        file1.touch()
        file2.touch()

        ref = VerseReference.parse("John 3:16")
        verse = Verse(
            reference=ref,
            text="For God so loved...",
            translation=TranslationType.NIV,
        )

        placeholders = {ref: ["placeholder"]}

        with patch.object(
            batch_processor,
            '_collect_all_placeholders',
            return_value={file1: placeholders, file2: placeholders},
        ), patch.object(
            batch_processor,
            '_fetch_all_verses',
            return_value={ref: verse},
        ), patch.object(
            batch_processor,
            '_process_single_file',
            side_effect=[
                BatchFileResult(
                    file_path=file1,
                    success=True,
                    placeholders_found=1,
                    verses_inserted=1,
                    output_path=tmp_path / "doc1_verses.docx",
                ),
                BatchFileResult(
                    file_path=file2,
                    success=False,
                    error_message="Processing error",
                ),
            ],
        ):
            result = await batch_processor.process_batch(
                file_paths=[file1, file2],
            )

            assert result.total_files == 2
            assert result.successful == 1
            assert result.failed == 1
            assert result.success_rate == 50.0

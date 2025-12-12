"""
Batch processing engine for multiple documents.

Handles processing multiple Word documents simultaneously with optimized
verse fetching and error handling per document.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field

from verse_inserter.core.document_processor import DocumentProcessor
from verse_inserter.api.bible_api_client import BibleAPIClient
from verse_inserter.core.cache_manager import CacheManager
from verse_inserter.models.verse import VerseReference, Verse


@dataclass
class BatchFileResult:
    """Result of processing a single file in batch."""

    file_path: Path
    success: bool
    placeholders_found: int = 0
    verses_inserted: int = 0
    error_message: Optional[str] = None
    output_path: Optional[Path] = None


@dataclass
class BatchProcessingResult:
    """Overall result of batch processing operation."""

    total_files: int
    successful: int
    failed: int
    total_placeholders: int = 0
    total_verses_inserted: int = 0
    file_results: List[BatchFileResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.successful / self.total_files) * 100


class BatchProcessor:
    """
    Process multiple Word documents in batch.

    Features:
    - Process multiple documents efficiently
    - Collect all unique verses first to minimize API calls
    - Per-document error handling
    - Progress callbacks for UI updates
    - Reuse verse data across documents
    """

    def __init__(
        self,
        api_client: BibleAPIClient,
        cache_manager: Optional[CacheManager] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ):
        """
        Initialize batch processor.

        Args:
            api_client: Bible API client for fetching verses
            cache_manager: Optional cache manager for verse caching
            progress_callback: Optional callback for progress updates (message, current, total)
        """
        self.api_client = api_client
        self.cache_manager = cache_manager
        self.progress_callback = progress_callback
        self.document_processor = DocumentProcessor()

    def _report_progress(self, message: str, current: int, total: int) -> None:
        """Report progress via callback if available."""
        if self.progress_callback:
            self.progress_callback(message, current, total)

    async def process_batch(
        self,
        file_paths: List[Path],
        output_dir: Optional[Path] = None,
        output_suffix: str = "_verses",
    ) -> BatchProcessingResult:
        """
        Process multiple documents in batch.

        Args:
            file_paths: List of input document paths
            output_dir: Optional output directory (defaults to same dir as input)
            output_suffix: Suffix to add to output filenames

        Returns:
            BatchProcessingResult with processing statistics
        """
        total_files = len(file_paths)
        result = BatchProcessingResult(
            total_files=total_files,
            successful=0,
            failed=0,
        )

        self._report_progress("Scanning documents...", 0, total_files)

        # Step 1: Collect all placeholders from all documents
        file_placeholders = await self._collect_all_placeholders(file_paths)

        # Step 2: Collect unique verse references
        all_references = set()
        for placeholders in file_placeholders.values():
            all_references.update(placeholders.keys())

        total_unique_verses = len(all_references)
        self._report_progress(
            f"Fetching {total_unique_verses} unique verses...",
            0,
            total_unique_verses,
        )

        # Step 3: Fetch all unique verses once
        verses = await self._fetch_all_verses(list(all_references))

        # Step 4: Process each document with pre-fetched verses
        for idx, file_path in enumerate(file_paths, 1):
            self._report_progress(
                f"Processing {file_path.name}...",
                idx,
                total_files,
            )

            file_result = await self._process_single_file(
                file_path,
                file_placeholders.get(file_path, {}),
                verses,
                output_dir,
                output_suffix,
            )

            result.file_results.append(file_result)

            if file_result.success:
                result.successful += 1
                result.total_placeholders += file_result.placeholders_found
                result.total_verses_inserted += file_result.verses_inserted
            else:
                result.failed += 1

        self._report_progress("Batch processing complete!", total_files, total_files)

        return result

    async def _collect_all_placeholders(
        self,
        file_paths: List[Path],
    ) -> Dict[Path, Dict[VerseReference, List]]:
        """
        Collect all placeholders from all documents.

        Returns:
            Dictionary mapping file paths to their placeholders
        """
        file_placeholders = {}

        for file_path in file_paths:
            try:
                with self.document_processor.load_document(file_path) as doc:
                    placeholders = self.document_processor.find_all_placeholders(doc)
                    file_placeholders[file_path] = placeholders
            except Exception:
                # Skip files that can't be read
                file_placeholders[file_path] = {}

        return file_placeholders

    async def _fetch_all_verses(
        self,
        references: List[VerseReference],
    ) -> Dict[VerseReference, Verse]:
        """
        Fetch all unique verses efficiently.

        Args:
            references: List of verse references to fetch

        Returns:
            Dictionary mapping references to verses
        """
        verses = {}
        total = len(references)

        for idx, ref in enumerate(references, 1):
            try:
                # Check cache first
                if self.cache_manager:
                    cached = self.cache_manager.get(ref)
                    if cached:
                        verses[ref] = cached
                        continue

                # Fetch from API
                verse = await self.api_client.fetch_verse(ref)
                verses[ref] = verse

                # Cache the result
                if self.cache_manager:
                    self.cache_manager.set(ref, verse)

                # Update progress periodically
                if idx % 10 == 0 or idx == total:
                    self._report_progress(
                        f"Fetching verses... ({idx}/{total})",
                        idx,
                        total,
                    )

            except Exception:
                # Skip verses that fail to fetch
                continue

        return verses

    async def _process_single_file(
        self,
        file_path: Path,
        placeholders: Dict[VerseReference, List],
        verses: Dict[VerseReference, Verse],
        output_dir: Optional[Path],
        output_suffix: str,
    ) -> BatchFileResult:
        """
        Process a single document file.

        Args:
            file_path: Path to input document
            placeholders: Placeholders found in this document
            verses: Pre-fetched verses dictionary
            output_dir: Output directory for processed file
            output_suffix: Suffix to add to output filename

        Returns:
            BatchFileResult with processing details
        """
        try:
            # Determine output path
            if output_dir:
                output_path = output_dir / f"{file_path.stem}{output_suffix}{file_path.suffix}"
            else:
                output_path = file_path.parent / f"{file_path.stem}{output_suffix}{file_path.suffix}"

            # Filter verses that exist for this document's placeholders
            available_verses = {
                ref: verse for ref, verse in verses.items()
                if ref in placeholders
            }

            # Process document
            with self.document_processor.load_document(file_path) as doc:
                replacements = self.document_processor.replace_placeholders(
                    doc,
                    available_verses,
                )

                # Save processed document
                self.document_processor.save_document(doc, output_path)

            return BatchFileResult(
                file_path=file_path,
                success=True,
                placeholders_found=len(placeholders),
                verses_inserted=replacements,
                output_path=output_path,
            )

        except Exception as e:
            return BatchFileResult(
                file_path=file_path,
                success=False,
                error_message=str(e),
            )

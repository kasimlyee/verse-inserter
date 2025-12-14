"""
Translation download manager for offline Bible database.

Handles downloading complete Bible translations from the API
and storing them in the local offline database.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

import asyncio
from typing import Optional, Callable, List
from dataclasses import dataclass

from verse_inserter.api.bible_api_client import BibleAPIClient
from verse_inserter.core.offline_database import OfflineBibleDatabase
from verse_inserter.models.verse import TranslationType, VerseReference, Verse
from verse_inserter.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DownloadProgress:
    """Download progress information."""

    translation: TranslationType
    current_book: str
    current_chapter: int
    total_books: int
    current_book_index: int
    verses_downloaded: int
    status: str  # "downloading", "completed", "failed", "cancelled"
    error_message: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        if self.total_books == 0:
            return 0.0
        return (self.current_book_index / self.total_books) * 100


class TranslationDownloader:
    """
    Download complete Bible translations for offline use.

    Features:
    - Download entire Bible translations
    - Progress tracking with callbacks
    - Batch verse insertion for efficiency
    - Cancellation support
    - Error recovery
    """

    # Bible book order (Protestant canon)
    BIBLE_BOOKS = [
        # Old Testament
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
        "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
        "Ezra", "Nehemiah", "Esther", "Job",
        "Psalm", "Proverbs", "Ecclesiastes", "Song of Solomon",
        "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
        "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
        "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
        "Zechariah", "Malachi",
        # New Testament
        "Matthew", "Mark", "Luke", "John", "Acts",
        "Romans", "1 Corinthians", "2 Corinthians", "Galatians",
        "Ephesians", "Philippians", "Colossians",
        "1 Thessalonians", "2 Thessalonians",
        "1 Timothy", "2 Timothy", "Titus", "Philemon",
        "Hebrews", "James", "1 Peter", "2 Peter",
        "1 John", "2 John", "3 John", "Jude", "Revelation",
    ]

    # Approximate chapter counts for progress estimation
    CHAPTER_COUNTS = {
        "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36,
        "Deuteronomy": 34, "Joshua": 24, "Judges": 21, "Ruth": 4,
        "1 Samuel": 31, "2 Samuel": 24, "1 Kings": 22, "2 Kings": 25,
        "1 Chronicles": 29, "2 Chronicles": 36, "Ezra": 10, "Nehemiah": 13,
        "Esther": 10, "Job": 42, "Psalm": 150, "Proverbs": 31,
        "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66,
        "Jeremiah": 52, "Lamentations": 5, "Ezekiel": 48, "Daniel": 12,
        "Hosea": 14, "Joel": 3, "Amos": 9, "Obadiah": 1, "Jonah": 4,
        "Micah": 7, "Nahum": 3, "Habakkuk": 3, "Zephaniah": 3,
        "Haggai": 2, "Zechariah": 14, "Malachi": 4,
        "Matthew": 28, "Mark": 16, "Luke": 24, "John": 21, "Acts": 28,
        "Romans": 16, "1 Corinthians": 16, "2 Corinthians": 13,
        "Galatians": 6, "Ephesians": 6, "Philippians": 4, "Colossians": 4,
        "1 Thessalonians": 5, "2 Thessalonians": 3, "1 Timothy": 6,
        "2 Timothy": 4, "Titus": 3, "Philemon": 1, "Hebrews": 13,
        "James": 5, "1 Peter": 5, "2 Peter": 3, "1 John": 5,
        "2 John": 1, "3 John": 1, "Jude": 1, "Revelation": 22,
    }

    def __init__(
        self,
        api_client: BibleAPIClient,
        database: OfflineBibleDatabase,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ):
        """
        Initialize translation downloader.

        Args:
            api_client: Bible API client for fetching verses
            database: Offline database for storage
            progress_callback: Optional callback for progress updates
        """
        self.api_client = api_client
        self.database = database
        self.progress_callback = progress_callback
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel ongoing download."""
        self._cancelled = True
        logger.info("Download cancellation requested")

    def _report_progress(self, progress: DownloadProgress) -> None:
        """Report progress via callback if available."""
        if self.progress_callback:
            self.progress_callback(progress)

    async def download_translation(
        self,
        translation: TranslationType,
        books: Optional[List[str]] = None,
    ) -> bool:
        """
        Download a complete Bible translation.

        Args:
            translation: Translation to download
            books: Optional list of specific books (defaults to all)

        Returns:
            True if download completed successfully
        """
        self._cancelled = False
        books_to_download = books or self.BIBLE_BOOKS
        total_books = len(books_to_download)
        verses_downloaded = 0

        try:
            # Add translation to database
            translation_name = self._get_translation_name(translation)
            self.database.add_translation(
                translation=translation,
                name=translation_name,
                language="English",
            )

            logger.info(
                f"Starting download of {translation.value} "
                f"({total_books} books)"
            )

            # Download each book
            for book_index, book_name in enumerate(books_to_download):
                if self._cancelled:
                    self._report_progress(DownloadProgress(
                        translation=translation,
                        current_book=book_name,
                        current_chapter=0,
                        total_books=total_books,
                        current_book_index=book_index,
                        verses_downloaded=verses_downloaded,
                        status="cancelled",
                    ))
                    return False

                chapter_count = self.CHAPTER_COUNTS.get(book_name, 50)

                # Download book chapters
                book_verses = []
                for chapter in range(1, chapter_count + 1):
                    if self._cancelled:
                        return False

                    # Report progress
                    self._report_progress(DownloadProgress(
                        translation=translation,
                        current_book=book_name,
                        current_chapter=chapter,
                        total_books=total_books,
                        current_book_index=book_index,
                        verses_downloaded=verses_downloaded,
                        status="downloading",
                    ))

                    # Download chapter verses
                    chapter_verses = await self._download_chapter(
                        translation=translation,
                        book=book_name,
                        chapter=chapter,
                    )

                    if chapter_verses:
                        book_verses.extend(chapter_verses)
                        verses_downloaded += len(chapter_verses)
                    else:
                        # No more chapters in this book
                        break

                # Store book verses in bulk
                if book_verses:
                    self.database.add_verses_bulk(translation, book_verses)
                    logger.info(
                        f"Stored {len(book_verses)} verses from {book_name}"
                    )

            # Download completed
            self._report_progress(DownloadProgress(
                translation=translation,
                current_book="",
                current_chapter=0,
                total_books=total_books,
                current_book_index=total_books,
                verses_downloaded=verses_downloaded,
                status="completed",
            ))

            logger.info(
                f"Download completed: {translation.value} "
                f"({verses_downloaded} verses)"
            )

            return True

        except Exception as e:
            logger.error(f"Download failed: {e}")
            self._report_progress(DownloadProgress(
                translation=translation,
                current_book="",
                current_chapter=0,
                total_books=total_books,
                current_book_index=0,
                verses_downloaded=verses_downloaded,
                status="failed",
                error_message=str(e),
            ))
            return False

    async def _download_chapter(
        self,
        translation: TranslationType,
        book: str,
        chapter: int,
    ) -> List[Verse]:
        """
        Download all verses from a chapter.

        Args:
            translation: Translation to download
            book: Book name
            chapter: Chapter number

        Returns:
            List of verses in the chapter
        """
        verses = []

        # Try downloading verses 1-200 (most chapters have < 200 verses)
        for verse_num in range(1, 201):
            if self._cancelled:
                break

            try:
                reference = VerseReference(
                    book=book,
                    chapter=chapter,
                    start_verse=verse_num,
                    translation=translation,
                )

                verse = await self.api_client.fetch_verse(reference)

                if verse:
                    verses.append(verse)
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.05)
                else:
                    # No more verses in this chapter
                    break

            except Exception as e:
                # Verse doesn't exist or API error
                logger.debug(
                    f"Stopped at {book} {chapter}:{verse_num} - {e}"
                )
                break

        return verses

    def _get_translation_name(self, translation: TranslationType) -> str:
        """Get full name for translation."""
        names = {
            TranslationType.KJV: "King James Version",
            TranslationType.NIV: "New International Version",
            TranslationType.ESV: "English Standard Version",
            TranslationType.NKJV: "New King James Version",
            TranslationType.NLT: "New Living Translation",
        }
        return names.get(translation, translation.value)

    async def download_specific_books(
        self,
        translation: TranslationType,
        books: List[str],
    ) -> bool:
        """
        Download specific books only.

        Args:
            translation: Translation to download
            books: List of book names to download

        Returns:
            True if successful
        """
        return await self.download_translation(translation, books)

    async def update_translation(
        self,
        translation: TranslationType,
    ) -> bool:
        """
        Update an existing translation (re-download).

        Args:
            translation: Translation to update

        Returns:
            True if successful
        """
        # Delete existing translation
        self.database.delete_translation(translation)

        # Re-download
        return await self.download_translation(translation)
